"""Registro de auditoría: quién cambió qué, cuándo y desde dónde.

Se escribe siempre y no se edita nunca. Es lo que permite responder «¿de dónde
salió esta cantidad?» seis meses después, delante de una supervisión.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Historial, Usuario

# Campos que nunca se copian al historial.
OCULTOS = {"hash_clave", "hash_token"}


def instantanea(obj: Any, campos: list[str] | None = None) -> dict:
    """Copia serializable de una fila de la base de datos."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        datos = dict(obj)
    else:
        columnas = [c.name for c in obj.__table__.columns]
        datos = {c: getattr(obj, c) for c in columnas}
    salida = {}
    for k, v in datos.items():
        if k in OCULTOS:
            continue
        if campos and k not in campos:
            continue
        salida[k] = v if isinstance(v, (str, int, float, bool, list, dict, type(None))) else str(v)
    return salida


def diferencias(antes: dict, despues: dict) -> dict:
    """Solo lo que cambió: el historial no debe ser una fotocopia."""
    cambios = {}
    for k in set(antes) | set(despues):
        a, d = antes.get(k), despues.get(k)
        if k in ("actualizado_en", "creado_en"):
            continue
        if a != d:
            cambios[k] = {"antes": a, "despues": d}
    return cambios


def registrar(db: Session, *, accion: str, entidad: str, entidad_id: str | None = None,
              proyecto_id: str | None = None, resumen: str | None = None,
              antes: dict | None = None, despues: dict | None = None,
              usuario: Usuario | None = None, ip: str | None = None,
              commit: bool = False) -> Historial:
    h = Historial(
        proyecto_id=proyecto_id,
        entidad=entidad,
        entidad_id=entidad_id,
        accion=accion,
        resumen=(resumen or "")[:400] or None,
        antes=antes or None,
        despues=despues or None,
        usuario_id=usuario.id if usuario else None,
        usuario_nombre=usuario.nombre if usuario else None,
        ip=ip,
    )
    db.add(h)
    if commit:
        db.commit()
    return h


def registrar_cambio(db: Session, *, entidad: str, entidad_id: str, proyecto_id: str | None,
                     antes: dict, despues: dict, resumen: str,
                     usuario: Usuario | None = None) -> Historial | None:
    """Registra solo si hubo cambios reales."""
    cambios = diferencias(antes, despues)
    if not cambios:
        return None
    return registrar(db, accion="editar", entidad=entidad, entidad_id=entidad_id,
                     proyecto_id=proyecto_id, resumen=resumen,
                     antes={k: v["antes"] for k, v in cambios.items()},
                     despues={k: v["despues"] for k, v in cambios.items()},
                     usuario=usuario)


def historial_de(db: Session, proyecto_id: str, *, entidad: str | None = None,
                 entidad_id: str | None = None, limite: int = 200) -> list[Historial]:
    q = select(Historial).where(Historial.proyecto_id == proyecto_id)
    if entidad:
        q = q.where(Historial.entidad == entidad)
    if entidad_id:
        q = q.where(Historial.entidad_id == entidad_id)
    return list(db.scalars(q.order_by(Historial.fecha.desc()).limit(limite)))
