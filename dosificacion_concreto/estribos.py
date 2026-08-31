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
PESO_KG_M = {
    6.000: 0.222,
    8.000: 0.395,
    9.525: 0.560,
    12.700: 0.994,
    15.875: 1.552,
    19.050: 2.235,
    22.225: 3.042,
    25.400: 3.973,
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


def s_max_confinada(a_cm: float, b_cm: float, db_mm: float, de_mm: float) -> float:
    """Separacion maxima en zona confinada (menor valor NTE E.060)"""
    d_min = min(a_cm, b_cm)
    return min(d_min / 4.0, 6.0 * db_mm / 10.0, 10.0)


def s_max_central(db_mm: float, de_mm: float) -> float:
    """Separacion maxima en zona central (menor valor NTE E.060)"""
    return min(16.0 * db_mm / 10.0, 48.0 * de_mm / 10.0, 30.0)


def longitud_estribo_cm(a_cm: float, b_cm: float, rec_cm: float, de_mm: float) -> float:
    """Longitud total de un estribo rectangular con ganchos sismicos 135°."""
    a_n = a_cm - 2.0 * rec_cm
    b_n = b_cm - 2.0 * rec_cm
    perimetro = 2.0 * (a_n + b_n)
    de_cm = de_mm / 10.0
    radio = 2.5 * de_cm                          # radio minimo de doblado
    arco = math.pi * (135.0 / 180.0) * radio     # arco del gancho 135°
    ext = max(6.0 * de_cm, 7.5)                  # extension libre >= 75 mm
    gancho = arco + ext
    return perimetro + 2.0 * gancho


def _posiciones(lo: float, s1: float, s2: float, h: float, l_central: float):
    """Genera lista de posiciones (cm desde la base) de cada estribo."""
    pos = []
    # Zona confinada inferior: primer estribo a s1/2 del extremo, luego a s1
    y = s1 / 2.0
    while y <= lo + 1e-3:
        pos.append(round(y, 1))
        y += s1
    # Zona central
    if l_central > 1e-3:
        y_start = lo + s2 / 2.0
        y_end = lo + l_central
        yc = y_start
        while yc <= y_end + 1e-3:
            pos.append(round(yc, 1))
            yc += s2
    # Zona confinada superior
    y_sup_base = h - lo
    y = y_sup_base + s1 / 2.0
    while y <= h + 1e-3:
        pos.append(round(y, 1))
        y += s1
    return sorted(set(pos))


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
) -> ResultadoEstribos:
    lo = lo_manual if lo_manual else calcular_lo(h_cm, a_cm, b_cm)
    lo = min(lo, h_cm / 2.0)
    s1 = s1_manual if s1_manual else s_max_confinada(a_cm, b_cm, db_mm, de_mm)
    s2 = s2_manual if s2_manual else s_max_central(db_mm, de_mm)

    l_central = max(0.0, h_cm - 2.0 * lo)

    # Conteo por zona
    n_conf = math.ceil((lo - s1 / 2.0) / s1) + 1  # primer est a s1/2
    n_cent = math.ceil((l_central - s2 / 2.0) / s2) + 1 if l_central > 1e-3 else 0
    n_total = 2 * n_conf + n_cent

    long_est = longitud_estribo_cm(a_cm, b_cm, rec_cm, de_mm)
    peso_unit = PESO_KG_M.get(de_mm, (math.pi * (de_mm / 2000.0) ** 2) * 7850.0)
    peso_total = n_total * long_est / 100.0 * peso_unit
    kg_ml = n_total * peso_unit * long_est / 100.0 / (h_cm / 100.0)

    pos = _posiciones(lo, s1, s2, h_cm, l_central)

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
