"""Motor de metrado: convierte filas de sustento en cantidades auditables.

La unidad de trabajo NO es un número: es una **fila de sustento** con la forma
de la planilla de todo expediente técnico:

    ITEM | PARTIDA | CANTIDAD | N° VECES | LARGO | ANCHO | ALTO | PARCIAL | UND

Dos reglas que la app anterior rompía y que aquí son ley:

1. **Un campo vacío se OMITE del producto; no vale cero.** Si una partida de
   área solo tiene largo y ancho, el parcial es largo × ancho — no
   largo × ancho × 0.
2. **Análisis dimensional con bloqueo.** Si la unidad declarada es m² y las
   dimensiones llenas producen un volumen, no se guarda. Es un error
   documentado por Contraloría en expedientes reales.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from . import formulas, normas
from .redondeo import ReglasRedondeo, dec, redondear
from .unidades import ErrorUnidad, dimension as dim_de_unidad

COLUMNAS_PLANILLA = ("n", "veces", "largo", "ancho", "alto")
COLUMNAS_GEOMETRICAS = ("largo", "ancho", "alto")

DIMENSION_POR_CONTEO = {0: "conteo", 1: "longitud", 2: "area", 3: "volumen"}

ETIQUETA_COLUMNA = {
    "n": "Cantidad", "veces": "N° de veces", "largo": "Largo",
    "ancho": "Ancho", "alto": "Alto",
}


@dataclass
class Fila:
    """Resultado del cálculo de UNA fila de metrado, con todo su sustento."""
    id: str | None = None
    parcial: Decimal | None = None
    signo: int = 1
    sustento: str = ""
    pasos: list[str] = field(default_factory=list)
    dimension: str | None = None
    unidad: str | None = None
    faltantes: list[str] = field(default_factory=list)
    error: str | None = None
    aviso: str | None = None
    origen: str = "ingresado"
    metodo: str = "planilla"          # planilla | formula | manual

    @property
    def incompleto(self) -> bool:
        return self.parcial is None

    def a_dict(self) -> dict:
        return {
            "id": self.id,
            "parcial": None if self.parcial is None else str(self.parcial),
            "signo": self.signo,
            "sustento": self.sustento,
            "pasos": self.pasos,
            "dimension": self.dimension,
            "unidad": self.unidad,
            "faltantes": self.faltantes,
            "error": self.error,
            "aviso": self.aviso,
            "origen": self.origen,
            "metodo": self.metodo,
            "incompleto": self.incompleto,
        }


def _valor(datos: dict, clave: str) -> Decimal | None:
    """Devuelve el valor de una columna, o None si está VACÍA.

    Distingue vacío de cero: `""` y `None` son «no aplica» (se omite del
    producto); `"0"` es un cero declarado por el usuario (y hace cero el parcial,
    que es lo correcto: si escribió 0, el parcial es 0).
    """
    v = datos.get(clave)
    if v is None:
        return None
    if isinstance(v, str) and not v.strip():
        return None
    try:
        return dec(v)
    except ValueError:
        return None


def columnas_llenas(datos: dict) -> list[str]:
    return [c for c in COLUMNAS_PLANILLA if _valor(datos, c) is not None]


def dimension_inferida(datos: dict) -> str:
    """Dimensión que producen las columnas geométricas llenas."""
    llenas = [c for c in COLUMNAS_GEOMETRICAS if _valor(datos, c) is not None]
    return DIMENSION_POR_CONTEO[len(llenas)]


def verificar_dimension(unidad: str | None, datos: dict, hay_formula: bool) -> tuple[str, str | None]:
    """Contrasta la unidad declarada con lo que produce la fila.

    Devuelve ("ok" | "aviso" | "error", mensaje).
    """
    if not unidad:
        return "aviso", "La partida no tiene unidad de medida declarada."
    try:
        esperada = dim_de_unidad(unidad)
    except ErrorUnidad as exc:
        return "error", str(exc)

    if hay_formula:
        # Con fórmula libre no se puede inferir la dimensión del resultado sin
        # conocer las unidades de cada variable: se confía en el autor.
        return "ok", None

    producida = dimension_inferida(datos)
    if esperada in ("global", "adimensional", "tiempo"):
        return "ok", None
    if esperada == "masa":
        if producida in ("longitud", "conteo"):
            return "aviso", (
                "La partida se mide en kilogramos: hace falta una fórmula con el peso "
                "unitario (por ejemplo n × longitud × peso_unitario). Las columnas de la "
                "planilla por sí solas no producen masa."
            )
        return "aviso", "Verifique cómo se obtiene el peso: la planilla no produce kilogramos."

    grados = {"conteo": 0, "longitud": 1, "area": 2, "volumen": 3}
    if producida == esperada:
        return "ok", None

    llenas = ", ".join(ETIQUETA_COLUMNA[c] for c in COLUMNAS_GEOMETRICAS
                       if _valor(datos, c) is not None) or "ninguna"

    if grados[producida] > grados[esperada]:
        # Multiplicar de más: la unidad dice m² y la fila entrega un volumen.
        # Este es el error que documenta Contraloría; se bloquea.
        return "error", (
            f"Incompatibilidad dimensional: la unidad «{unidad}» es de {esperada}, pero las "
            f"columnas llenas ({llenas}) producen {producida}. "
            "Corrija la unidad o quite la dimensión que sobra."
        )

    # Menos dimensiones de las esperadas: normalmente el metrador escribió un
    # valor ya calculado (un área tomada del plano). Es legítimo; se avisa para
    # que quede constancia de que ese número no se descompone en la planilla.
    return "aviso", (
        f"La partida se mide en {unidad} y solo llenó {llenas}. Se entiende que ese valor "
        "ya viene calculado; anote en la fila de dónde sale, porque la planilla no lo "
        "descompone."
    )


def _texto(d: Decimal) -> str:
    return format(d.normalize(), "f")


def calcular_fila(datos: dict, unidad: str | None = None,
                  reglas: ReglasRedondeo | None = None) -> Fila:
    """Calcula el parcial de una fila con su sustento textual."""
    reglas = reglas or ReglasRedondeo()
    signo = -1 if int(datos.get("signo") or 1) < 0 else 1
    fila = Fila(id=datos.get("id"), signo=signo, unidad=unidad,
                origen=datos.get("origen") or "ingresado")

    expresion = (datos.get("formula") or "").strip()
    hay_formula = bool(expresion)
    estado_dim, mensaje_dim = verificar_dimension(unidad, datos, hay_formula)
    if estado_dim == "error":
        fila.error = mensaje_dim
        fila.dimension = dimension_inferida(datos)
        return fila
    if estado_dim == "aviso":
        fila.aviso = mensaje_dim

    if hay_formula:
        fila.metodo = "formula"
        variables: dict[str, Any] = {}
        for c in COLUMNAS_PLANILLA:
            v = _valor(datos, c)
            if v is not None:
                variables[c] = v
        variables.update(datos.get("variables") or {})
        r = formulas.evaluar(expresion, variables)
        fila.faltantes = r.faltantes
        fila.pasos = r.pasos
        fila.sustento = r.sustituida
        if r.valor is None:
            fila.error = r.error
            return fila
        bruto = r.valor
    else:
        llenas = columnas_llenas(datos)
        if not llenas:
            fila.error = "La fila está vacía: escriba al menos una cantidad o dimensión."
            return fila
        bruto = Decimal(1)
        partes: list[str] = []
        for c in llenas:
            v = _valor(datos, c)
            bruto *= v
            partes.append(_texto(v))
        fila.sustento = " × ".join(partes)
        fila.pasos = [f"{ETIQUETA_COLUMNA[c]} = {_texto(_valor(datos, c))}" for c in llenas]
        fila.pasos.append(f"{fila.sustento} = {_texto(bruto)}")

    fila.dimension = dimension_inferida(datos) if not hay_formula else None
    fila.parcial = reglas.metrado(bruto) * signo
    if signo < 0:
        fila.sustento = f"− ({fila.sustento})"
    return fila


# --------------------------------------------------------------------------- #
# Totales de partida
# --------------------------------------------------------------------------- #

@dataclass
class TotalPartida:
    total: Decimal
    unidad: str | None
    filas_ok: int = 0
    filas_incompletas: int = 0
    filas_con_error: int = 0
    deducciones: Decimal = Decimal(0)
    bruto: Decimal = Decimal(0)
    desperdicio_pct: Decimal = Decimal(0)
    cantidad_a_comprar: Decimal | None = None
    origen: str = "mediciones"        # mediciones | manual | vacio
    avisos: list[str] = field(default_factory=list)

    def a_dict(self) -> dict:
        return {
            "total": str(self.total),
            "unidad": self.unidad,
            "filas_ok": self.filas_ok,
            "filas_incompletas": self.filas_incompletas,
            "filas_con_error": self.filas_con_error,
            "deducciones": str(self.deducciones),
            "bruto": str(self.bruto),
            "desperdicio_pct": str(self.desperdicio_pct),
            "cantidad_a_comprar": None if self.cantidad_a_comprar is None else str(self.cantidad_a_comprar),
            "origen": self.origen,
            "avisos": self.avisos,
        }


def total_partida(filas: list[Fila], unidad: str | None, desperdicio_pct: Any = 0,
                  cantidad_manual: Any = None,
                  reglas: ReglasRedondeo | None = None) -> TotalPartida:
    """Suma los parciales YA redondeados.

    Se suman los parciales redondeados, no los valores crudos, para que la
    planilla impresa cuadre línea a línea. Es la convención de expediente: el
    revisor suma con calculadora lo que ve en el papel.
    """
    reglas = reglas or ReglasRedondeo()
    t = TotalPartida(total=Decimal(0), unidad=unidad)
    suma = Decimal(0)
    for f in filas:
        # Faltar un dato no es un error del usuario: es una fila incompleta que
        # hay que terminar. Se cuentan aparte porque se resuelven distinto.
        if f.faltantes:
            t.filas_incompletas += 1
            continue
        if f.error:
            t.filas_con_error += 1
            continue
        if f.parcial is None:
            t.filas_incompletas += 1
            continue
        t.filas_ok += 1
        suma += f.parcial
        if f.parcial < 0:
            t.deducciones += f.parcial
        else:
            t.bruto += f.parcial

    if t.filas_ok == 0:
        if cantidad_manual not in (None, ""):
            t.total = reglas.metrado(cantidad_manual)
            t.origen = "manual"
            t.avisos.append(
                "Cantidad ingresada a mano: no tiene filas de sustento. Un expediente "
                "técnico exige el sustento del metrado."
            )
        else:
            t.origen = "vacio"
    else:
        t.total = reglas.metrado(suma)
        if cantidad_manual not in (None, ""):
            t.avisos.append(
                "Hay una cantidad manual y además filas de sustento. Se usa la suma de "
                "las filas; la cantidad manual queda ignorada."
            )

    if t.filas_incompletas:
        t.avisos.append(
            f"{t.filas_incompletas} fila(s) sin calcular por datos faltantes. "
            "El total mostrado está incompleto — no se inventan valores."
        )
    if t.filas_con_error:
        t.avisos.append(f"{t.filas_con_error} fila(s) con error de cálculo.")

    # El desperdicio NUNCA entra al metrado. Se publica aparte.
    t.desperdicio_pct = dec(desperdicio_pct or 0)
    if t.desperdicio_pct > 0:
        t.cantidad_a_comprar = reglas.metrado(t.total * (Decimal(1) + t.desperdicio_pct / Decimal(100)))
        t.avisos.append(
            f"Desperdicio {t.desperdicio_pct}% aplicado SOLO a la cantidad a comprar "
            f"({t.cantidad_a_comprar} {unidad or ''}). El metrado de la partida es {t.total}. "
            + normas.REGLA_DESPERDICIO["explicacion"]
        )
    return t


# --------------------------------------------------------------------------- #
# Deducción de vanos según familia normativa
# --------------------------------------------------------------------------- #

def filas_deduccion_vanos(vanos: list[dict], familia: str,
                          reglas: ReglasRedondeo | None = None) -> list[dict]:
    """Genera las filas negativas de descuento de vanos que correspondan.

    `vanos`: [{"descripcion":"Puerta P-1","n":2,"ancho":"0.90","alto":"2.10"}]
    Devuelve filas listas para insertar, cada una con el motivo citable. Los
    vanos que NO se descuentan se devuelven igual, con `aplica=False` y la
    leyenda — porque el revisor busca justamente esa leyenda.
    """
    reglas = reglas or ReglasRedondeo()
    salida = []
    for v in vanos:
        ancho = _valor(v, "ancho")
        alto = _valor(v, "alto")
        n = _valor(v, "n") or Decimal(1)
        if ancho is None or alto is None:
            salida.append({**v, "aplica": False,
                           "motivo": "Faltan las dimensiones del vano; no se puede evaluar el umbral."})
            continue
        area_unitaria = ancho * alto
        aplica, motivo, area_descontable = normas.descontar_vano(area_unitaria, familia)
        fila = {
            "descripcion": v.get("descripcion") or "Vano",
            "n": str(n), "ancho": str(ancho), "alto": str(alto),
            "area_unitaria": str(reglas.metrado(area_unitaria)),
            "area_descontable": str(reglas.metrado(area_descontable)),
            "signo": -1 if aplica else 1,
            "aplica": aplica,
            "motivo": motivo,
            "familia": familia,
            "modo": normas.FAMILIAS[familia].modo if familia in normas.FAMILIAS else None,
        }
        # En el modo «deducir_exceso» no se descuenta ancho × alto: se descuenta
        # solo la superficie que supera el umbral. La fila resultante lleva esa
        # área ya calculada, no las dimensiones del vano.
        if aplica and area_descontable != area_unitaria:
            fila["ancho"] = str(reglas.metrado(area_descontable))
            fila["alto"] = None
            fila["descripcion"] += f" (exceso sobre el umbral)"
        salida.append(fila)
    return salida


# --------------------------------------------------------------------------- #
# Cálculo de un item completo (partida + sus mediciones)
# --------------------------------------------------------------------------- #

def calcular_item(item: dict, mediciones: list[dict],
                  reglas: ReglasRedondeo | None = None) -> dict:
    """Calcula una partida completa. Entrada y salida son dicts serializables."""
    reglas = reglas or ReglasRedondeo()
    unidad = item.get("unidad")
    filas = [calcular_fila(m, unidad, reglas) for m in mediciones]
    total = total_partida(
        filas, unidad,
        desperdicio_pct=item.get("desperdicio_pct"),
        cantidad_manual=item.get("cantidad_manual"),
        reglas=reglas,
    )
    return {
        "item_id": item.get("id"),
        "filas": [f.a_dict() for f in filas],
        "resumen": total.a_dict(),
    }
