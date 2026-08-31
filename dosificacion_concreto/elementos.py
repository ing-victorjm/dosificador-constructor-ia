"""
Metrado de concreto por elemento estructural.

Cada tipo de elemento define sus campos de dimensiones (en metros salvo que se
indique) y una formula que devuelve el volumen de concreto en m3 por unidad.
La cantidad de elementos identicos se aplica fuera de la formula.

Factores de losa aligerada: volumen de concreto (m3) por m2 de losa, valores
referenciales de practica peruana (viguetas @0.40 m, ladrillo de techo). Siempre
verificar con el detalle de losa del proyecto.
"""

import math
from dataclasses import dataclass, field
from typing import Callable

PIE3_A_M3 = 0.0283168  # 1 pie3 = 0.0283168 m3

# Losa aligerada UNIDIRECCIONAL: m3 de concreto por m2 (segun peralte en cm)
FACTORES_ALIGERADO_1D = {17: 0.077, 20: 0.087, 25: 0.100, 30: 0.120}
# Losa aligerada BIDIRECCIONAL (casetones / nervada en dos sentidos)
FACTORES_ALIGERADO_2D = {20: 0.100, 25: 0.120, 30: 0.140}


def _factor_cercano(tabla, peralte_cm):
    """Devuelve el factor de la tabla cuyo peralte es el mas cercano."""
    clave = min(tabla, key=lambda k: abs(k - peralte_cm))
    return tabla[clave]


@dataclass
class CampoDim:
    clave: str
    etiqueta: str
    valor: float
    minimo: float = 0.0
    maximo: float = 100000.0
    decimales: int = 2
    paso: float = 0.05
    sufijo: str = " m"


@dataclass
class TipoElemento:
    clave: str
    nombre: str
    campos: list  # list[CampoDim]
    formula: Callable  # dict[clave -> valor] -> m3 por unidad
    ayuda: str = ""


def _c(clave, etiqueta, valor, **kw):
    return CampoDim(clave, etiqueta, valor, **kw)


