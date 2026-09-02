"""Historial de cambios y copias de seguridad."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .. import audit, security, servicios
from ..db import obtener_sesion
from ..models import Usuario
from .proyectos import obtener, _publico

router = APIRouter(tags=["historial"])

ETIQUETA_ACCION = {
    "crear": "creó", "editar": "modificó", "eliminar": "eliminó",
    "aprobar": "aprobó", "revisar": "revisó", "importar": "importó",
    "desbloquear": "desbloqueó",
}

ETIQUETA_ENTIDAD = {
    "proyecto": "el proyecto", "item": "una partida", "medicion": "una fila de metrado",
    "ubicacion": "una ubicación", "elemento": "un elemento", "archivo": "un archivo",
    "plano": "un plano", "version": "una versión", "observacion": "una observación",
    "usuario": "un usuario", "partida_catalogo": "una partida del catálogo",
    "alerta": "una alerta de calidad", "marcado": "una medición sobre plano",
}


@router.get("/proyectos/{proyecto_id}/historial")
def historial(proyecto_id: str, entidad: str | None = None, entidad_id: str | None = None,
              limite: int = Query(default=200, ge=1, le=1000),
              db: Session = Depends(obtener_sesion),
              usuario: Usuario = Depends(security.usuario_actual)):
    obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "ver")
    filas = audit.historial_de(db, proyecto_id, entidad=entidad,
                               entidad_id=entidad_id, limite=limite)
    return {"historial": [{
        "id": h.id, "accion": h.accion, "entidad": h.entidad, "entidad_id": h.entidad_id,
        "resumen": h.resumen, "antes": h.antes, "despues": h.despues,
        "usuario": h.usuario_nombre or "—",
        "fecha": h.fecha.isoformat() if h.fecha else None,
        "frase": f"{h.usuario_nombre or 'Alguien'} {ETIQUETA_ACCION.get(h.accion, h.accion)} "
                 f"{ETIQUETA_ENTIDAD.get(h.entidad, h.entidad)}",
    } for h in filas]}


@router.get("/proyectos/{proyecto_id}/respaldo")
def respaldo(proyecto_id: str, db: Session = Depends(obtener_sesion),
             usuario: Usuario = Depends(security.usuario_actual)):
    """Copia de seguridad completa del proyecto en JSON, descargable."""
    p = obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "exportar")
    datos = {
        "formato": "metra-ai/respaldo",
        "version_formato": 1,
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "generado_por": usuario.nombre,
        "proyecto": _publico(p),
        "ubicaciones": servicios.arbol_ubicaciones(db, proyecto_id),
        "metrados": servicios.arbol(db, p, con_filas=True),
        "historial": [{"accion": h.accion, "entidad": h.entidad, "resumen": h.resumen,
                       "usuario": h.usuario_nombre,
                       "fecha": h.fecha.isoformat() if h.fecha else None}
                      for h in audit.historial_de(db, proyecto_id, limite=1000)],
    }
    db.commit()
    nombre = f"respaldo-{p.codigo or p.id}-{datetime.now().strftime('%Y%m%d-%H%M')}.json"
    return JSONResponse(
        content=json.loads(json.dumps(datos, default=str)),
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )
