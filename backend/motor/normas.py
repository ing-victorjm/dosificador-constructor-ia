"""Reglas normativas de medición, con su cita literal.

Este módulo existe por una razón concreta: la app anterior fallaba porque tenía
UN interruptor global de "descontar vanos". La norma no funciona así. Los muros
descuentan todo vano sin umbral; los pisos no descuentan huecos menores a
0,25 m². Un solo interruptor produce error garantizado en una de las dos
familias.

Cada regla trae `cita` con el texto de la norma. Cuando el motor bloquea o
avisa, muestra la cita — no un "esto está mal" que nadie puede rebatir ante una
supervisión.

Etiquetas de procedencia (`etiqueta`), porque no todo dato tiene el mismo peso:

* `NORMA`            — Norma Técnica de Metrados (R.D. 073-2010-VIVIENDA/VMCS-DNC)
* `E060`             — Reglamento Nacional de Edificaciones, norma técnica citada
* `LITERATURA`       — CAPECO y manuales de costos
* `FICHA_FABRICANTE` — catálogo de un fabricante
* `COSTUMBRE_OBRA`   — práctica extendida sin respaldo normativo
* `USUARIO`          — lo definió quien usa la app
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .redondeo import dec

NORMA = "NORMA"
E060 = "E060"
LITERATURA = "LITERATURA"
FICHA_FABRICANTE = "FICHA_FABRICANTE"
COSTUMBRE_OBRA = "COSTUMBRE_OBRA"
USUARIO = "USUARIO"

ETIQUETAS = {
    NORMA: {"nombre": "Norma de metrados", "peso": 5, "color": "#0d9463"},
    E060: {"nombre": "Norma técnica (RNE)", "peso": 5, "color": "#0d9463"},
    FICHA_FABRICANTE: {"nombre": "Ficha de fabricante", "peso": 4, "color": "#2563eb"},
    LITERATURA: {"nombre": "Literatura técnica", "peso": 3, "color": "#c07b10"},
    COSTUMBRE_OBRA: {"nombre": "Costumbre de obra", "peso": 2, "color": "#d97706"},
    USUARIO: {"nombre": "Definido por el usuario", "peso": 1, "color": "#8593ab"},
}

FUENTE_NORMA_PE = "Norma Técnica de Metrados para Obras de Edificación y Habilitaciones Urbanas — R.D. N° 073-2010-VIVIENDA/VMCS-DNC"


# --------------------------------------------------------------------------- #
# Descuento de vanos: umbral POR FAMILIA
# --------------------------------------------------------------------------- #

# Cuatro maneras distintas de tratar un vano. Un umbral numérico no basta: en
# España los revestimientos descuentan SOLO EL EXCESO sobre 4 m², y en Colombia
# la práctica de «vacío por lleno» no descuenta nada. Modelar esto como un único
# umbral produciría un metrado equivocado en dos de los cuatro casos.
DEDUCIR_TODO = "deducir_todo"
UMBRAL = "umbral"
DEDUCIR_EXCESO = "deducir_exceso"
NO_DEDUCIR = "no_deducir"

MODOS_DESCUENTO = {
    DEDUCIR_TODO: "Se descuenta todo vano, sin importar su tamaño.",
    UMBRAL: "Se descuenta el vano completo cuando alcanza el umbral.",
    DEDUCIR_EXCESO: "Se descuenta solo la parte que excede el umbral.",
    NO_DEDUCIR: "No se descuentan vanos (medición «vacío por lleno»).",
}


@dataclass(frozen=True)
class FamiliaDescuento:
    clave: str
    nombre: str
    descuenta: bool
    umbral_m2: Decimal          # umbral del modo; 0 cuando no aplica
    codigo: str
    cita: str
    etiqueta: str = NORMA
    nota: str | None = None
    modo: str = UMBRAL
    pais: str | None = None     # None = criterio general


FAMILIAS: dict[str, FamiliaDescuento] = {f.clave: f for f in [
    FamiliaDescuento(
        "muros", "Muros y tabiques de albañilería", True, dec("0"), "OE.3.1",
        "Se descontarán todos los vanos que se presenten en el muro.",
        nota="Sin umbral: se descuenta cualquier vano, por pequeño que sea.",
        modo=DEDUCIR_TODO, pais="PE",
    ),
    FamiliaDescuento(
        "revoques", "Revoques, enlucidos y molduras", True, dec("0"), "OE.3.2",
        "Se descontarán todos los vanos; los derrames se miden por separado.",
        nota="El derrame (vestidura de vanos) es partida aparte, en metro lineal.",
        modo=DEDUCIR_TODO, pais="PE",
    ),
    FamiliaDescuento(
        "pintura", "Pintura", True, dec("0"), "OE.3.11.1",
        "El área de pintura se obtiene de la superficie efectivamente revestida, "
        "descontando los vanos, igual que en los revoques.",
        nota="Hereda el criterio del tarrajeo. El número de manos multiplica el "
             "material, NUNCA el área metrada.",
        modo=DEDUCIR_TODO, pais="PE",
    ),
    FamiliaDescuento(
        "pisos", "Pisos, contrapisos y acabados de piso", True, dec("0.25"), "OE.3.4.1 / OE.3.4.2",
        "No se descontarán las áreas ocupadas por columnas, huecos, rejillas y "
        "similares menores a 0,25 m².",
        nota="El umbral se evalúa HUECO POR HUECO, no sobre la suma.",
        modo=UMBRAL, pais="PE",
    ),
    FamiliaDescuento(
        "cielorrasos", "Cielorrasos y falsos techos", True, dec("0.25"), "OE.3.3.1",
        "No se descontarán las áreas de columnas y huecos menores a 0,25 m².",
        nota="El texto publicado dice «0,25 cm²»; es errata evidente de la norma, "
             "se lee 0,25 m². Se documenta para que nadie lo corrija en silencio.",
        modo=UMBRAL, pais="PE",
    ),
    FamiliaDescuento(
        "coberturas", "Coberturas de techo (arquitectura)", True, dec("0.50"), "OE.3.6",
        "No se descontarán los vanos menores a 0,50 m².",
        modo=UMBRAL, pais="PE",
    ),
    FamiliaDescuento(
        "coberturas_estructuras", "Coberturas de estructuras", True, dec("1.00"), "OE.2",
        "Se descontarán los vanos iguales o mayores a 1,00 m².",
        modo=UMBRAL, pais="PE",
    ),
    FamiliaDescuento(
        "recubrimientos_pe", "Recubrimientos y enchapes", True, dec("0.50"), "OE.3.2",
        "No se descontarán los vanos menores a 0,50 m².",
        modo=UMBRAL, pais="PE",
    ),
    # --- Criterios de otros países ---------------------------------------
    FamiliaDescuento(
        "fabrica_es", "Fábrica de ladrillo (España)", True, dec("2.00"),
        "Criterio de medición",
        "Se deducen los huecos de superficie mayor a 2,00 m².",
        etiqueta=LITERATURA, modo=UMBRAL, pais="ES",
        nota="Criterio habitual de las bases de precios españolas (CYPE, BEDEC, PREOC).",
    ),
    FamiliaDescuento(
        "revestimientos_es", "Revestimientos (España)", True, dec("4.00"),
        "Criterio de medición",
        "Se deduce únicamente la superficie de los huecos que excede de 4,00 m².",
        etiqueta=LITERATURA, modo=DEDUCIR_EXCESO, pais="ES",
        nota="No se descuenta el hueco completo: solo su exceso sobre el umbral. "
             "Tratarlo como corte binario sobremetraría el descuento.",
    ),
    FamiliaDescuento(
        "vacio_por_lleno", "Vacío por lleno (Colombia)", False, dec("0"),
        "Criterio de medición",
        "Los vanos no se descuentan: se mide el paño completo.",
        etiqueta=COSTUMBRE_OBRA, modo=NO_DEDUCIR, pais="CO",
        nota="Práctica extendida en Colombia. Compensa el sobrecosto de ejecutar los "
             "bordes del vano; por eso el derrame tampoco se mide aparte.",
    ),
    FamiliaDescuento(
        "albanileria_nrm2", "Albañilería (RICS NRM2)", True, dec("0.50"), "NRM2",
        "Se deducen los huecos mayores a 0,50 m².",
        etiqueta=LITERATURA, modo=UMBRAL, pais="INT",
    ),
    FamiliaDescuento(
        "encofrado_nrm2", "Encofrado (RICS NRM2)", True, dec("5.00"), "NRM2",
        "Se deducen los huecos mayores a 5,00 m².",
        etiqueta=LITERATURA, modo=UMBRAL, pais="INT",
    ),
    FamiliaDescuento(
        "sin_descuento", "Sin descuento de vanos", False, dec("0"), "—",
        "La partida se mide bruta; no corresponde descuento de vanos.",
        etiqueta=USUARIO, modo=NO_DEDUCIR,
    ),
]}

# Aviso permanente: el umbral de 2,00 m² es costumbre, no norma.
UMBRAL_MITO = {
    "valor": "2.00",
    "aviso": "El umbral de 2,00 m² para descontar vanos NO figura en la Norma Técnica "
             "de Metrados. Es costumbre de obra. Si lo usa, quedará registrado como "
             "criterio del usuario, no como norma.",
    "etiqueta": COSTUMBRE_OBRA,
}


def descontar_vano(area_vano, familia: str) -> tuple[bool, str, Decimal]:
    """¿Se descuenta este vano y cuánto?

    Devuelve (aplica, motivo citable, área a descontar). El tercer valor importa:
    en el modo «deducir_exceso» no se descuenta el vano completo, sino solo la
    parte que supera el umbral.
    """
    f = FAMILIAS.get(familia or "sin_descuento", FAMILIAS["sin_descuento"])
    area = dec(area_vano)

    if f.modo == NO_DEDUCIR or not f.descuenta:
        return False, f"{f.nombre}: {f.cita}", Decimal(0)

    if f.modo == DEDUCIR_TODO:
        return True, f"{f.codigo} — {f.cita}", area

    if f.modo == DEDUCIR_EXCESO:
        exceso = area - f.umbral_m2
        if exceso <= 0:
            return False, (f"{f.codigo} — no se descuenta: {area} m² no supera los "
                           f"{f.umbral_m2} m². «{f.cita}»"), Decimal(0)
        return True, (f"{f.codigo} — se descuenta solo el exceso: {area} − {f.umbral_m2} "
                      f"= {exceso} m². «{f.cita}»"), exceso

    if area >= f.umbral_m2:
        return True, f"{f.codigo} — se descuenta: {area} m² ≥ {f.umbral_m2} m².", area
    return (False,
            f"{f.codigo} — no se descuenta: {area} m² < {f.umbral_m2} m². «{f.cita}»",
            Decimal(0))


# --------------------------------------------------------------------------- #
# Desperdicio: fuera del metrado
# --------------------------------------------------------------------------- #

REGLA_DESPERDICIO = {
    "codigo": "OE.2.3 / OE.2.3.9.2",
    "cita": "El cómputo del acero será la suma de las longitudes de las varillas, "
            "sin considerar desperdicios.",
    "etiqueta": NORMA,
    "explicacion": (
        "El desperdicio NO forma parte del metrado: se aplica en el análisis de "
        "precios unitarios. Incluirlo en la partida lo cobra dos veces. METRA AI "
        "muestra siempre dos cifras separadas: «metrado neto» (lo que va al "
        "presupuesto) y «cantidad a comprar» (metrado + desperdicio, referencial)."
    ),
    "advertencia_cita": (
        "La frase general «el cómputo será neto… ni desperdicios» está en el Título III "
        "(Habilitaciones Urbanas), no en OE. Ante una supervisión de edificación, cite "
        "OE.2.3 para acero y OE.2.3.9.2 para ladrillos de techo."
    ),
}

DESPERDICIOS_REFERENCIALES = [
    {"material": "Acero de refuerzo", "pct": "5", "etiqueta": LITERATURA},
    {"material": "Ladrillo de arcilla", "pct": "5", "etiqueta": LITERATURA},
    {"material": "Ladrillo de techo", "pct": "5", "etiqueta": LITERATURA},
    {"material": "Cerámico y porcelanato", "pct": "7", "etiqueta": LITERATURA},
    {"material": "Concreto premezclado", "pct": "3", "etiqueta": LITERATURA},
    {"material": "Concreto hecho en obra", "pct": "5", "etiqueta": LITERATURA},
    {"material": "Mortero", "pct": "10", "etiqueta": LITERATURA},
    {"material": "Tubería PVC", "pct": "5", "etiqueta": COSTUMBRE_OBRA},
    {"material": "Cable eléctrico", "pct": "5", "etiqueta": COSTUMBRE_OBRA},
]


# --------------------------------------------------------------------------- #
# Esponjamiento: solo en eliminación
# --------------------------------------------------------------------------- #

REGLA_ESPONJAMIENTO = {
    "codigo": "OE.2.1.6",
    "cita": "El volumen de material excedente se obtiene afectando el volumen de "
            "material a eliminar por el factor de esponjamiento correspondiente.",
    "etiqueta": NORMA,
    "explicacion": (
        "El esponjamiento entra SOLO en la eliminación de material excedente. "
        "Nunca en la excavación ni en el corte: esos se miden en su volumen "
        "natural (banco)."
    ),
    "contradiccion": (
        "La propia norma se contradice entre regímenes: OE.2.1.6 pone el "
        "esponjamiento en el metrado, mientras que HU.3.4 (habilitaciones urbanas) "
        "lo pone en el análisis de precios. Por eso el proyecto declara su régimen "
        "y METRA AI aplica el criterio correspondiente."
    ),
    "regimenes": {
        "OE": "Edificación: el esponjamiento se aplica en el metrado de eliminación.",
        "HU": "Habilitación urbana: el esponjamiento se aplica en el APU, el metrado va en banco.",
    },
}


# --------------------------------------------------------------------------- #
# Acero: arranques
# --------------------------------------------------------------------------- #

REGLA_ARRANQUES = {
    "codigo": "OE.2.3",
    "etiqueta": NORMA,
    "excluyen": ["cimiento_reforzado", "zapata", "viga_cimentacion", "losa_cimentacion",
                 "platea", "sobrecimiento_reforzado"],
    "incluyen": ["columna", "placa", "viga", "losa_maciza", "losa_aligerada",
                 "muro_contencion", "escalera", "cisterna"],
    "explicacion": (
        "El acero de arranque (vástago) NO se computa en el elemento de cimentación: "
        "se computa en el elemento vertical que arranca. En columnas, placas, vigas, "
        "losas, muros de contención, escaleras y cisternas sí se incluye la longitud "
        "empotrada. Ningún ratio kg/m³ puede reproducir esta frontera."
    ),
}

REGLA_KG_M3 = {
    "etiqueta": COSTUMBRE_OBRA,
    "aviso": (
        "«kg/m³» no aparece ni una vez en la Norma Técnica de Metrados. Un ratio de "
        "acero por metro cúbico es una ESTIMACIÓN PRELIMINAR para contrastar, jamás "
        "un metrado. METRA AI no permite que un valor estimado por ratio entre al "
        "presupuesto ni a la exportación."
    ),
    "rangos_control": [
        {"elemento": "Zapatas", "min": "40", "max": "70"},
        {"elemento": "Columnas", "min": "100", "max": "350"},
        {"elemento": "Vigas", "min": "100", "max": "250"},
        {"elemento": "Losa aligerada", "min": "80", "max": "175"},
        {"elemento": "Losa maciza", "min": "50", "max": "200"},
    ],
    "fuente": "Rangos de control de uso extendido en foros y manuales de obra. "
              "Solo para semáforo de verificación posterior al despiece.",
}


# --------------------------------------------------------------------------- #
# Tuberías: descuento de accesorios según régimen
# --------------------------------------------------------------------------- #

REGLA_ACCESORIOS = {
    "OE": {
        "descuenta": False,
        "codigo": "OE.4",
        "cita": "La longitud de la tubería se mide sin descontar la longitud de los "
                "accesorios, válvulas y piezas especiales.",
        "etiqueta": NORMA,
    },
    "HU": {
        "descuenta": True,
        "codigo": "HU.3 / HU.6",
        "cita": "Se descontará la longitud ocupada por accesorios y válvulas.",
        "etiqueta": NORMA,
    },
}


# --------------------------------------------------------------------------- #
# Erratas conocidas de la norma
# --------------------------------------------------------------------------- #

ERRATAS = [
    {"codigo": "OE.2.1.2.1", "detalle": "Aparece duplicado (excavaciones masivas y simples). "
                                        "No existe un OE.2.1.2.2."},
    {"codigo": "OE.2.1.7.1", "detalle": "Código duplicado."},
    {"codigo": "OE.3.2.22", "detalle": "Duplicado; corre la numeración del capítulo de enchapes."},
    {"codigo": "OE.3.3.1", "detalle": "Dice «0,25 cm²» donde corresponde 0,25 m²."},
    {"codigo": "OE.3.5.2", "detalle": "Dice «Se medirá el la longitud»."},
    {"codigo": "OE.3.11", "detalle": "Dice «Metro (m2)» en pintura de estructuras metálicas."},
]

CRITERIO_ERRATAS = (
    "Se usan los códigos del ÍNDICE de la norma. Donde el código sea dudoso o esté "
    "duplicado, la partida se emite por su NOMBRE LITERAL sin código, y se deja "
    "constancia de la errata. Nunca se corrige la norma en silencio."
)


# --------------------------------------------------------------------------- #
# Antipatrones detectados en la app anterior (guardarraíles del producto)
# --------------------------------------------------------------------------- #

GUARDARRAILES = [
    "Un solo interruptor global de descuento de vanos.",
    "Desperdicio dentro del metrado.",
    "Ratios kg/m³ presentados como metrado de acero.",
    "Unidades que contradicen la norma (falso piso o vereda en m³, sardinel en m³).",
    "Cantidades fabricadas con factores sin fuente (ml = puntos × 4,5).",
    "Resultados en pantalla que no producen una fila exportable con su sustento.",
    "Códigos de partida inventados.",
    "Obligar a iniciar sesión antes de poder metrar.",
]


def familia_por_defecto(especialidad: str, descripcion: str) -> str:
    """Deduce la familia de descuento a partir del texto de la partida."""
    t = (descripcion or "").lower()
    if any(p in t for p in ("muro", "tabique", "albañileria", "albañilería", "ladrillo")):
        return "muros"
    if any(p in t for p in ("tarrajeo", "revoque", "enlucido", "empaste", "solaqueo")):
        return "revoques"
    if "pintura" in t or "pintado" in t:
        return "pintura"
    if any(p in t for p in ("cielorraso", "falso techo", "cielo raso")):
        return "cielorrasos"
    if "cobertura" in t or "techo" in t:
        return "coberturas_estructuras" if "corrugad" in t else "coberturas"
    if any(p in t for p in ("piso", "contrapiso", "falso piso", "vereda", "pavimento", "loseta")):
        return "pisos"
    return "sin_descuento"


def catalogo_reglas() -> dict:
    """Todo lo citable, para que la interfaz lo muestre junto a cada partida."""
    return {
        "fuente": FUENTE_NORMA_PE,
        "familias": [
            {"clave": f.clave, "nombre": f.nombre, "descuenta": f.descuenta,
             "umbral_m2": str(f.umbral_m2), "codigo": f.codigo, "cita": f.cita,
             "etiqueta": f.etiqueta, "nota": f.nota, "modo": f.modo,
             "modo_explicacion": MODOS_DESCUENTO[f.modo], "pais": f.pais}
            for f in FAMILIAS.values()
        ],
        "modos_descuento": MODOS_DESCUENTO,
        "umbral_mito": UMBRAL_MITO,
        "desperdicio": REGLA_DESPERDICIO,
        "desperdicios_referenciales": DESPERDICIOS_REFERENCIALES,
        "esponjamiento": REGLA_ESPONJAMIENTO,
        "arranques": REGLA_ARRANQUES,
        "kg_m3": REGLA_KG_M3,
        "accesorios": REGLA_ACCESORIOS,
        "erratas": ERRATAS,
        "criterio_erratas": CRITERIO_ERRATAS,
        "guardarrailes": GUARDARRAILES,
        "etiquetas": ETIQUETAS,
    }
