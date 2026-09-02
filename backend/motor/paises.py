"""Configuración por país: norma, moneda, unidades, impuesto y reglas por defecto.

La app NO asume una normativa única. Al crear un proyecto se elige país y de ahí
salen: la norma de medición aplicable, el símbolo y formato de moneda, el sistema
de unidades y los valores por defecto de las reglas que varían entre países
(descuento de vanos, si el encofrado se mide aparte, si el acero lleva
desperdicio).

Los datos vienen de `datos/tablas/paises.json`. Aquí solo queda el mínimo para
que la app arranque sin esa tabla, marcado como no verificado.
"""
from __future__ import annotations

from . import tablas

MINIMO = [
    {
        "pais": "Perú", "codigo_iso": "PE",
        "normas": [{
            "nombre": "Norma Técnica de Metrados para Obras de Edificación y Habilitaciones Urbanas",
            "entidad": "Ministerio de Vivienda, Construcción y Saneamiento",
            "anio": 2010, "referencia": "R.D. N° 073-2010-VIVIENDA/VMCS-DNC", "url": None,
        }],
        "moneda": {"iso": "PEN", "simbolo": "S/", "decimales": 2, "sep_decimal": ".", "sep_miles": ","},
        "sistema_unidades": "metrico",
        "impuesto": {"nombre": "IGV", "tasa": "18"},
        "reglas_por_defecto": {
            "regimen": "OE",
            "familias_descuento": "norma_pe",
            "encofrado_separado": True,
            "acero_incluye_desperdicio": False,
            "desperdicio_acero_pct": "5",
            "esponjamiento_en_metrado": True,
        },
        "verificado": True,
    },
]


def todos() -> list[dict]:
    datos = tablas.cargar("paises", MINIMO)
    return datos if isinstance(datos, list) and datos else MINIMO


def por_codigo(iso: str) -> dict:
    iso = (iso or "PE").upper()
    for p in todos():
        if str(p.get("codigo_iso", "")).upper() == iso:
            return p
    return MINIMO[0]


def moneda(iso_pais: str) -> dict:
    return por_codigo(iso_pais).get("moneda", MINIMO[0]["moneda"])


def reglas_iniciales(iso_pais: str) -> dict:
    """Reglas por defecto de un proyecto nuevo en ese país."""
    p = por_codigo(iso_pais)
    base = {
        "redondeo": {"decimales_metrado": 2, "decimales_precio": 2,
                     "decimales_parcial": 2, "modo": "medio_arriba"},
        "impuesto": p.get("impuesto", {"nombre": "IGV", "tasa": "18"}),
        "gastos_generales_pct": "10",
        "utilidad_pct": "5",
        "norma": (p.get("normas") or [{}])[0].get("nombre"),
        "exigir_lamina": True,
        "bloquear_dimension_incompatible": True,
        "desperdicio_en_metrado": False,
    }
    base.update(p.get("reglas_por_defecto", {}))
    return base


MONEDAS_COMUNES = [
    {"iso": "PEN", "simbolo": "S/", "nombre": "Sol peruano"},
    {"iso": "USD", "simbolo": "$", "nombre": "Dólar estadounidense"},
    {"iso": "EUR", "simbolo": "€", "nombre": "Euro"},
    {"iso": "COP", "simbolo": "$", "nombre": "Peso colombiano"},
    {"iso": "CLP", "simbolo": "$", "nombre": "Peso chileno"},
    {"iso": "MXN", "simbolo": "$", "nombre": "Peso mexicano"},
    {"iso": "ARS", "simbolo": "$", "nombre": "Peso argentino"},
    {"iso": "BOB", "simbolo": "Bs", "nombre": "Boliviano"},
    {"iso": "BRL", "simbolo": "R$", "nombre": "Real brasileño"},
]
