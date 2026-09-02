"""Registro de unidades: dimensión, conversión y compatibilidad.

La app no asume sistema métrico. Cada proyecto declara `metrico` o `imperial`;
el motor calcula SIEMPRE en unidades base (m, m2, m3, kg, und) y convierte solo
al presentar o al exportar. Así una partida importada en pies cuadrados suma sin
corromper el metrado.
"""
from __future__ import annotations

from decimal import Decimal
from typing import NamedTuple

from .redondeo import dec

# Dimensiones físicas. Dos unidades solo se suman si comparten dimensión.
LONGITUD = "longitud"
AREA = "area"
VOLUMEN = "volumen"
MASA = "masa"
CONTEO = "conteo"
GLOBAL = "global"
TIEMPO = "tiempo"
ADIMENSIONAL = "adimensional"


class Unidad(NamedTuple):
    codigo: str
    nombre: str
    dimension: str
    factor: Decimal      # cuánto vale 1 unidad expresada en la unidad base de su dimensión
    sistema: str         # "metrico" | "imperial" | "ambos"
    base: str            # unidad base de la dimensión


def _u(codigo, nombre, dimension, factor, sistema, base):
    return Unidad(codigo, nombre, dimension, dec(factor), sistema, base)


UNIDADES: dict[str, Unidad] = {u.codigo: u for u in [
    # --- Longitud (base: m) ---
    _u("m",    "metro",               LONGITUD, "1",              "metrico",  "m"),
    _u("ml",   "metro lineal",        LONGITUD, "1",              "metrico",  "m"),
    _u("km",   "kilómetro",           LONGITUD, "1000",           "metrico",  "m"),
    _u("cm",   "centímetro",          LONGITUD, "0.01",           "metrico",  "m"),
    _u("mm",   "milímetro",           LONGITUD, "0.001",          "metrico",  "m"),
    _u("ft",   "pie",                 LONGITUD, "0.3048",         "imperial", "m"),
    _u("lf",   "pie lineal",          LONGITUD, "0.3048",         "imperial", "m"),
    _u("in",   "pulgada",             LONGITUD, "0.0254",         "imperial", "m"),
    _u("yd",   "yarda",               LONGITUD, "0.9144",         "imperial", "m"),
    # --- Área (base: m2) ---
    _u("m2",   "metro cuadrado",      AREA,     "1",              "metrico",  "m2"),
    _u("cm2",  "centímetro cuadrado", AREA,     "0.0001",         "metrico",  "m2"),
    _u("ha",   "hectárea",            AREA,     "10000",          "metrico",  "m2"),
    _u("sf",   "pie cuadrado",        AREA,     "0.09290304",     "imperial", "m2"),
    _u("sy",   "yarda cuadrada",      AREA,     "0.83612736",     "imperial", "m2"),
    _u("p2",   "pie tablar",          AREA,     "1",              "ambos",    "p2"),
    # --- Volumen (base: m3) ---
    _u("m3",   "metro cúbico",        VOLUMEN,  "1",              "metrico",  "m3"),
    _u("l",    "litro",               VOLUMEN,  "0.001",          "metrico",  "m3"),
    _u("cy",   "yarda cúbica",        VOLUMEN,  "0.764554857984", "imperial", "m3"),
    _u("cf",   "pie cúbico",          VOLUMEN,  "0.028316846592", "imperial", "m3"),
    _u("gal",  "galón US",            VOLUMEN,  "0.003785411784", "imperial", "m3"),
    # --- Masa (base: kg) ---
    _u("kg",   "kilogramo",           MASA,     "1",              "metrico",  "kg"),
    _u("t",    "tonelada métrica",    MASA,     "1000",           "metrico",  "kg"),
    _u("g",    "gramo",               MASA,     "0.001",          "metrico",  "kg"),
    _u("lb",   "libra",               MASA,     "0.45359237",     "imperial", "kg"),
    _u("ton",  "tonelada corta",      MASA,     "907.18474",      "imperial", "kg"),
    # --- Conteo (base: und) ---
    _u("und",  "unidad",              CONTEO,   "1",              "ambos",    "und"),
    _u("pza",  "pieza",               CONTEO,   "1",              "ambos",    "und"),
    _u("ea",   "each",                CONTEO,   "1",              "imperial", "und"),
    _u("jgo",  "juego",               CONTEO,   "1",              "ambos",    "und"),
    _u("par",  "par",                 CONTEO,   "2",              "ambos",    "und"),
    _u("mll",  "millar",              CONTEO,   "1000",           "ambos",    "und"),
    _u("cto",  "ciento",              CONTEO,   "100",            "ambos",    "und"),
    _u("bls",  "bolsa",               CONTEO,   "1",              "ambos",    "und"),
    _u("pto",  "punto",               CONTEO,   "1",              "ambos",    "und"),
    _u("sal",  "salida",              CONTEO,   "1",              "ambos",    "und"),
    # --- Global / tiempo ---
    _u("glb",  "global",              GLOBAL,   "1",              "ambos",    "glb"),
    _u("ls",   "lump sum",            GLOBAL,   "1",              "imperial", "glb"),
    _u("est",  "estimado",            GLOBAL,   "1",              "ambos",    "glb"),
    _u("mes",  "mes",                 TIEMPO,   "30",             "ambos",    "dia"),
    _u("dia",  "día",                 TIEMPO,   "1",              "ambos",    "dia"),
    _u("h",    "hora",                TIEMPO,   "0.0416666667",   "ambos",    "dia"),
    _u("hh",   "hora-hombre",         TIEMPO,   "0.125",          "ambos",    "dia"),
    _u("hm",   "hora-máquina",        TIEMPO,   "0.125",          "ambos",    "dia"),
    _u("pct",  "porcentaje",          ADIMENSIONAL, "1",          "ambos",    "pct"),
]}

