"""
Dosificacion de concreto por metodo de volumenes (ACI / practica peruana).
Unidades: kg/cm2 para f'c, m3 para agregados y agua, bolsas de 42.5 kg para cemento.
Datos base tomados de tabla de dosificacion referencial (bolsas/m3, arena m3, piedra m3, agua m3).
"""

from dataclasses import dataclass

# (fc, a/c, slump", Tmax", dosificacion volumen, cemento bolsas/m3, arena m3/m3, piedra m3/m3, agua m3/m3)
TABLA_BASE = [
    (140, 0.61, 4, 0.75, "1 : 2.5 : 3.5", 7.01, 0.51, 0.64, 0.184),
    (175, 0.51, 3, 0.5, "1 : 2.5 : 2.5", 8.43, 0.54, 0.55, 0.185),
    (210, 0.45, 3, 0.5, "1 : 2 : 2", 9.73, 0.52, 0.53, 0.186),
    (245, 0.38, 3, 0.5, "1 : 1.5 : 1.5", 11.5, 0.5, 0.51, 0.187),
    (280, 0.38, 3, 0.5, "1 : 1 : 1.5", 13.34, 0.45, 0.51, 0.189),
]

PESO_BOLSA_CEMENTO_KG = 42.5


@dataclass
class Dosificacion:
    fc: float
    a_c: float
    slump_pulg: float
    tmax_pulg: float
    dosificacion_volumen: str
    cemento_bolsas_m3: float
    arena_m3_m3: float
    piedra_m3_m3: float
    agua_m3_m3: float
    interpolado: bool


@dataclass
class Requerimiento:
    fc: float
    volumen_m3: float
    dosificacion: Dosificacion
    cemento_bolsas: float
    cemento_kg: float
    arena_m3: float
    piedra_m3: float
    agua_m3: float
    agua_litros: float


@dataclass
class Precios:
    """Precios unitarios en la moneda elegida (por defecto S/)."""

    cemento_bolsa: float = 0.0
    arena_m3: float = 0.0
    piedra_m3: float = 0.0
    agua_m3: float = 0.0


@dataclass
class LineaCosto:
    material: str
    cantidad: float
    unidad: str
    precio_unit: float
    parcial: float


@dataclass
class Presupuesto:
    lineas: list
    total: float
    costo_m3: float
    moneda: str = "S/"


def _interpolar(fc):
    fcs = [fila[0] for fila in TABLA_BASE]

    if fc <= fcs[0]:
        fila = TABLA_BASE[0]
        return Dosificacion(
            fc, fila[1], fila[2], fila[3], fila[4], fila[5], fila[6], fila[7], fila[8],
            interpolado=fc != fila[0],
        )
    if fc >= fcs[-1]:
        fila = TABLA_BASE[-1]
        return Dosificacion(
            fc, fila[1], fila[2], fila[3], fila[4], fila[5], fila[6], fila[7], fila[8],
            interpolado=fc != fila[0],
        )

    for i in range(len(TABLA_BASE) - 1):
        f0 = TABLA_BASE[i]
        f1 = TABLA_BASE[i + 1]
        if f0[0] <= fc <= f1[0]:
            if fc == f0[0]:
                return Dosificacion(
                    fc, f0[1], f0[2], f0[3], f0[4], f0[5], f0[6], f0[7], f0[8],
                    interpolado=False,
                )
            if fc == f1[0]:
                return Dosificacion(
                    fc, f1[1], f1[2], f1[3], f1[4], f1[5], f1[6], f1[7], f1[8],
                    interpolado=False,
                )
            t = (fc - f0[0]) / (f1[0] - f0[0])

            def interp(a, b):
                return a + t * (b - a)

            return Dosificacion(
                fc=fc,
                a_c=round(interp(f0[1], f1[1]), 3),
                slump_pulg=round(interp(f0[2], f1[2]), 2),
                tmax_pulg=round(interp(f0[3], f1[3]), 2),
                dosificacion_volumen=f"{f0[4]} a {f1[4]} (interpolado)",
                cemento_bolsas_m3=round(interp(f0[5], f1[5]), 3),
                arena_m3_m3=round(interp(f0[6], f1[6]), 3),
                piedra_m3_m3=round(interp(f0[7], f1[7]), 3),
                agua_m3_m3=round(interp(f0[8], f1[8]), 4),
                interpolado=True,
            )

    raise ValueError(f"No se pudo interpolar f'c = {fc}")


def calcular(fc, volumen_m3, desperdicio_pct=0.0, peso_bolsa=PESO_BOLSA_CEMENTO_KG):
    if fc <= 0:
        raise ValueError("f'c debe ser mayor a 0")
    if volumen_m3 <= 0:
        raise ValueError("El volumen debe ser mayor a 0")
    if desperdicio_pct < 0:
        raise ValueError("El desperdicio no puede ser negativo")
    if peso_bolsa <= 0:
        raise ValueError("El peso de la bolsa de cemento debe ser mayor a 0")

    dos = _interpolar(fc)
    factor = volumen_m3 * (1 + desperdicio_pct / 100.0)

    # La tabla base entrega bolsas/m3 con bolsa de 42.5 kg (practica peruana).
    # Se convierte a kg y luego se re-expresa en bolsas del peso elegido por el
    # usuario, para paises donde la bolsa pesa distinto (p. ej. 50 kg).
    cemento_kg_total = dos.cemento_bolsas_m3 * PESO_BOLSA_CEMENTO_KG * factor
    cemento_bolsas = cemento_kg_total / peso_bolsa
    arena_m3 = dos.arena_m3_m3 * factor
    piedra_m3 = dos.piedra_m3_m3 * factor
    agua_m3 = dos.agua_m3_m3 * factor

    return Requerimiento(
        fc=fc,
        volumen_m3=volumen_m3,
        dosificacion=dos,
        cemento_bolsas=round(cemento_bolsas, 2),
        cemento_kg=round(cemento_kg_total, 1),
        arena_m3=round(arena_m3, 3),
        piedra_m3=round(piedra_m3, 3),
        agua_m3=round(agua_m3, 3),
        agua_litros=round(agua_m3 * 1000, 1),
    )


def calcular_presupuesto(req, precios, moneda="S/"):
    lineas = [
        LineaCosto("Cemento", req.cemento_bolsas, "bolsas", precios.cemento_bolsa,
                   round(req.cemento_bolsas * precios.cemento_bolsa, 2)),
        LineaCosto("Arena", req.arena_m3, "m3", precios.arena_m3,
                   round(req.arena_m3 * precios.arena_m3, 2)),
        LineaCosto("Piedra / agregado grueso", req.piedra_m3, "m3", precios.piedra_m3,
                   round(req.piedra_m3 * precios.piedra_m3, 2)),
        LineaCosto("Agua", req.agua_m3, "m3", precios.agua_m3,
                   round(req.agua_m3 * precios.agua_m3, 2)),
    ]
    total = round(sum(l.parcial for l in lineas), 2)
    costo_m3 = round(total / req.volumen_m3, 2) if req.volumen_m3 else 0.0
    return Presupuesto(lineas=lineas, total=total, costo_m3=costo_m3, moneda=moneda)
