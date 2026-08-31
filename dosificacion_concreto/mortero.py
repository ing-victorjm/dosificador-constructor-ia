"""
Mortero para albanileria: asentado de ladrillos y tarrajeo (revoque).

El mortero es cemento + arena (sin piedra). Se calcula el volumen de mortero de
la partida y luego se convierte a bolsas de cemento y m3 de arena segun la
proporcion en volumen (1 : n). Valores de dosificacion referenciales para bolsa
de cemento de 42.5 kg (practica peruana). Verificar con diseno del proyecto.
"""

from dataclasses import dataclass

# Proporcion de mortero 1:n -> (bolsas de cemento por m3, arena m3 por m3 de mortero)
PROPORCIONES = {
    "1:3": (11.0, 1.03),
    "1:4": (8.9, 1.09),
    "1:5": (7.4, 1.10),
    "1:6": (6.2, 1.10),
}

# Ladrillos comunes (Peru): (nombre, largo_cm, ancho_cm, alto_cm)
LADRILLOS = [
    ("King Kong 18 huecos", 23.0, 12.5, 9.0),
    ("King Kong artesanal", 24.0, 13.0, 9.0),
    ("Pandereta", 23.0, 11.0, 9.0),
    ("Bloque de concreto", 39.0, 19.0, 19.0),
]

# Aparejo -> como se apoya el ladrillo. Da (indice_largo_cara, indice_alto_cara, indice_espesor)
# indices sobre (largo, ancho, alto)
APAREJOS = {
    "Soga": (0, 2, 1),    # cara vista: largo x alto ; espesor de muro = ancho
    "Cabeza": (1, 2, 0),  # cara vista: ancho x alto ; espesor = largo
    "Canto": (0, 1, 2),   # cara vista: largo x ancho ; espesor = alto
}


@dataclass
class MorteroResultado:
    volumen_mortero_m3: float
    cemento_bolsas: float
    arena_m3: float
    detalle: str
    ladrillos: float = 0.0
    ladrillos_por_m2: float = 0.0


def _dosificar(volumen_m3, proporcion, desperdicio_pct):
    vol = volumen_m3 * (1 + desperdicio_pct / 100.0)
    bolsas_m3, arena_m3_m3 = PROPORCIONES.get(proporcion, PROPORCIONES["1:5"])
    return vol, round(vol * bolsas_m3, 1), round(vol * arena_m3_m3, 2)


def asentado(area_muro_m2, ladrillo, aparejo, junta_cm=1.5,
             proporcion="1:4", desperdicio_pct=10.0):
    """Mortero y ladrillos para asentar un muro de albanileria."""
    dims = ladrillo[1:]  # (largo, ancho, alto) en cm
    i_l, i_h, i_e = APAREJOS.get(aparejo, APAREJOS["Soga"])
    cara_l = dims[i_l] / 100.0
    cara_h = dims[i_h] / 100.0
    espesor = dims[i_e] / 100.0
    j = junta_cm / 100.0

    por_m2 = 1.0 / ((cara_l + j) * (cara_h + j))
    vol_ladrillo = (dims[0] / 100.0) * (dims[1] / 100.0) * (dims[2] / 100.0)
    # volumen de mortero por m2 = volumen del muro - volumen de ladrillos
    mortero_m2 = max(0.0, espesor - por_m2 * vol_ladrillo)
    vol_mortero = area_muro_m2 * mortero_m2

    vol, bolsas, arena = _dosificar(vol_mortero, proporcion, desperdicio_pct)
    ladrillos = area_muro_m2 * por_m2 * 1.05  # +5% por roturas
    return MorteroResultado(
        volumen_mortero_m3=round(vol, 3),
        cemento_bolsas=bolsas,
        arena_m3=arena,
        detalle=f"Aparejo {aparejo} · muro e={espesor * 100:.0f} cm · junta {junta_cm:g} cm · {proporcion}",
        ladrillos=round(ladrillos, 0),
        ladrillos_por_m2=round(por_m2, 1),
    )


def tarrajeo(area_m2, espesor_cm=1.5, proporcion="1:5", desperdicio_pct=10.0,
             caras=1):
    """Mortero para tarrajeo/revoque (una o dos caras)."""
    vol_mortero = area_m2 * (espesor_cm / 100.0) * max(1, caras)
    vol, bolsas, arena = _dosificar(vol_mortero, proporcion, desperdicio_pct)
    return MorteroResultado(
        volumen_mortero_m3=round(vol, 3),
        cemento_bolsas=bolsas,
        arena_m3=arena,
        detalle=f"Tarrajeo e={espesor_cm:g} cm · {caras} cara(s) · {proporcion}",
    )