# --- Catalogo de elementos estructurales -----------------------------------
TIPOS = [
    TipoElemento(
        "zapata", "Zapata",
        [_c("largo", "Largo", 1.20), _c("ancho", "Ancho", 1.20),
         _c("peralte", "Peralte (altura)", 0.50)],
        lambda d: d["largo"] * d["ancho"] * d["peralte"],
        "Zapata aislada: Largo x Ancho x Peralte.",
    ),
    TipoElemento(
        "columna", "Columna",
        [_c("lado_a", "Lado a", 0.30), _c("lado_b", "Lado b", 0.30),
         _c("altura", "Altura", 2.80)],
        lambda d: d["lado_a"] * d["lado_b"] * d["altura"],
        "Columna rectangular: a x b x altura.",
    ),
    TipoElemento(
        "viga", "Viga",
        [_c("base", "Base", 0.25), _c("peralte", "Peralte", 0.50),
         _c("longitud", "Longitud", 4.00)],
        lambda d: d["base"] * d["peralte"] * d["longitud"],
        "Viga: base x peralte x longitud.",
    ),
    TipoElemento(
        "viga_cimentacion", "Viga de cimentacion",
        [_c("base", "Base", 0.30), _c("peralte", "Peralte", 0.60),
         _c("longitud", "Longitud", 4.00)],
        lambda d: d["base"] * d["peralte"] * d["longitud"],
        "Viga de cimentacion (VC): base x peralte x longitud.",
    ),
    TipoElemento(
        "cimiento_corrido", "Cimiento corrido",
        [_c("ancho", "Ancho", 0.60), _c("altura", "Altura", 0.60),
         _c("longitud", "Longitud", 5.00)],
        lambda d: d["ancho"] * d["altura"] * d["longitud"],
        "Cimiento corrido: ancho x altura x longitud.",
    ),
    TipoElemento(
        "sobrecimiento", "Sobrecimiento",
        [_c("ancho", "Ancho", 0.15), _c("altura", "Altura", 0.40),
         _c("longitud", "Longitud", 5.00)],
        lambda d: d["ancho"] * d["altura"] * d["longitud"],
        "Sobrecimiento: ancho x altura x longitud.",
    ),
    TipoElemento(
        "placa", "Placa / muro de concreto",
        [_c("espesor", "Espesor", 0.20), _c("altura", "Altura", 2.80),
         _c("longitud", "Longitud", 3.00)],
        lambda d: d["espesor"] * d["altura"] * d["longitud"],
        "Placa o muro: espesor x altura x longitud.",
    ),
    TipoElemento(
        "losa_maciza", "Losa maciza",
        [_c("area", "Area", 20.0, sufijo=" m2", paso=1.0),
         _c("espesor", "Espesor", 0.20)],
        lambda d: d["area"] * d["espesor"],
        "Losa maciza / bidireccional solida: Area x espesor.",
    ),
    TipoElemento(
        "losa_aligerada_1d", "Losa aligerada (1 direccion)",
        [_c("area", "Area", 20.0, sufijo=" m2", paso=1.0),
         _c("peralte", "Peralte", 20, minimo=17, maximo=30, decimales=0,
            paso=1, sufijo=" cm")],
        lambda d: d["area"] * _factor_cercano(FACTORES_ALIGERADO_1D, d["peralte"]),
        "Aligerado unidireccional. Concreto por m2 segun peralte (17/20/25/30 cm).",
    ),
    TipoElemento(
        "losa_aligerada_2d", "Losa aligerada (bidireccional)",
        [_c("area", "Area", 25.0, sufijo=" m2", paso=1.0),
         _c("peralte", "Peralte", 25, minimo=20, maximo=30, decimales=0,
            paso=1, sufijo=" cm")],
        lambda d: d["area"] * _factor_cercano(FACTORES_ALIGERADO_2D, d["peralte"]),
        "Aligerado bidireccional (casetones). Valor referencial por m2.",
    ),
    TipoElemento(
        "losa_piso", "Losa de piso / contrapiso",
        [_c("area", "Area", 30.0, sufijo=" m2", paso=1.0),
         _c("espesor", "Espesor", 0.10)],
        lambda d: d["area"] * d["espesor"],
        "Piso o contrapiso: Area x espesor.",
    ),
    TipoElemento(
        "zapata_combinada", "Zapata combinada",
        [_c("largo", "Largo", 2.40), _c("ancho", "Ancho", 1.20),
         _c("peralte", "Peralte", 0.50),
         _c("sep_columnas", "Separacion de columnas", 1.60),
         _c("lado_col", "Lado de columna", 0.30)],
        lambda d: d["largo"] * d["ancho"] * d["peralte"],
        "Zapata combinada bajo dos columnas: Largo x Ancho x Peralte (solo la zapata).",
    ),
    TipoElemento(
        "columna_circular", "Columna circular",
        [_c("diametro", "Diametro", 0.40), _c("altura", "Altura", 2.80)],
        lambda d: math.pi * (d["diametro"] / 2) ** 2 * d["altura"],
        "Columna circular: area del circulo x altura.",
    ),
    TipoElemento(
        "columna_t", "Columna T",
        [_c("ancho_ala", "Ancho del ala", 0.60), _c("esp_ala", "Espesor del ala", 0.20),
         _c("ancho_alma", "Ancho del alma", 0.25), _c("peralte", "Peralte total", 0.60),
         _c("altura", "Altura", 2.80)],
        lambda d: (d["ancho_ala"] * d["esp_ala"]
                   + d["ancho_alma"] * max(0.0, d["peralte"] - d["esp_ala"])) * d["altura"],
        "Columna en T: area de la seccion T x altura.",
    ),
    TipoElemento(
        "columna_l", "Columna L",
        [_c("lado1", "Lado 1", 0.60), _c("lado2", "Lado 2", 0.60),
         _c("espesor", "Espesor", 0.25), _c("altura", "Altura", 2.80)],
        lambda d: d["espesor"] * (d["lado1"] + d["lado2"] - d["espesor"]) * d["altura"],
        "Columna en L: area de la seccion L x altura.",
    ),
    TipoElemento(
        "viga_t", "Viga T",
        [_c("ancho_ala", "Ancho del ala (losa)", 0.60), _c("esp_ala", "Espesor del ala", 0.20),
         _c("ancho_alma", "Ancho del alma", 0.25), _c("peralte", "Peralte total", 0.50),
         _c("longitud", "Longitud", 4.0)],
        lambda d: (d["ancho_ala"] * d["esp_ala"]
                   + d["ancho_alma"] * max(0.0, d["peralte"] - d["esp_ala"])) * d["longitud"],
        "Viga T: area de la seccion T x longitud.",
    ),
    TipoElemento(
        "viga_acartelada", "Viga acartelada",
        [_c("base", "Base", 0.30), _c("peralte", "Peralte central", 0.50),
         _c("peralte_apoyo", "Peralte en apoyo", 0.80),
         _c("long_cartela", "Longitud de cartela", 0.80),
         _c("longitud", "Longitud total", 6.0)],
        lambda d: d["base"] * (d["peralte"] * d["longitud"]
                               + d["long_cartela"] * max(0.0, d["peralte_apoyo"] - d["peralte"])),
        "Viga acartelada: viga recta + 2 cartelas triangulares en los apoyos.",
    ),
    TipoElemento(
        "muro_contencion", "Muro de contencion",
        [_c("ancho_zapata", "Ancho de zapata", 1.80), _c("esp_zapata", "Espesor de zapata", 0.40),
         _c("esp_muro", "Espesor de pantalla", 0.25), _c("altura_muro", "Altura de pantalla", 3.0),
         _c("longitud", "Longitud", 5.0)],
        lambda d: (d["ancho_zapata"] * d["esp_zapata"]
                   + d["esp_muro"] * d["altura_muro"]) * d["longitud"],
        "Muro de contencion (seccion L): zapata + pantalla, x longitud.",
    ),
    TipoElemento(
        "muro_estructural", "Muro estructural confinado",
        [_c("longitud", "Longitud del muro", 3.50), _c("altura", "Altura", 2.60),
         _c("espesor", "Espesor del muro", 0.15),
         _c("lado_col", "Lado de columna de confinamiento", 0.25)],
        lambda d: d["altura"] * (
            d["espesor"] * max(0.0, d["longitud"] - 2 * d["lado_col"])
            + 2 * d["lado_col"] ** 2),
        "Muro estructural con 2 columnas de confinamiento amarradas con acero.",
    ),
    TipoElemento(
        "viga_voladizo", "Viga en voladizo",
        [_c("base", "Base", 0.25), _c("peralte", "Peralte", 0.50),
         _c("longitud", "Longitud del volado", 2.00),
         _c("altura_apoyo", "Altura del apoyo", 1.20)],
        lambda d: d["base"] * d["peralte"] * d["longitud"],
        "Viga en voladizo (cantilever): base x peralte x longitud del volado.",
    ),
    TipoElemento(
        "falso_piso", "Falso piso",
        [_c("area", "Area", 30.0, sufijo=" m2", paso=1.0),
         _c("espesor", "Espesor", 0.10)],
        lambda d: d["area"] * d["espesor"],
        "Falso piso (concreto simple sobre terreno): Area x espesor (~0.10 m).",
    ),
    TipoElemento(
        "vereda", "Vereda / piso exterior",
        [_c("area", "Area", 20.0, sufijo=" m2", paso=1.0),
         _c("espesor", "Espesor", 0.10)],
        lambda d: d["area"] * d["espesor"],
        "Vereda de concreto: Area x espesor.",
    ),
    TipoElemento(
        "platea", "Platea de cimentacion",
        [_c("area", "Area", 40.0, sufijo=" m2", paso=1.0),
         _c("espesor", "Espesor", 0.30)],
        lambda d: d["area"] * d["espesor"],
        "Platea (losa) de cimentacion: Area x espesor. Doble malla sup. e inf.",
    ),
    TipoElemento(
        "solado", "Solado (concreto pobre)",
        [_c("area", "Area", 20.0, sufijo=" m2", paso=1.0),
         _c("espesor", "Espesor", 0.10)],
        lambda d: d["area"] * d["espesor"],
        "Solado de nivelacion bajo zapatas: Area x espesor. Concreto simple.",
    ),
    TipoElemento(
        "dado", "Dado / Pedestal",
        [_c("lado_a", "Lado a", 0.50), _c("lado_b", "Lado b", 0.50),
         _c("altura", "Altura", 0.80)],
        lambda d: d["lado_a"] * d["lado_b"] * d["altura"],
        "Dado o pedestal de concreto: a x b x altura.",
    ),
    TipoElemento(
        "pilote", "Pilote",
        [_c("diametro", "Diametro", 0.40), _c("longitud", "Longitud", 8.00)],
        lambda d: math.pi * (d["diametro"] / 2) ** 2 * d["longitud"],
        "Pilote (cimentacion profunda): area del circulo x longitud.",
    ),
    TipoElemento(
        "cisterna", "Cisterna / Tanque",
        [_c("largo", "Largo interior", 2.00), _c("ancho", "Ancho interior", 1.50),
         _c("altura", "Altura interior", 1.80), _c("espesor", "Espesor de muro/losa", 0.20)],
        lambda d: (
            (d["largo"] + 2 * d["espesor"]) * (d["ancho"] + 2 * d["espesor"]) * d["espesor"]
            + ((d["largo"] + 2 * d["espesor"]) * (d["ancho"] + 2 * d["espesor"]) - d["largo"] * d["ancho"]) * d["altura"]
            + (d["largo"] + 2 * d["espesor"]) * (d["ancho"] + 2 * d["espesor"]) * d["espesor"]
        ),
        "Cisterna: losa de fondo + muros + losa de techo (concreto armado).",
    ),
    TipoElemento(
        "dintel", "Dintel",
        [_c("base", "Base", 0.15), _c("peralte", "Peralte", 0.20),
         _c("longitud", "Longitud (vano + apoyos)", 1.40)],
        lambda d: d["base"] * d["peralte"] * d["longitud"],
        "Dintel sobre vano: base x peralte x longitud (vano + 0.20 m de apoyo por lado).",
    ),
    TipoElemento(
        "sardinel", "Sardinel / Bordillo",
        [_c("ancho", "Ancho", 0.15), _c("altura", "Altura", 0.30),
         _c("longitud", "Longitud", 5.00)],
        lambda d: d["ancho"] * d["altura"] * d["longitud"],
        "Sardinel o bordillo: ancho x altura x longitud. Concreto simple.",
    ),
    TipoElemento(
        "rampa", "Rampa (losa inclinada)",
        [_c("area", "Area inclinada", 15.0, sufijo=" m2", paso=1.0),
         _c("espesor", "Espesor", 0.15)],
        lambda d: d["area"] * d["espesor"],
        "Rampa de concreto (losa inclinada): Area inclinada x espesor.",
    ),
    TipoElemento(
        "viga_amarre", "Viga de amarre / solera",
        [_c("base", "Base", 0.15), _c("peralte", "Peralte", 0.20),
         _c("longitud", "Longitud", 4.00)],
        lambda d: d["base"] * d["peralte"] * d["longitud"],
        "Viga de amarre (solera/collar) de albanileria confinada: base x peralte x longitud.",
    ),
    TipoElemento(
        "personalizado", "Volumen directo (m3)",
        [_c("volumen", "Volumen", 1.0, sufijo=" m3", paso=0.1, decimales=3)],
        lambda d: d["volumen"],
        "Ingresar directamente el volumen en m3.",
    ),
]

