"""Calculo de estribos en columnas rectangulares (NTE E.060 / ACI 318-19)."""

import math
from dataclasses import dataclass

# Diametros comerciales Peru (mm)
DIAMS_ESTRIBO = {
    "6 mm (1/4\")": 6.000,
    "8 mm (5/16\")": 8.000,
    "9.5 mm (3/8\")": 9.525,
    "12.7 mm (1/2\")": 12.700,
}

DIAMS_LONG = {
    "9.5 mm (3/8\")": 9.525,
    "12.7 mm (1/2\")": 12.700,
    "15.9 mm (5/8\")": 15.875,
    "19.1 mm (3/4\")": 19.050,
    "22.2 mm (7/8\")": 22.225,
    "25.4 mm (1\")": 25.400,
}

# Peso lineal (kg/m) por diametro en mm
# Pesos nominales ASTM A615 Gr.60 / NTP 341.031 (ficha de Aceros Arequipa).
# Ojo con los pares que se confunden en obra: 6 mm no es 1/4", 8 mm no es 5/16"
# y 12 mm no es 1/2". Se listan por separado con su peso real.
PESO_KG_M = {
    6.000: 0.222,    # 6 mm
    6.350: 0.250,    # 1/4"
    7.900: 0.384,    # 5/16"
    8.000: 0.395,    # 8 mm
    9.525: 0.560,    # 3/8"
    12.000: 0.888,   # 12 mm
    12.700: 0.994,   # 1/2"
    15.875: 1.552,   # 5/8"
    19.050: 2.235,   # 3/4"
    22.225: 3.042,   # 7/8"
    25.400: 3.973,   # 1"
    35.800: 7.907,   # 1 3/8"
}


@dataclass
class ResultadoEstribos:
    lo_cm: float
    s1_cm: float
    s2_cm: float
    n_conf_inf: int
    n_central: int
    n_conf_sup: int
    n_total: int
    long_estribo_cm: float
    peso_total_kg: float
    kg_por_ml: float
    detalle: str
    posiciones_cm: list  # list[float] desde base (para diagrama)


def calcular_lo(h_cm: float, a_cm: float, b_cm: float) -> float:
    """Longitud de zona confinada segun NTE E.060-2009 art.21.6.4.1"""
    return max(h_cm / 6.0, max(a_cm, b_cm), 50.0)


# Sistemas estructurales de la E.060. La separacion de estribos NO es la misma
# en los dos, y antes aqui se aplicaba una unica formula que ademas venia del
# ACI 318 (d_min/4), no de la E.060, pese a que la pantalla decia "auto E.060".
PORTICOS = "porticos"   # porticos y dual II  -> E.060 21.6.4
MUROS = "muros"         # muros estructurales y dual I -> E.060 21.4.5


def s_max_confinada(
    a_cm: float, b_cm: float, db_mm: float, de_mm: float, sistema: str = PORTICOS
) -> float:
    """Separacion maxima dentro de la zona de confinamiento Lo.

    E.060 21.6.4.2 (porticos y dual II): la menor de un tercio de la dimension
    minima del elemento, seis veces el diametro de la barra longitudinal, y 100 mm.
    E.060 21.4.5.3 (muros estructurales y dual I): la menor de ocho veces el
    diametro de la barra longitudinal, la mitad de la menor dimension, y 100 mm.

    Antes se usaba d_min/4, que es ACI 318-19 18.7.5.3(a) y no existe en la
    E.060: sobrecontaba ~35% en la zona confinada.
    """
    d_min = min(a_cm, b_cm)
    db_cm = db_mm / 10.0
    if sistema == MUROS:
        return min(8.0 * db_cm, d_min / 2.0, 10.0)
    return min(d_min / 3.0, 6.0 * db_cm, 10.0)


def s_max_central(
    db_mm: float, de_mm: float, a_cm: float = 0.0, b_cm: float = 0.0,
    sistema: str = PORTICOS
) -> float:
    """Separacion maxima fuera de la zona de confinamiento.

    E.060 21.6.4.5 (porticos y dual II): no mayor que la menor de diez veces el
    diametro de la barra longitudinal y 250 mm.
    E.060 21.4.5.4 remite a 7.10.5.2 (16 db, 48 de, menor dimension del elemento)
    y a 11.5.5.1 (d/2), con tope de 300 mm.

    Antes se aplicaba siempre la regla de columna SIN responsabilidad sismica, y
    ademas incompleta (el tercer limite estaba cableado en 30 cm): subcontaba
    hasta 60% en la zona central.
    """
    db_cm = db_mm / 10.0
    de_cm = de_mm / 10.0
    if sistema == MUROS:
        d_min = min(a_cm, b_cm) if a_cm and b_cm else float("inf")
        # d/2 con el peralte efectivo aproximado como la dimension menos el
        # recubrimiento tipico; se acota por el tope de 300 mm de todos modos.
        return min(16.0 * db_cm, 48.0 * de_cm, d_min, 30.0)
    return min(10.0 * db_cm, 25.0)


