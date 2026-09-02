"""Control de calidad y observaciones."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import audit, security, servicios
from ..db import obtener_sesion
from ..models import AlertaDescartada, Elemento, Observacion, Plano, Usuario
from ..motor import validaciones
from .proyectos import obtener

router = APIRouter(tags=["calidad"])


@router.get("/proyectos/{proyecto_id}/calidad")
def revisar(proyecto_id: str, version_id: str | None = None,
            comparar_con: str | None = None,
            db: Session = Depends(obtener_sesion),
            usuario: Usuario = Depends(security.usuario_actual)):
    p = obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "ver")

    datos = servicios.arbol(db, p, version_id=version_id or p.version_actual_id, con_filas=True)
    db.commit()
    partidas = [n for n in servicios.aplanar(datos["items"]) if n["tipo"] == "partida"]

    planos = [{"id": pl.id, "codigo": pl.codigo, "titulo": pl.titulo, "pagina": pl.pagina,
               "metros_por_px": pl.metros_por_px}
              for pl in db.scalars(select(Plano).where(Plano.proyecto_id == proyecto_id))]
    elementos = [{"id": e.id, "tipo": e.tipo, "marca": e.marca, "nombre": e.nombre}
                 for e in db.scalars(select(Elemento).where(Elemento.proyecto_id == proyecto_id))]

    contexto = {"partidas": partidas, "planos": planos, "elementos": elementos,
                "reglas": p.reglas or {}}

    if comparar_con:
        from .proyectos import comparar_versiones
        contexto["comparacion"] = comparar_versiones(
            proyecto_id, a=comparar_con, b=version_id or p.version_actual_id,
            db=db, usuario=usuario)["comparacion"]

    alertas = validaciones.evaluar(contexto)
    descartadas = {a.clave for a in db.scalars(
        select(AlertaDescartada).where(AlertaDescartada.proyecto_id == proyecto_id))}

    activas = [a for a in alertas if a.clave not in descartadas]
    return {
        "alertas": [a.a_dict() for a in activas],
        "descartadas": len(alertas) - len(activas),
        "resumen": validaciones.resumen(activas),
        "revisadas": {"partidas": len(partidas), "planos": len(planos),
                      "elementos": len(elementos)},
    }


class Descarte(BaseModel):
    clave: str
    motivo: str | None = None


@router.post("/proyectos/{proyecto_id}/calidad/descartar")
def descartar(proyecto_id: str, datos: Descarte, db: Session = Depends(obtener_sesion),
              usuario: Usuario = Depends(security.usuario_actual)):
    """Ignora una alerta dejando constancia de quién la ignoró y por qué."""
    security.exigir(db, usuario, proyecto_id, "revisar")
    if not datos.motivo or len(datos.motivo.strip()) < 5:
        raise HTTPException(
            400, "Escriba el motivo por el que se descarta la alerta. Queda en el historial.")
    ya = db.scalar(select(AlertaDescartada).where(
        AlertaDescartada.proyecto_id == proyecto_id, AlertaDescartada.clave == datos.clave))
    if ya:
        ya.motivo = datos.motivo
    else:
        db.add(AlertaDescartada(proyecto_id=proyecto_id, clave=datos.clave,
                                motivo=datos.motivo, usuario_id=usuario.id))
    audit.registrar(db, accion="editar", entidad="alerta", entidad_id=datos.clave,
                    proyecto_id=proyecto_id,
                    resumen=f"Alerta descartada: {datos.clave} — {datos.motivo[:120]}",
                    usuario=usuario)
    db.commit()
    return {"ok": True}


@router.delete("/proyectos/{proyecto_id}/calidad/descartar/{clave}")
def reactivar(proyecto_id: str, clave: str, db: Session = Depends(obtener_sesion),
              usuario: Usuario = Depends(security.usuario_actual)):
    security.exigir(db, usuario, proyecto_id, "revisar")
    fila = db.scalar(select(AlertaDescartada).where(
        AlertaDescartada.proyecto_id == proyecto_id, AlertaDescartada.clave == clave))
    if fila:
        db.delete(fila)
        db.commit()
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Observaciones
# --------------------------------------------------------------------------- #

class DatosObservacion(BaseModel):
    texto: str
    gravedad: str = "media"
    tipo: str = "comentario"
    item_id: str | None = None
    medicion_id: str | None = None
    plano_id: str | None = None
    punto: dict | None = None


@router.get("/proyectos/{proyecto_id}/observaciones")
def listar_observaciones(proyecto_id: str, estado: str | None = None,
                         db: Session = Depends(obtener_sesion),
                         usuario: Usuario = Depends(security.usuario_actual)):
    security.exigir(db, usuario, proyecto_id, "ver")
    q = select(Observacion).where(Observacion.proyecto_id == proyecto_id)
    if estado:
        q = q.where(Observacion.estado == estado)
    filas = list(db.scalars(q.order_by(Observacion.creado_en.desc())))
    autores = {u.id: u.nombre for u in db.scalars(select(Usuario))}
    return {"observaciones": [{
        "id": o.id, "texto": o.texto, "gravedad": o.gravedad, "tipo": o.tipo,
        "estado": o.estado, "item_id": o.item_id, "medicion_id": o.medicion_id,
        "plano_id": o.plano_id, "punto": o.punto,
        "autor": autores.get(o.autor, "—"),
        "creado_en": o.creado_en.isoformat() if o.creado_en else None,
    } for o in filas]}


@router.post("/proyectos/{proyecto_id}/observaciones", status_code=201)
def crear_observacion(proyecto_id: str, datos: DatosObservacion,
                      db: Session = Depends(obtener_sesion),
                      usuario: Usuario = Depends(security.usuario_actual)):
    obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "ver")
    o = Observacion(proyecto_id=proyecto_id, autor=usuario.id, **datos.model_dump())
    db.add(o)
    audit.registrar(db, accion="crear", entidad="observacion", entidad_id=o.id,
                    proyecto_id=proyecto_id, resumen=f"Observación: {o.texto[:120]}",
                    usuario=usuario)
    db.commit()
    return {"observacion_id": o.id}


class CierreObservacion(BaseModel):
    estado: str
    comentario: str | None = None


@router.put("/observaciones/{observacion_id}")
def cerrar_observacion(observacion_id: str, datos: CierreObservacion,
                       db: Session = Depends(obtener_sesion),
                       usuario: Usuario = Depends(security.usuario_actual)):
    o = db.get(Observacion, observacion_id)
    if not o:
        raise HTTPException(404, "Observación no encontrada.")
    security.exigir(db, usuario, o.proyecto_id, "revisar")
    if datos.estado not in ("abierta", "resuelta", "descartada"):
        raise HTTPException(400, "Estado no válido.")
    o.estado = datos.estado
    o.resuelta_por = usuario.id
    if datos.comentario:
        o.texto = f"{o.texto}\n\n— {usuario.nombre}: {datos.comentario}"
    audit.registrar(db, accion="editar", entidad="observacion", entidad_id=o.id,
                    proyecto_id=o.proyecto_id, resumen=f"Observación {datos.estado}",
                    usuario=usuario)
    db.commit()
    return {"ok": True}
