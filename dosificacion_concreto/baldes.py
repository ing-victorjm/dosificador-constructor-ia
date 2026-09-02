"""
Vaciado en obra con trompo (mezcladora): conversion de la dosificacion en
volumen a BALDES por bolsa de cemento, y recomendaciones de obra.

Metodo del balde (practica peruana):
- La proporcion en volumen (1 : a : b) esta en pie3: 1 pie3 de cemento = 1 bolsa.
- Se mide el volumen real del balde (tronco de cono) y se convierte cada pie3
  de agregado a numero de baldes:  baldes = (prop * 0.0283168 m3) / V_balde.
- El agua por bolsa sale de la relacion agua/cemento (a/c) por el peso de bolsa.
"""

import math
import re
from dataclasses import dataclass

from .elementos import PIE3_A_M3


def volumen_balde_m3(diam_inf_cm, diam_sup_cm, altura_cm):
    """Volumen de un balde (tronco de cono): V = h*pi/3 * (R1^2 + R2^2 + R1*R2)."""
    r1 = (diam_inf_cm / 100.0) / 2.0
    r2 = (diam_sup_cm / 100.0) / 2.0
    h = altura_cm / 100.0
    return (h * math.pi / 3.0) * (r1 * r1 + r2 * r2 + r1 * r2)


def parse_proporcion(texto):
    """Extrae (cemento, arena, piedra) de un texto como '1 : 2.5 : 3.5'."""
    nums = re.findall(r"[0-9]+(?:\.[0-9]+)?", texto or "")
    if len(nums) >= 3:
        return (float(nums[0]), float(nums[1]), float(nums[2]))
    return (1.0, 2.0, 2.0)


def proporcion_volumen(fc):
    """Proporcion en volumen (1 : arena : piedra) interpolada numericamente.

    Se interpola sobre la tabla base para evitar el problema de leer el texto
    'interpolado' (que es un rango). Devuelve numeros reales de proporcion.
    """
    from . import modelo

    filas = []
    for row in modelo.TABLA_BASE:
        _, a, b = parse_proporcion(row[4])
        filas.append((row[0], a, b))
    fcs = [f[0] for f in filas]

    if fc <= fcs[0]:
        return (1.0, filas[0][1], filas[0][2])
    if fc >= fcs[-1]:
        return (1.0, filas[-1][1], filas[-1][2])
    for i in range(len(filas) - 1):
        f0, f1 = filas[i], filas[i + 1]
        if f0[0] <= fc <= f1[0]:
            if fc == f0[0]:
                return (1.0, f0[1], f0[2])
            t = (fc - f0[0]) / (f1[0] - f0[0])
            a = f0[1] + t * (f1[1] - f0[1])
            b = f0[2] + t * (f1[2] - f0[2])
            return (1.0, round(a, 2), round(b, 2))
    return (1.0, filas[-1][1], filas[-1][2])


@dataclass
class DosificacionBaldes:
    volumen_balde_l: float
    prop_cemento: float
    prop_arena: float
    prop_piedra: float
    baldes_arena: float
    baldes_piedra: float
    agua_litros_bolsa: float
    baldes_agua: float
    tandas: float


def dosificar_por_baldes(dos, req, vol_balde_m3, peso_bolsa):
    c, a, b = proporcion_volumen(req.fc)
    vol_balde_l = vol_balde_m3 * 1000.0

    # La proporcion 1:a:b asume 1 bolsa = 1 pie3 de cemento (bolsa de 42.5 kg).
    # Con bolsas de otro peso (p. ej. 50 kg) el cemento por bolsa cambia, asi
    # que los agregados por bolsa escalan en la misma relacion.
    f_bolsa = peso_bolsa / 42.5
    arena_m3_bolsa = a * PIE3_A_M3 * f_bolsa
    piedra_m3_bolsa = b * PIE3_A_M3 * f_bolsa
    baldes_arena = arena_m3_bolsa / vol_balde_m3 if vol_balde_m3 else 0.0
    baldes_piedra = piedra_m3_bolsa / vol_balde_m3 if vol_balde_m3 else 0.0

    agua_l_bolsa = dos.a_c * peso_bolsa
    baldes_agua = agua_l_bolsa / vol_balde_l if vol_balde_l else 0.0

    return DosificacionBaldes(
        volumen_balde_l=round(vol_balde_l, 1),
        prop_cemento=c,
        prop_arena=a,
        prop_piedra=b,
        baldes_arena=round(baldes_arena, 2),
        baldes_piedra=round(baldes_piedra, 2),
        agua_litros_bolsa=round(agua_l_bolsa, 1),
        baldes_agua=round(baldes_agua, 2),
        tandas=round(req.cemento_bolsas, 1),
    )


