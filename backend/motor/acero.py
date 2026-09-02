"""Cuadro de acero: despiece, resumen por diámetro y peso total.

El acero NO se estima con un ratio kg/m³. Se despieza barra por barra: diámetro,
longitud, ganchos, doblados y traslapes. `normas.REGLA_KG_M3` explica por qué, y
la app impide que una estimación por ratio entre al presupuesto.

Los pesos unitarios y las longitudes de gancho se leen de
`datos/tablas/estructuras.json`, que viaja con su fuente. Si esa tabla no está,
se usa el respaldo mínimo de abajo, marcado como no verificado.
"""
from __future__ import annotations

from decimal import Decimal

from . import normas, tablas
from .redondeo import dec, redondear

# Respaldo mínimo: valores nominales ASTM A615 / NTP 341.031 de uso corriente en
# Perú. Se sustituyen en cuanto exista `datos/tablas/estructuras.json`.
RESPALDO_PESOS = [
    {"denominacion": "6 mm", "diametro_mm": "6.00", "peso_kg_m": "0.222", "area_cm2": "0.28"},
    {"denominacion": "8 mm", "diametro_mm": "8.00", "peso_kg_m": "0.395", "area_cm2": "0.50"},
    {"denominacion": '3/8"', "diametro_mm": "9.53", "peso_kg_m": "0.560", "area_cm2": "0.71"},
    {"denominacion": "12 mm", "diametro_mm": "12.00", "peso_kg_m": "0.888", "area_cm2": "1.13"},
    {"denominacion": '1/2"', "diametro_mm": "12.70", "peso_kg_m": "0.994", "area_cm2": "1.29"},
    {"denominacion": '5/8"', "diametro_mm": "15.88", "peso_kg_m": "1.552", "area_cm2": "1.99"},
    {"denominacion": '3/4"', "diametro_mm": "19.05", "peso_kg_m": "2.235", "area_cm2": "2.85"},
    {"denominacion": '1"', "diametro_mm": "25.40", "peso_kg_m": "3.973", "area_cm2": "5.10"},
    {"denominacion": '1 3/8"', "diametro_mm": "35.81", "peso_kg_m": "7.907", "area_cm2": "10.06"},
]


def tabla_pesos() -> list[dict]:
    datos = tablas.cargar("estructuras", {})
    filas = datos.get("acero_pesos") if isinstance(datos, dict) else None
    if filas:
        return filas
    return [{**f, "verificado": False,
             "fuente": "Respaldo interno (valores nominales de uso corriente). "
                       "Pendiente de contrastar con ficha de fabricante."}
            for f in RESPALDO_PESOS]


def _normalizar_diametro(texto: str) -> str:
    t = str(texto or "").strip().replace("Ø", "").replace("φ", "").strip()
    t = t.replace("''", '"').replace("”", '"').replace("’", "'")
    return t


def buscar_diametro(denominacion: str) -> dict | None:
    objetivo = _normalizar_diametro(denominacion).lower()
    for fila in tabla_pesos():
        if _normalizar_diametro(fila.get("denominacion")).lower() == objetivo:
            return fila
        if str(fila.get("diametro_mm", "")).startswith(objetivo.replace("mm", "").strip()):
            return fila
    return None


def peso_unitario(denominacion: str) -> Decimal | None:
    fila = buscar_diametro(denominacion)
    return dec(fila["peso_kg_m"]) if fila else None


def longitud_barra(datos: dict) -> tuple[Decimal | None, str, list[str]]:
    """Longitud desarrollada de UNA barra, con su explicación y sus avisos.

    Suma: longitud recta + ganchos + doblados + traslapes. Cada término se
    declara explícitamente; nada se asume.
    """
    avisos: list[str] = []
    recta = datos.get("longitud")
    if recta in (None, ""):
        return None, "Falta la longitud de la barra.", avisos

    total = dec(recta)
    partes = [f"recta {dec(recta)}"]

    for clave, etiqueta in (("ganchos", "ganchos"), ("doblados", "doblados"),
                            ("traslapes", "traslapes")):
        valor = datos.get(clave)
        if valor in (None, ""):
            continue
        v = dec(valor)
        total += v
        partes.append(f"{etiqueta} {v}")

    if not datos.get("ganchos") and str(datos.get("tipo", "")).lower() in ("estribo", "grapa"):
        avisos.append("Estribo sin longitud de gancho declarada: el gancho sísmico "
                      "de 135° suele ser el 10-15% del peso del estribo.")
    return redondear(total, 4), " + ".join(partes), avisos