TIPOS_POR_CLAVE = {t.clave: t for t in TIPOS}

ACERO_KG_M3 = {
    "zapata": 40,
    "columna": 100,
    "viga": 80,
    "viga_cimentacion": 60,
    "cimiento_corrido": 25,
    "sobrecimiento": 20,
    "placa": 70,
    "losa_maciza": 50,
    "losa_aligerada_1d": 30,
    "losa_aligerada_2d": 35,
    "losa_piso": 10,
    "zapata_combinada": 45,
    "columna_circular": 100,
    "columna_t": 95,
    "columna_l": 95,
    "viga_t": 75,
    "viga_acartelada": 85,
    "muro_contencion": 65,
    "muro_estructural": 50,
    "viga_voladizo": 90,
    "falso_piso": 0,
    "vereda": 5,
    "platea": 60,
    "solado": 0,
    "dado": 90,
    "pilote": 90,
    "cisterna": 80,
    "dintel": 80,
    "sardinel": 5,
    "rampa": 50,
    "viga_amarre": 75,
    "personalizado": 0,
}

PESO_VARILLA = {
    "6mm (1/4\")": {"mm": 6, "kg_m": 0.222, "largo_m": 9.0},
    "8mm (5/16\")": {"mm": 8, "kg_m": 0.395, "largo_m": 9.0},
    "3/8\"": {"mm": 9.5, "kg_m": 0.560, "largo_m": 9.0},
    "12mm (1/2\")": {"mm": 12.7, "kg_m": 0.994, "largo_m": 9.0},
    "5/8\"": {"mm": 15.9, "kg_m": 1.552, "largo_m": 9.0},
    "3/4\"": {"mm": 19.1, "kg_m": 2.235, "largo_m": 9.0},
    "1\"": {"mm": 25.4, "kg_m": 3.973, "largo_m": 9.0},
}