def palabras_maestro(req, bal, peso_bolsa):
    """Instrucciones claras para el maestro de obra (control del trompo)."""
    tandas = math.ceil(req.cemento_bolsas)
    return (
        f"Maestro: para f'c = {req.fc:.0f} kg/cm2, por CADA bolsa de cemento "
        f"({peso_bolsa:g} kg) eche:\n"
        f"   • {bal.baldes_arena:g} baldes de ARENA\n"
        f"   • {bal.baldes_piedra:g} baldes de PIEDRA\n"
        f"   • {bal.agua_litros_bolsa:g} litros de AGUA "
        f"(≈ {bal.baldes_agua:g} baldes)\n"
        f"Use SIEMPRE el mismo balde de {bal.volumen_balde_l:g} litros y llenelo "
        f"al ras. Son aprox. {tandas} tandas (1 bolsa por tanda) para todo el "
        f"vaciado.\n"
        f"NO aumente el agua para \"que corra mejor\": eso baja la resistencia. "
        f"Si esta muy seco, use plastificante. Respete el slump de "
        f"{req.dosificacion.slump_pulg:g}\" y haga la prueba de slump al inicio "
        f"y cada 5 tandas."
    )


def material_a_pedir(req, margen_pct=5.0):
    """Cantidades a comprar/pedir, con un margen por manipuleo."""
    f = 1 + margen_pct / 100.0
    return {
        "cemento_bolsas": math.ceil(req.cemento_bolsas),
        "arena_m3": round(req.arena_m3 * f, 2),
        "piedra_m3": round(req.piedra_m3 * f, 2),
        "agua_litros": round(req.agua_litros, 0),
        "margen_pct": margen_pct,
    }


# Recomendaciones de aditivos (informativas)
ADITIVOS = [
    ("Plastificante / reductor de agua",
     "Mejora la trabajabilidad SIN agregar agua. Ideal cuando la mezcla sale seca."),
    ("Acelerante de fragua",
     "Clima frio o cuando se necesita desencofrar rapido. No usar con clima muy caluroso."),
    ("Retardante",
     "Clima caluroso o vaciados largos (losas grandes), evita juntas frias."),
    ("Impermeabilizante",
     "Cisternas, tanques, sotanos y elementos en contacto con agua o terreno humedo."),
    ("Incorporador de aire",
     "Zonas de heladas / congelamiento; mejora la durabilidad."),
]


def recomendaciones_obra(req):
    """Texto de recomendaciones tecnicas segun la mezcla calculada."""
    dos = req.dosificacion
    lineas = [
        f"Slump (asentamiento) objetivo: {dos.slump_pulg:g}\" — verificar con cono de Abrams.",
        f"Tamano maximo del agregado (TMN): {dos.tmax_pulg:g}\".",
        f"Relacion agua/cemento (a/c): {dos.a_c:g} — es el limite; no pasarse de agua.",
        "Curado: mantener humedo minimo 7 dias (regar o cubrir). Es lo que mas sube la resistencia.",
        "Probetas: tomar 2-3 testigos por vaciado importante para rotura a 7 y 28 dias.",
        "Vibrado: chuzar o vibrar para sacar el aire; no dejar cangrejeras.",
    ]
    return lineas