def cuadro(barras: list[dict], desperdicio_pct=0) -> dict:
    """Arma el cuadro de acero completo a partir de las barras despiezadas."""
    detalle, avisos_globales = [], []
    por_diametro: dict[str, dict] = {}
    peso_total = Decimal(0)
    longitud_total_global = Decimal(0)

    for i, b in enumerate(barras, start=1):
        denominacion = _normalizar_diametro(b.get("diametro") or b.get("denominacion") or "")
        fila_tabla = buscar_diametro(denominacion)
        unitario = dec(b["peso_unitario"]) if b.get("peso_unitario") else (
            dec(fila_tabla["peso_kg_m"]) if fila_tabla else None)

        longitud_unitaria, explicacion, avisos = longitud_barra(b)
        cantidad = dec(b.get("cantidad") or 0)

        if longitud_unitaria is None or unitario is None or cantidad == 0:
            detalle.append({
                "marca": b.get("marca") or f"B-{i:03d}",
                "elemento": b.get("elemento") or "",
                "diametro": denominacion or "—",
                "cantidad": str(cantidad),
                "longitud_unitaria": None if longitud_unitaria is None else str(longitud_unitaria),
                "longitud_total": None, "peso_unitario": None if unitario is None else str(unitario),
                "peso": None, "explicacion": explicacion,
                "error": ("Falta el peso unitario: registre el diámetro en la tabla de aceros."
                          if unitario is None else
                          "Falta la cantidad de barras." if cantidad == 0 else explicacion),
                "avisos": avisos,
            })
            continue

        longitud_total = redondear(longitud_unitaria * cantidad, 4)
        peso = redondear(longitud_total * unitario, 3)
        peso_total += peso
        longitud_total_global += longitud_total

        acumulado = por_diametro.setdefault(denominacion, {
            "diametro": denominacion, "peso_unitario": str(unitario),
            "cantidad": Decimal(0), "longitud_total": Decimal(0), "peso": Decimal(0),
            "verificado": bool(fila_tabla and fila_tabla.get("verificado", True)),
            "fuente": (fila_tabla or {}).get("fuente"),
        })
        acumulado["cantidad"] += cantidad
        acumulado["longitud_total"] += longitud_total
        acumulado["peso"] += peso

        detalle.append({
            "marca": b.get("marca") or f"B-{i:03d}",
            "elemento": b.get("elemento") or "",
            "diametro": denominacion,
            "cantidad": str(cantidad),
            "longitud_unitaria": str(longitud_unitaria),
            "longitud_total": str(longitud_total),
            "peso_unitario": str(unitario),
            "peso": str(peso),
            "explicacion": explicacion,
            "error": None,
            "avisos": avisos,
        })
        avisos_globales.extend(avisos)

    resumen = sorted(
        [{**v, "cantidad": str(v["cantidad"]),
          "longitud_total": str(redondear(v["longitud_total"], 3)),
          "peso": str(redondear(v["peso"], 3))} for v in por_diametro.values()],
        key=lambda x: dec(x["peso_unitario"]))

    pct = dec(desperdicio_pct or 0)
    return {
        "barras": detalle,
        "resumen_por_diametro": resumen,
        "peso_total": str(redondear(peso_total, 2)),
        "longitud_total": str(redondear(longitud_total_global, 2)),
        "unidad": "kg",
        "desperdicio_pct": str(pct),
        "cantidad_a_comprar": str(redondear(peso_total * (1 + pct / 100), 2)) if pct else None,
        "nota_desperdicio": normas.REGLA_DESPERDICIO["explicacion"] if pct else None,
        "avisos": sorted(set(avisos_globales)),
        "barras_incompletas": sum(1 for d in detalle if d["error"]),
        "regla_arranques": normas.REGLA_ARRANQUES,
    }


def control_por_ratio(peso_kg, volumen_concreto_m3, elemento: str) -> dict:
    """Semáforo de verificación kg/m³. NO es un metrado: solo contrasta el despiece."""
    volumen = dec(volumen_concreto_m3 or 0)
    if volumen == 0:
        return {"aplica": False, "aviso": normas.REGLA_KG_M3["aviso"]}
    ratio = redondear(dec(peso_kg) / volumen, 1)
    rango = next((r for r in normas.REGLA_KG_M3["rangos_control"]
                  if r["elemento"].lower().startswith(elemento.lower()[:5])), None)
    dentro = None
    if rango:
        dentro = dec(rango["min"]) <= ratio <= dec(rango["max"])
    return {
        "aplica": True, "ratio": str(ratio), "unidad": "kg/m3",
        "rango": rango, "dentro_de_rango": dentro,
        "aviso": normas.REGLA_KG_M3["aviso"],
        "etiqueta": normas.COSTUMBRE_OBRA,
        "mensaje": ("El despiece está dentro del rango habitual." if dentro
                    else "El despiece se aleja del rango habitual: revise si falta acero "
                         "o si sobra." if dentro is False
                    else "No hay rango de control para este elemento."),
    }