# Equivalencias imperial <-> métrico para el mismo concepto de partida.
EQUIVALENTE_SISTEMA = {
    "m": "lf", "ml": "lf", "m2": "sf", "m3": "cy", "kg": "lb", "und": "ea", "glb": "ls",
    "lf": "m", "sf": "m2", "cy": "m3", "lb": "kg", "ea": "und", "ls": "glb",
    "ft": "m", "in": "cm",
}

# Tolerancia a variantes de escritura habituales en planillas importadas.
ALIAS = {
    "m2.": "m2", "m3.": "m3", "mt": "m", "mts": "m", "u": "und", "un": "und",
    "unid": "und", "kg.": "kg", "gbl": "glb", "global": "glb", "p.2": "p2",
    "pie2": "sf", "sqft": "sf", "cuyd": "cy", "pulg": "in", "%": "pct",
    "m²": "m2", "m³": "m3", "punto": "pto", "salida": "sal",
}


class ErrorUnidad(ValueError):
    pass


def unidad(codigo: str) -> Unidad:
    if not codigo:
        raise ErrorUnidad("Falta la unidad de medida.")
    clave = str(codigo).strip().lower()
    if clave in UNIDADES:
        return UNIDADES[clave]
    if clave in ALIAS:
        return UNIDADES[ALIAS[clave]]
    raise ErrorUnidad(
        "Unidad desconocida: " + repr(codigo) + ". Regístrela en el catálogo de unidades."
    )


def existe(codigo: str) -> bool:
    try:
        unidad(codigo)
        return True
    except ErrorUnidad:
        return False


def dimension(codigo: str) -> str:
    return unidad(codigo).dimension


def compatibles(a: str, b: str) -> bool:
    """¿Se pueden sumar cantidades de estas dos unidades?"""
    try:
        return unidad(a).dimension == unidad(b).dimension
    except ErrorUnidad:
        return False


def convertir(cantidad, desde: str, hacia: str) -> Decimal:
    """Convierte respetando la dimensión. Lanza ErrorUnidad si son incompatibles."""
    ua, ub = unidad(desde), unidad(hacia)
    if ua.dimension != ub.dimension:
        raise ErrorUnidad(
            f"No se puede convertir {ua.codigo} ({ua.dimension}) a {ub.codigo} ({ub.dimension}): "
            "son magnitudes distintas."
        )
    if ua.codigo == ub.codigo:
        return dec(cantidad)
    return dec(cantidad) * ua.factor / ub.factor


def a_base(cantidad, desde: str) -> Decimal:
    u = unidad(desde)
    return dec(cantidad) * u.factor


def unidades_de(dim: str, sistema: str | None = None) -> list[Unidad]:
    return [u for u in UNIDADES.values()
            if u.dimension == dim and (sistema is None or u.sistema in (sistema, "ambos"))]


def sugerir_por_sistema(codigo: str, sistema: str) -> str:
    """Devuelve la unidad equivalente del sistema pedido (m2 -> sf en imperial)."""
    u = unidad(codigo)
    if u.sistema in (sistema, "ambos"):
        return u.codigo
    return EQUIVALENTE_SISTEMA.get(u.codigo, u.codigo)


def catalogo() -> list[dict]:
    return [
        {"codigo": u.codigo, "nombre": u.nombre, "dimension": u.dimension,
         "sistema": u.sistema, "base": u.base, "factor": str(u.factor)}
        for u in UNIDADES.values()
    ]
