"""Registro, inicio y cierre de sesión."""
from __future__ import annotations

import os
import re

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import audit, security
from ..db import obtener_sesion
from ..models import Empresa, Usuario

router = APIRouter(tags=["sesión"])


RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def _email(v: str) -> str:
    v = (v or "").strip().lower()
    if not RE_EMAIL.match(v):
        raise ValueError("Escriba un correo válido, por ejemplo nombre@empresa.com")
    return v


class DatosRegistro(BaseModel):
    email: str
    nombre: str = Field(min_length=2, max_length=200)
    clave: str = Field(min_length=8, max_length=200)
    empresa: str | None = Field(default=None, max_length=200)
    profesion: str | None = None

    _valida_email = field_validator("email")(lambda cls, v: _email(v))


class DatosAcceso(BaseModel):
    email: str
    clave: str

    _valida_email = field_validator("email")(lambda cls, v: _email(v))


def _publico(u: Usuario) -> dict:
    return {
        "id": u.id, "email": u.email, "nombre": u.nombre, "rol": u.rol,
        "empresa_id": u.empresa_id, "profesion": u.profesion,
        "preferencias": u.preferencias or {},
        "permisos": sorted(security.PERMISOS.get(u.rol, set())),
    }


@router.post("/sesion/registro", status_code=status.HTTP_201_CREATED)
def registrar(datos: DatosRegistro, request: Request, respuesta: Response,
              db: Session = Depends(obtener_sesion)):
    ok, motivo = security.fuerza_clave(datos.clave)
    if not ok:
        raise HTTPException(400, f"Contraseña débil: {motivo}")

    existe = db.scalar(select(Usuario).where(func.lower(Usuario.email) == datos.email.lower()))
    if existe:
        raise HTTPException(409, "Ya hay una cuenta con ese correo.")

    empresa = None
    if datos.empresa:
        empresa = db.scalar(select(Empresa).where(func.lower(Empresa.nombre) == datos.empresa.lower()))
        if not empresa:
            empresa = Empresa(nombre=datos.empresa)
            db.add(empresa)
            db.flush()

    # Quién administra. En una instalación local, el primero que se registra.
    # En un servidor público eso sería un agujero: cualquiera que llegue primero
    # se quedaría con el control. Por eso, si `METRA_ADMIN_EMAIL` está definido,
    # solo ese correo obtiene el rol de administrador.
    admin_declarado = os.environ.get("METRA_ADMIN_EMAIL", "").strip().lower()
    if admin_declarado:
        es_admin = datos.email.lower() == admin_declarado
    else:
        es_admin = db.scalar(select(func.count(Usuario.id))) == 0

    u = Usuario(
        email=datos.email.lower(), nombre=datos.nombre.strip(),
        hash_clave=security.hash_clave(datos.clave),
        rol="administrador" if es_admin else "metrador",
        empresa_id=empresa.id if empresa else None,
        profesion=datos.profesion,
    )
    db.add(u)
    db.flush()
    audit.registrar(db, accion="crear", entidad="usuario", entidad_id=u.id,
                    resumen=f"Alta de {u.email}", usuario=u)
    db.commit()

    token = security.crear_sesion(db, u, request.headers.get("user-agent"),
                                  request.client.host if request.client else None)
    respuesta.set_cookie(security.COOKIE, token, httponly=True, samesite="lax",
                         max_age=int(security.DURACION_SESION.total_seconds()))
    return {"usuario": _publico(u), "token": token}


@router.post("/sesion/acceso")
def acceder(datos: DatosAcceso, request: Request, respuesta: Response,
            db: Session = Depends(obtener_sesion)):
    u = db.scalar(select(Usuario).where(func.lower(Usuario.email) == datos.email.lower()))
    # Mismo mensaje para usuario inexistente y clave errada: no se filtra qué correos existen.
    if not u or not security.verificar_clave(datos.clave, u.hash_clave):
        raise HTTPException(401, "Correo o contraseña incorrectos.")
    if not u.activo:
        raise HTTPException(403, "Su cuenta está desactivada. Contacte al administrador.")

    token = security.crear_sesion(db, u, request.headers.get("user-agent"),
                                  request.client.host if request.client else None)
    respuesta.set_cookie(security.COOKIE, token, httponly=True, samesite="lax",
                         max_age=int(security.DURACION_SESION.total_seconds()))
    return {"usuario": _publico(u), "token": token}


@router.post("/sesion/salida")
def salir(request: Request, respuesta: Response, db: Session = Depends(obtener_sesion)):
    token = request.cookies.get(security.COOKIE)
    if token:
        security.cerrar_sesion(db, token)
    respuesta.delete_cookie(security.COOKIE)
    return {"ok": True}


@router.get("/sesion/yo")
def yo(usuario: Usuario = Depends(security.usuario_actual)):
    return {"usuario": _publico(usuario), "modo_local": security.MODO_LOCAL}


class Preferencias(BaseModel):
    tema: str | None = None
    densidad: str | None = None
    idioma: str | None = None


@router.put("/sesion/preferencias")
def guardar_preferencias(prefs: Preferencias, db: Session = Depends(obtener_sesion),
                         usuario: Usuario = Depends(security.usuario_actual)):
    actuales = dict(usuario.preferencias or {})
    actuales.update({k: v for k, v in prefs.model_dump().items() if v is not None})
    usuario.preferencias = actuales
    db.commit()
    return {"preferencias": actuales}


@router.get("/usuarios")
def listar_usuarios(db: Session = Depends(obtener_sesion),
                    usuario: Usuario = Depends(security.usuario_actual)):
    security.exigir(db, usuario, None, "ver")
    q = select(Usuario)
    if usuario.rol != "administrador":
        q = q.where(Usuario.empresa_id == usuario.empresa_id)
    return {"usuarios": [_publico(u) | {"activo": u.activo,
                                        "ultimo_acceso": u.ultimo_acceso.isoformat() if u.ultimo_acceso else None}
                         for u in db.scalars(q.order_by(Usuario.nombre))],
            "roles": security.DESCRIPCION_ROLES}


class CambioRol(BaseModel):
    rol: str
    activo: bool | None = None


@router.put("/usuarios/{usuario_id}")
def actualizar_usuario(usuario_id: str, cambio: CambioRol,
                       db: Session = Depends(obtener_sesion),
                       usuario: Usuario = Depends(security.usuario_actual)):
    security.exigir(db, usuario, None, "administrar")
    if cambio.rol not in security.PERMISOS:
        raise HTTPException(400, f"Rol desconocido: {cambio.rol}")
    objetivo = db.get(Usuario, usuario_id)
    if not objetivo:
        raise HTTPException(404, "Usuario no encontrado.")
    if objetivo.id == usuario.id and cambio.rol != "administrador":
        raise HTTPException(400, "No puede quitarse a sí mismo el rol de administrador.")
    antes = audit.instantanea(objetivo)
    objetivo.rol = cambio.rol
    if cambio.activo is not None:
        objetivo.activo = cambio.activo
    audit.registrar_cambio(db, entidad="usuario", entidad_id=objetivo.id, proyecto_id=None,
                           antes=antes, despues=audit.instantanea(objetivo),
                           resumen=f"Cambio de rol de {objetivo.email}", usuario=usuario)
    db.commit()
    return {"usuario": _publico(objetivo)}
