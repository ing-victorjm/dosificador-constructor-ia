"""METRA AI — aplicación FastAPI.

Frontend estático + API JSON. El motor de cálculo vive en `backend/motor` y no
conoce ni HTTP ni la base de datos: se puede probar solo.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .db import crear_tablas
from .motor.unidades import ErrorUnidad

RAIZ = Path(__file__).resolve().parent.parent
FRONTEND = RAIZ / "frontend"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("metra")

app = FastAPI(
    title="METRA AI",
    description="Metrados de obra trazables, auditables y exportables.",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


@app.on_event("startup")
def arrancar() -> None:
    crear_tablas()
    from .semillas import sembrar
    resumen = sembrar()

    # El proyecto de demostración se crea también aquí, no solo en run.py: en un
    # servidor con disco efímero la base se vacía en cada despliegue, y una app
    # que arranca sin nada que mirar parece rota.
    if not os.environ.get("METRA_SIN_DEMO"):
        try:
            from . import demo
            demo.asegurar()
        except Exception as exc:      # una demo que falla no debe tumbar la app
            log.warning("No se pudo preparar la demostración: %s", exc)

    log.info("METRA AI lista · %s partidas en el catálogo · panel en el puerto %s",
             resumen.get("partidas_catalogo"), os.environ.get("PORT", "8770"))


@app.exception_handler(ErrorUnidad)
def _error_unidad(_r: Request, exc: ErrorUnidad):
    return JSONResponse(status_code=400, content={"detail": str(exc), "tipo": "unidad"})


@app.exception_handler(ValueError)
def _error_valor(_r: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc), "tipo": "validacion"})


# --- Rutas de la API ---------------------------------------------------------
from .api import (  # noqa: E402
    asistente, calidad, catalogo, exportar, historial, planos,
    presupuesto, proyectos, referencia, sesion, metrados,
)

for router in (sesion.router, referencia.router, proyectos.router, metrados.router,
               catalogo.router, planos.router, calidad.router, presupuesto.router,
               exportar.router, historial.router, asistente.router):
    app.include_router(router, prefix="/api")


# --- Frontend ----------------------------------------------------------------
if (FRONTEND / "css").exists():
    app.mount("/css", StaticFiles(directory=FRONTEND / "css"), name="css")
if (FRONTEND / "js").exists():
    app.mount("/js", StaticFiles(directory=FRONTEND / "js"), name="js")
if (FRONTEND / "vendor").exists():
    app.mount("/vendor", StaticFiles(directory=FRONTEND / "vendor"), name="vendor")


@app.get("/", include_in_schema=False)
def inicio():
    return FileResponse(FRONTEND / "index.html")


@app.get("/salud", include_in_schema=False)
def salud():
    return {"estado": "ok", "version": app.version}


@app.get("/{ruta:path}", include_in_schema=False)
def spa(ruta: str):
    """Cualquier ruta que no sea API devuelve la SPA (navegación por hash y por path)."""
    if ruta.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Ruta de API no encontrada."})
    archivo = FRONTEND / ruta
    if archivo.is_file():
        return FileResponse(archivo)
    return FileResponse(FRONTEND / "index.html")