def encofrado_m2(clave, d):
    """Area de encofrado (contacto) por unidad, en m2."""
    g = d.get
    if clave in ("zapata", "zapata_combinada"):
        return 2 * (g("largo", 0) + g("ancho", 0)) * g("peralte", 0)
    if clave == "columna":
        return 2 * (g("lado_a", 0) + g("lado_b", 0)) * g("altura", 0)
    if clave == "columna_circular":
        return math.pi * g("diametro", 0) * g("altura", 0)
    if clave == "columna_t":
        return 2 * (g("ancho_ala", 0) + g("peralte", 0)) * g("altura", 0)
    if clave == "columna_l":
        return 2 * (g("lado1", 0) + g("lado2", 0)) * g("altura", 0)
    if clave in ("viga", "viga_cimentacion", "viga_t", "viga_acartelada",
                 "viga_voladizo", "viga_amarre", "dintel"):
        return (g("base", 0) + 2 * g("peralte", 0)) * g("longitud", 0)
    if clave in ("cimiento_corrido", "sobrecimiento"):
        return 2 * g("altura", 0) * g("longitud", 0)
    if clave in ("placa", "muro_estructural"):
        return 2 * g("altura", 0) * g("longitud", 0)
    if clave == "muro_contencion":
        return 2 * g("altura_muro", 0) * g("longitud", 0)
    if clave == "dado":
        return 2 * (g("lado_a", 0) + g("lado_b", 0)) * g("altura", 0)
    if clave in ("losa_maciza", "losa_aligerada_1d", "losa_aligerada_2d", "rampa"):
        return g("area", 0)
    if clave == "platea":
        return 4 * math.sqrt(max(0.01, g("area", 0))) * g("espesor", 0)
    if clave == "cisterna":
        e = g("espesor", 0)
        lo, wo = g("largo", 0) + 2 * e, g("ancho", 0) + 2 * e
        return (2 * (lo + wo) + 2 * (g("largo", 0) + g("ancho", 0))) * g("altura", 0)
    return 0.0