def longitud_estribo_cm(a_cm: float, b_cm: float, rec_cm: float, de_mm: float) -> float:
    """Longitud total de un estribo rectangular con ganchos sismicos 135°."""
    a_n = a_cm - 2.0 * rec_cm
    b_n = b_cm - 2.0 * rec_cm
    perimetro = 2.0 * (a_n + b_n)
    de_cm = de_mm / 10.0
    radio = 2.5 * de_cm                          # radio minimo de doblado
    arco = math.pi * (135.0 / 180.0) * radio     # arco del gancho 135°
    # E.060 21.1, gancho sismico: doblez de 135 grados con extension de OCHO
    # veces el diametro de la barra, no menor de 75 mm. Antes decia 6 db, que es
    # el gancho general del ACI; dejaba ~5 kg sin metrar por cada 100 estribos.
    ext = max(8.0 * de_cm, 7.5)
    gancho = arco + ext
    return perimetro + 2.0 * gancho


def _posiciones_zonas(lo: float, s1: float, s2: float, h: float, l_central: float):
    """Posiciones (cm desde la base) de cada estribo, separadas por zona.

    Zona inferior: primer estribo a s1/2 de la base, luego cada s1 hasta Lo.
    Zona superior: espejo de la inferior (primer estribo a s1/2 del tope).
    Zona central: desde Lo + s2/2, cada s2, hasta h - Lo.
    """
    inf = []
    y = s1 / 2.0
    while y <= lo + 1e-3:
        inf.append(round(y, 1))
        y += s1
    sup = [round(h - y, 1) for y in inf]
    cent = []
    if l_central > 1e-3:
        yc = lo + s2 / 2.0
        while yc <= h - lo + 1e-3:
            cent.append(round(yc, 1))
            yc += s2
    return inf, cent, sorted(sup)


def calcular(
    h_cm: float,
    a_cm: float,
    b_cm: float,
    de_mm: float,
    db_mm: float,
    rec_cm: float = 4.0,
    s1_manual: float = None,
    s2_manual: float = None,
    lo_manual: float = None,
    sistema: str = PORTICOS,
) -> ResultadoEstribos:
    lo = lo_manual if lo_manual else calcular_lo(h_cm, a_cm, b_cm)
    lo = min(lo, h_cm / 2.0)
    s1 = s1_manual if s1_manual else s_max_confinada(a_cm, b_cm, db_mm, de_mm, sistema)
    s2 = s2_manual if s2_manual else s_max_central(db_mm, de_mm, a_cm, b_cm, sistema)
    # E-25: con separaciones <= 0 los bucles de posiciones no terminan nunca y
    # el servidor se queda colgado. Se rechaza antes de entrar.
    if s1 <= 0 or s2 <= 0:
        raise ValueError("Las separaciones s1 y s2 deben ser mayores que cero.")
    if h_cm <= 0 or a_cm <= 0 or b_cm <= 0:
        raise ValueError("Las dimensiones de la columna deben ser mayores que cero.")

    l_central = max(0.0, h_cm - 2.0 * lo)

    # Conteo por zona derivado de las posiciones reales (coincide con el diagrama)
    pos_inf, pos_cent, pos_sup = _posiciones_zonas(lo, s1, s2, h_cm, l_central)
    n_conf = len(pos_inf)
    n_cent = len(pos_cent)
    n_total = n_conf + n_cent + len(pos_sup)

    long_est = longitud_estribo_cm(a_cm, b_cm, rec_cm, de_mm)
    peso_unit = PESO_KG_M.get(de_mm, (math.pi * (de_mm / 2000.0) ** 2) * 7850.0)
    peso_total = n_total * long_est / 100.0 * peso_unit
    kg_ml = n_total * peso_unit * long_est / 100.0 / (h_cm / 100.0)

    pos = sorted(set(pos_inf + pos_cent + pos_sup))

    detalle = (
        f"Lo = {lo:.0f} cm  ·  s1 = {s1:.1f} cm  ·  s2 = {s2:.1f} cm  ·  "
        f"L.estribo = {long_est:.1f} cm"
    )

    return ResultadoEstribos(
        lo_cm=round(lo, 1),
        s1_cm=round(s1, 1),
        s2_cm=round(s2, 1),
        n_conf_inf=n_conf,
        n_central=n_cent,
        n_conf_sup=n_conf,
        n_total=n_total,
        long_estribo_cm=round(long_est, 1),
        peso_total_kg=round(peso_total, 3),
        kg_por_ml=round(kg_ml, 3),
        detalle=detalle,
        posiciones_cm=pos,
    )
