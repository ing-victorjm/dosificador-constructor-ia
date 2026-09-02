"""Autenticación, sesiones y control de acceso por rol.

Sin dependencias externas: PBKDF2-HMAC-SHA256 de la biblioteca estándar. Menos
piezas que instalar en Windows y menos superficie que auditar.

Decisión de producto: **no se obliga a iniciar sesión para poder metrar**. Hay
un modo local con un usuario propietario del equipo. Obligar a registrarse antes
de dejar calcular es el antipatrón que hace que nadie use la herramienta.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import obtener_sesion
from .models import MiembroProyecto, Sesion, Usuario

ITERACIONES = 240_000
DURACION_SESION = timedelta(days=14)
COOKIE = "metra_sesion"

MODO_LOCAL = os.environ.get("METRA_MODO", "local") == "local"
EMAIL_LOCAL = os.environ.get("METRA_USUARIO_LOCAL", "local@metra.ai")


# --------------------------------------------------------------------------- #
# Contraseñas
# --------------------------------------------------------------------------- #

def hash_clave(clave: str) -> str:
    if not clave or len(clave) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    sal = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal, ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${sal.hex()}${dk.hex()}"


def verificar_clave(clave: str, guardado: str) -> bool:
    try:
        algoritmo, iteraciones, sal_hex, esperado = guardado.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", (clave or "").encode("utf-8"),
                                 bytes.fromhex(sal_hex), int(iteraciones))
        return hmac.compare_digest(dk.hex(), esperado)
    except (ValueError, AttributeError):
        return False


def fuerza_clave(clave: str) -> tuple[bool, str]:
    if not clave or len(clave) < 8:
        return False, "Mínimo 8 caracteres."
    if clave.isdigit() or clave.isalpha():
        return False, "Combine letras y números."
    if clave.lower() in {"12345678", "password", "contrasena", "constructor", "metra123"}:
        return False, "Esa contraseña es demasiado común."
    return True, "Correcta."


# --------------------------------------------------------------------------- #
# Sesiones
# --------------------------------------------------------------------------- #

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def crear_sesion(db: Session, usuario: Usuario, agente: str | None = None,
                 ip: str | None = None) -> str:
    token = secrets.token_urlsafe(32)
    db.add(Sesion(
        usuario_id=usuario.id,
        hash_token=_hash_token(token),
        expira_en=datetime.now(timezone.utc) + DURACION_SESION,
        agente=(agente or "")[:300] or None,
        ip=ip,
    ))
    usuario.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()
    return token


def cerrar_sesion(db: Session, token: str) -> None:
    s = db.scalar(select(Sesion).where(Sesion.hash_token == _hash_token(token)))
    if s:
        db.delete(s)
        db.commit()


def usuario_de_token(db: Session, token: str) -> Usuario | None:
    s = db.scalar(select(Sesion).where(Sesion.hash_token == _hash_token(token)))
    if not s:
        return None
    expira = s.expira_en if s.expira_en.tzinfo else s.expira_en.replace(tzinfo=timezone.utc)
    if expira < datetime.now(timezone.utc):
        db.delete(s)
        db.commit()
        return None
    u = db.get(Usuario, s.usuario_id)
    return u if (u and u.activo) else None


def asegurar_usuario_local(db: Session) -> Usuario:
    """Usuario del equipo, para trabajar sin registro previo."""
    u = db.scalar(select(Usuario).where(Usuario.email == EMAIL_LOCAL))
    if not u:
        u = Usuario(
            email=EMAIL_LOCAL, nombre="Usuario local", rol="administrador",
            hash_clave=hash_clave(secrets.token_urlsafe(24)),
            preferencias={"tema": "claro"},
        )
        db.add(u)
        db.commit()
    return u


# --------------------------------------------------------------------------- #
# Dependencias de FastAPI
# --------------------------------------------------------------------------- #

def _token_de(request: Request) -> str | None:
    cabecera = request.headers.get("authorization", "")
    if cabecera.lower().startswith("bearer "):
        return cabecera[7:].strip()
    return request.cookies.get(COOKIE)


def usuario_actual(request: Request, db: Session = Depends(obtener_sesion)) -> Usuario:
    token = _token_de(request)
    if token:
        u = usuario_de_token(db, token)
        if u:
            return u
    if MODO_LOCAL:
        return asegurar_usuario_local(db)
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inicie sesión para continuar.")


def usuario_opcional(request: Request, db: Session = Depends(obtener_sesion)) -> Usuario | None:
    token = _token_de(request)
    if token:
        return usuario_de_token(db, token)
    return asegurar_usuario_local(db) if MODO_LOCAL else None


# --------------------------------------------------------------------------- #
# Roles y permisos
# --------------------------------------------------------------------------- #

# Qué puede hacer cada rol. El cliente solo mira; el supervisor aprueba.
PERMISOS = {
    "administrador": {"ver", "crear", "editar", "eliminar", "revisar", "aprobar",
                      "exportar", "administrar", "desbloquear"},
    "metrador":      {"ver", "crear", "editar", "exportar"},
    "revisor":       {"ver", "editar", "revisar", "exportar"},
    "supervisor":    {"ver", "revisar", "aprobar", "exportar", "desbloquear"},
    "cliente":       {"ver", "exportar"},
}

DESCRIPCION_ROLES = {
    "administrador": "Control total: usuarios, proyectos, aprobación y desbloqueo.",
    "metrador": "Crea y edita metrados. No aprueba ni desbloquea partidas.",
    "revisor": "Revisa, observa y corrige. No aprueba.",
    "supervisor": "Aprueba, observa y desbloquea. No edita metrados.",
    "cliente": "Solo consulta y descarga reportes.",
}


def rol_en_proyecto(db: Session, usuario: Usuario, proyecto_id: str) -> str:
    if usuario.rol == "administrador":
        return "administrador"
    m = db.scalar(select(MiembroProyecto).where(
        MiembroProyecto.proyecto_id == proyecto_id,
        MiembroProyecto.usuario_id == usuario.id,
    ))
    return m.rol if m else usuario.rol


def puede(rol: str, accion: str) -> bool:
    return accion in PERMISOS.get(rol, set())


def exigir(db: Session, usuario: Usuario, proyecto_id: str | None, accion: str) -> str:
    rol = rol_en_proyecto(db, usuario, proyecto_id) if proyecto_id else usuario.rol
    if not puede(rol, accion):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Su rol ({rol}) no permite {accion}. {DESCRIPCION_ROLES.get(rol, '')}",
        )
    return rol
