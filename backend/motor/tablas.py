"""Tablas técnicas cargadas desde JSON, con su procedencia.

Todo dato numérico que no sea una medida del proyecto vive aquí (pesos de
varilla, factores de esponjamiento, diámetros comerciales, configuración por
país) y viaja SIEMPRE con su `fuente` y su `etiqueta` de procedencia. Un número
sin fuente no entra: es la causa raíz de los errores de la app anterior
(«ml = puntos × 4,5», «Fuente: RNE» sobre datos que no están en el RNE).

Los archivos viven en `datos/tablas/*.json` para poder corregirlos sin tocar
código, y se recargan al vuelo en desarrollo.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger("metra.tablas")

RAIZ = Path(__file__).resolve().parent.parent.parent
DIR_TABLAS = Path(os.environ.get("METRA_DIR_TABLAS", RAIZ / "datos" / "tablas"))
DIR_TABLAS.mkdir(parents=True, exist_ok=True)

_cache: dict[str, Any] = {}
_marcas: dict[str, float] = {}


def cargar(nombre: str, por_defecto: Any = None) -> Any:
    """Carga `datos/tablas/<nombre>.json`. Recarga si el archivo cambió."""
    ruta = DIR_TABLAS / f"{nombre}.json"
    if not ruta.exists():
        if nombre not in _cache:
            log.warning("Tabla ausente: %s (se usa el valor por defecto)", ruta.name)
        _cache.setdefault(nombre, por_defecto if por_defecto is not None else [])
        return _cache[nombre]
    marca = ruta.stat().st_mtime
    if _marcas.get(nombre) != marca:
        try:
            _cache[nombre] = json.loads(ruta.read_text(encoding="utf-8"))
            _marcas[nombre] = marca
            log.info("Tabla cargada: %s", ruta.name)
        except json.JSONDecodeError as exc:
            log.error("Tabla ilegible %s: %s", ruta.name, exc)
            _cache.setdefault(nombre, por_defecto if por_defecto is not None else [])
    return _cache[nombre]


def guardar(nombre: str, datos: Any) -> Path:
    ruta = DIR_TABLAS / f"{nombre}.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    _marcas.pop(nombre, None)
    return ruta


def existe(nombre: str) -> bool:
    return (DIR_TABLAS / f"{nombre}.json").exists()


def inventario() -> list[dict]:
    """Qué tablas hay, cuántas filas y cuántas están verificadas."""
    salida = []
    for ruta in sorted(DIR_TABLAS.glob("*.json")):
        nombre = ruta.stem
        datos = cargar(nombre)
        filas = _contar(datos)
        salida.append({
            "nombre": nombre,
            "archivo": ruta.name,
            "filas": filas,
            "verificadas": _contar_verificadas(datos),
            "tamano_kb": round(ruta.stat().st_size / 1024, 1),
        })
    return salida


def _contar(datos: Any) -> int:
    if isinstance(datos, list):
        return len(datos)
    if isinstance(datos, dict):
        return sum(len(v) if isinstance(v, list) else 1 for v in datos.values())
    return 0


def _contar_verificadas(datos: Any) -> int:
    def cuenta(lista):
        return sum(1 for x in lista if isinstance(x, dict) and x.get("verificado") is not False)
    if isinstance(datos, list):
        return cuenta(datos)
    if isinstance(datos, dict):
        return sum(cuenta(v) for v in datos.values() if isinstance(v, list))
    return 0


def buscar(nombre_tabla: str, clave: str, valor: Any, seccion: str | None = None) -> dict | None:
    """Busca la primera fila cuya `clave` valga `valor`."""
    datos = cargar(nombre_tabla)
    if seccion and isinstance(datos, dict):
        datos = datos.get(seccion, [])
    if not isinstance(datos, list):
        return None
    for fila in datos:
        if isinstance(fila, dict) and str(fila.get(clave, "")).strip().lower() == str(valor).strip().lower():
            return fila
    return None