def excavacion_m3(clave, d):
    """Volumen de excavacion por unidad (geometrico), en m3. 0 si no aplica."""
    g = d.get
    if clave in ("zapata", "zapata_combinada"):
        return (g("largo", 0) + 0.30) * (g("ancho", 0) + 0.30) * g("peralte", 0)
    if clave == "cimiento_corrido":
        return (g("ancho", 0) + 0.30) * g("altura", 0) * g("longitud", 0)
    if clave == "viga_cimentacion":
        return (g("base", 0) + 0.30) * g("peralte", 0) * g("longitud", 0)
    if clave == "dado":
        return (g("lado_a", 0) + 0.30) * (g("lado_b", 0) + 0.30) * g("altura", 0)
    if clave == "pilote":
        return math.pi * (g("diametro", 0) / 2) ** 2 * g("longitud", 0)
    if clave == "platea":
        return g("area", 0) * g("espesor", 0)
    if clave == "cisterna":
        e = g("espesor", 0)
        lo, wo = g("largo", 0) + 2 * e, g("ancho", 0) + 2 * e
        return (lo + 0.30) * (wo + 0.30) * (g("altura", 0) + e)
    return 0.0


@dataclass
class ElementoMetrado:
    tipo_clave: str
    nombre: str
    descripcion: str
    cantidad: int
    volumen_unitario: float
    volumen_total: float


def calcular_elemento(tipo_clave, valores, cantidad):
    """Calcula el volumen de un elemento. `valores` es dict clave->float."""
    tipo = TIPOS_POR_CLAVE[tipo_clave]
    vol_unit = tipo.formula(valores)
    cantidad = max(1, int(cantidad))
    partes = ", ".join(
        f"{c.etiqueta} {valores[c.clave]:g}{c.sufijo}" for c in tipo.campos
    )
    return ElementoMetrado(
        tipo_clave=tipo_clave,
        nombre=tipo.nombre,
        descripcion=partes,
        cantidad=cantidad,
        volumen_unitario=round(vol_unit, 4),
        volumen_total=round(vol_unit * cantidad, 4),
    )
