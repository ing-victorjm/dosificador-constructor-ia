"""Conexión a base de datos y sesión.

SQLite por defecto (un archivo, cero instalación, funciona en Windows sin
servicio). El mismo código corre sobre PostgreSQL cambiando `METRA_DB_URL`,
porque no se usa ningún dialecto propietario.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

RAIZ = Path(__file__).resolve().parent.parent
DIR_DATOS = Path(os.environ.get("METRA_DIR_DATOS", RAIZ / "datos"))
DIR_ARCHIVOS = DIR_DATOS / "archivos"
DIR_DATOS.mkdir(parents=True, exist_ok=True)
DIR_ARCHIVOS.mkdir(parents=True, exist_ok=True)

URL = os.environ.get("METRA_DB_URL") or f"sqlite:///{(DIR_DATOS / 'metra.db').as_posix()}"

_es_sqlite = URL.startswith("sqlite")

engine = create_engine(
    URL,
    echo=bool(os.environ.get("METRA_SQL_ECHO")),
    future=True,
    connect_args={"check_same_thread": False, "timeout": 30} if _es_sqlite else {},
    pool_pre_ping=not _es_sqlite,
)

if _es_sqlite:
    @event.listens_for(engine, "connect")
    def _configurar_sqlite(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")     # sin esto SQLite ignora las FK
        cur.execute("PRAGMA journal_mode=WAL")    # lecturas concurrentes durante escrituras
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()

Sesion = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


class Base(DeclarativeBase):
    pass


def obtener_sesion():
    """Dependencia de FastAPI."""
    s = Sesion()
    try:
        yield s
    finally:
        s.close()


@contextmanager
def sesion():
    """Uso fuera de FastAPI (semillas, scripts, pruebas)."""
    s = Sesion()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def crear_tablas() -> None:
    from . import models  # noqa: F401  (registra los modelos en el metadata)
    Base.metadata.create_all(engine)
