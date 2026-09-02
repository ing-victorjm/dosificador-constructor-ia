"""Análisis de precios unitarios y resumen de presupuesto.

Convención S10, que es la que espera cualquier revisor en LatAm:

* Mano de obra y equipo: `cantidad = cuadrilla × jornada / rendimiento`, a 4 dec.
* `PU = redondear(Σ parciales del APU)` — el redondeo se hace en el precio
  unitario, no al final, para que el presupuesto impreso cuadre línea a línea.
* `Parcial = redondear(metrado × PU)`.

El desperdicio vive AQUÍ, en el APU, nunca en el metrado.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .redondeo import ReglasRedondeo, dec, redondear

JORNADA_HORAS = dec("8")

TIPOS = {"MO": "Mano de obra", "MAT": "Materiales", "EQ": "Equipos", "SC": "Subcontratos"}


@dataclass
class LineaApu:
    tipo: str
    descripcion: str
    unidad: str
    cantidad: Decimal
    precio: Decimal
    parcial: Decimal
    cuadrilla: Decimal | None = None
    rendimiento: Decimal | None = None
    formula: str = ""

    def a_dict(self) -> dict:
        return {
            "tipo": self.tipo, "descripcion": self.descripcion, "unidad": self.unidad,
            "cuadrilla": None if self.cuadrilla is None else str(self.cuadrilla),
            "rendimiento": None if self.rendimiento is None else str(self.rendimiento),
            "cantidad": str(self.cantidad), "precio": str(self.precio),
            "parcial": str(self.parcial), "formula": self.formula,
        }


def cantidad_linea(fila: dict, rendimiento_partida) -> tuple[Decimal, str]:
    """Cantidad de insumo por unidad de partida, con la fórmula que la explica."""
    tipo = (fila.get("tipo") or "MAT").upper()
    cuadrilla = fila.get("cuadrilla")
    rendimiento = fila.get("rendimiento") or rendimiento_partida

    if tipo in ("MO", "EQ") and cuadrilla not in (None, ""):
        r = dec(rendimiento or 0)
        if r == 0:
            return Decimal(0), "Falta el rendimiento de la partida."
        c = dec(cuadrilla)
        cantidad = c * JORNADA_HORAS / r
        return (redondear(cantidad, 4),
                f"{c} × {JORNADA_HORAS} h / {r} = {redondear(cantidad, 4)}")
    return dec(fila.get("cantidad") or 0), ""


def analisis(filas: list[dict], rendimiento_partida=None,
             reglas: ReglasRedondeo | None = None) -> dict:
    """Calcula el APU completo de una partida."""
    reglas = reglas or ReglasRedondeo()
    lineas: list[LineaApu] = []
    por_tipo: dict[str, Decimal] = {t: Decimal(0) for t in TIPOS}

    total_mo = Decimal(0)
    for fila in filas:
        tipo = (fila.get("tipo") or "MAT").upper()
        if tipo == "MO":
            cantidad, _ = cantidad_linea(fila, rendimiento_partida)
            total_mo += redondear(cantidad * dec(fila.get("precio") or 0), 2)

    for fila in filas:
        tipo = (fila.get("tipo") or "MAT").upper()
        precio = dec(fila.get("precio") or 0)
        unidad = fila.get("unidad") or "und"

        # Herramientas menores: porcentaje de la mano de obra, no una cantidad.
        if unidad == "pct" or str(fila.get("unidad")).strip() == "%":
            pct = dec(fila.get("cantidad") or 0)
            parcial = redondear(total_mo * pct / 100, 2)
            lineas.append(LineaApu(tipo, fila.get("descripcion") or "", "%",
                                   pct, total_mo, parcial,
                                   formula=f"{pct}% de {total_mo} (mano de obra)"))
            por_tipo[tipo] = por_tipo.get(tipo, Decimal(0)) + parcial
            continue

        cantidad, formula = cantidad_linea(fila, rendimiento_partida)
        desperdicio = dec(fila.get("desperdicio_pct") or 0)
        if desperdicio:
            cantidad = redondear(cantidad * (1 + desperdicio / 100), 4)
            formula = (formula + " " if formula else "") + f"+ {desperdicio}% desperdicio"
        parcial = redondear(cantidad * precio, 2)
        lineas.append(LineaApu(
            tipo, fila.get("descripcion") or "", unidad, cantidad, precio, parcial,
            cuadrilla=dec(fila["cuadrilla"]) if fila.get("cuadrilla") else None,
            rendimiento=dec(fila["rendimiento"]) if fila.get("rendimiento") else None,
            formula=formula,
        ))
        por_tipo[tipo] = por_tipo.get(tipo, Decimal(0)) + parcial

    pu = reglas.precio(sum(l.parcial for l in lineas))
    return {
        "lineas": [l.a_dict() for l in lineas],
        "por_tipo": {k: str(v) for k, v in por_tipo.items()},
        "total_mo": str(total_mo),
        "pu": str(pu),
        "rendimiento": None if rendimiento_partida is None else str(rendimiento_partida),
    }


def resumen(costo_directo, gg_pct=0, utilidad_pct=0, impuesto_pct=0,
            nombre_impuesto: str = "IGV", reglas: ReglasRedondeo | None = None) -> dict:
    """Pie del presupuesto: CD → GG → utilidad → subtotal → impuesto → total."""
    reglas = reglas or ReglasRedondeo()
    cd = dec(costo_directo)
    gg = reglas.parcial(cd * dec(gg_pct) / 100)
    ut = reglas.parcial(cd * dec(utilidad_pct) / 100)
    subtotal = reglas.parcial(cd + gg + ut)
    impuesto = reglas.parcial(subtotal * dec(impuesto_pct) / 100)
    total = reglas.parcial(subtotal + impuesto)
    return {
        "costo_directo": str(reglas.parcial(cd)),
        "gastos_generales": str(gg), "gastos_generales_pct": str(dec(gg_pct)),
        "utilidad": str(ut), "utilidad_pct": str(dec(utilidad_pct)),
        "subtotal": str(subtotal),
        "impuesto": str(impuesto), "impuesto_pct": str(dec(impuesto_pct)),
        "nombre_impuesto": nombre_impuesto,
        "total": str(total),
    }


def curva_s(items: list[dict], meses: int, reglas: ReglasRedondeo | None = None) -> dict:
    """Cronograma valorizado básico: reparte cada partida en su ventana de meses.

    Es deliberadamente simple: sin CPM ni holguras. Distribuye por especialidad
    en el orden natural de obra (preliminares → estructuras → arquitectura →
    instalaciones) para dar una curva creíble sin pedir fechas partida por
    partida. Cuando el usuario asigne fechas reales, sustituye a esta estimación.
    """
    reglas = reglas or ReglasRedondeo()
    meses = max(1, min(int(meses or 1), 120))
    ventanas = {
        "preliminares": (0.00, 0.20), "movimiento_tierras": (0.05, 0.30),
        "estructuras": (0.10, 0.65), "arquitectura": (0.45, 0.95),
        "sanitarias": (0.35, 0.85), "electricas": (0.35, 0.85),
        "mecanicas": (0.55, 0.95), "comunicaciones": (0.60, 0.95),
        "exteriores": (0.70, 1.00), "seguridad": (0.00, 1.00), "varios": (0.85, 1.00),
    }
    por_mes = [Decimal(0) for _ in range(meses)]
    for it in items:
        parcial = dec(it.get("parcial") or 0)
        if parcial == 0:
            continue
        inicio_pct, fin_pct = ventanas.get(it.get("especialidad"), (0.0, 1.0))
        inicio = int(inicio_pct * meses)
        fin = max(inicio + 1, int(fin_pct * meses))
        reparto = parcial / (fin - inicio)
        for m in range(inicio, min(fin, meses)):
            por_mes[m] += reparto

    acumulado = Decimal(0)
    total = sum(por_mes) or Decimal(1)
    filas = []
    for i, v in enumerate(por_mes, start=1):
        acumulado += v
        filas.append({
            "mes": i,
            "valorizacion": str(reglas.parcial(v)),
            "acumulado": str(reglas.parcial(acumulado)),
            "avance_pct": str(redondear(acumulado / total * 100, 2)),
        })
    return {"meses": filas, "total": str(reglas.parcial(sum(por_mes))),
            "nota": "Distribución estimada por especialidad. Asigne fechas a las partidas "
                    "para obtener un cronograma real."}
