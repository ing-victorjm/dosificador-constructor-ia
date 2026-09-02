"""Motor de fórmulas: evaluación segura, exacta y AUDITABLE.

Tres reglas que no se negocian:

1. **Seguro**: se evalúa un AST con lista blanca de nodos. Nunca `eval()` libre.
   Una fórmula guardada en la base de datos es dato del usuario, no código.
2. **Exacto**: aritmética en `Decimal`. Un metrado no puede depender del error
   binario de coma flotante.
3. **Auditable**: cada evaluación devuelve la expresión con los valores
   sustituidos y el paso a paso. Si una variable falta, el resultado es
   `incompleto` — NUNCA se asume cero. Inventar un cero es inventar un metrado.
"""
from __future__ import annotations

import ast
import math
import re
from dataclasses import dataclass, field
from decimal import Decimal, DivisionByZero, InvalidOperation
from typing import Any

from .redondeo import dec

MAX_LONGITUD_EXPRESION = 2000
MAX_NODOS = 400


class ErrorFormula(ValueError):
    """Fórmula inválida: sintaxis, función no permitida o división por cero."""


@dataclass
class Resultado:
    valor: Decimal | None
    expresion: str
    sustituida: str                      # "3 * 4.20 * 0.15" — lo que se calculó
    variables: dict[str, Decimal] = field(default_factory=dict)
    faltantes: list[str] = field(default_factory=list)
    pasos: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def incompleto(self) -> bool:
        return self.valor is None

    def a_dict(self) -> dict:
        return {
            "valor": None if self.valor is None else str(self.valor),
            "expresion": self.expresion,
            "sustituida": self.sustituida,
            "variables": {k: str(v) for k, v in self.variables.items()},
            "faltantes": self.faltantes,
            "pasos": self.pasos,
            "error": self.error,
            "incompleto": self.incompleto,
        }


# --- Funciones permitidas -----------------------------------------------------
# Cada una recibe y devuelve Decimal. Las trigonométricas trabajan en GRADOS,
# porque en obra los taludes y pendientes se dan en grados, no en radianes.

def _raiz(x: Decimal) -> Decimal:
    if x < 0:
        raise ErrorFormula("raiz() de un número negativo")
    return x.sqrt()


def _redondear(x: Decimal, n: Decimal = Decimal(2)) -> Decimal:
    return x.quantize(Decimal(1).scaleb(-int(n)))


def _grados(fn):
    return lambda x: dec(repr(fn(math.radians(float(x)))))


FUNCIONES: dict[str, Any] = {
    "abs": abs,
    "min": min,
    "max": max,
    "raiz": _raiz,
    "sqrt": _raiz,
    "redondear": _redondear,
    "round": _redondear,
    "techo": lambda x: dec(math.ceil(x)),
    "ceil": lambda x: dec(math.ceil(x)),
    "piso": lambda x: dec(math.floor(x)),
    "floor": lambda x: dec(math.floor(x)),
    "seno": _grados(math.sin),
    "coseno": _grados(math.cos),
    "tangente": _grados(math.tan),
    "sen": _grados(math.sin),
    "cos": _grados(math.cos),
    "tan": _grados(math.tan),
    "si": lambda cond, a, b: a if cond != 0 else b,   # si(condicion; valor_si; valor_no)
}

CONSTANTES: dict[str, Decimal] = {
    "PI": dec("3.14159265358979323846"),
    "pi": dec("3.14159265358979323846"),
}

_NODOS_PERMITIDOS = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Call,
    ast.Load, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
    ast.USub, ast.UAdd, ast.Compare, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Eq, ast.NotEq, ast.Tuple,
)

_RE_VARIABLE = re.compile(r"\b([A-Za-zÁÉÍÓÚÜÑáéíóúüñ_][A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ_]*)\b")


def normalizar(expresion: str) -> str:
    """Acepta la escritura de obra: 'x' por multiplicar, ',' decimal, ';' de argumentos.

    Convierte `3 x 4,20 x 0,15` en `3 * 4.20 * 0.15`. La coma decimal solo se
    traduce cuando está entre dígitos, para no romper `min(a, b)`.
    """
    if expresion is None:
        return ""
    e = str(expresion).strip()
    e = e.replace("×", "*").replace("·", "*").replace("−", "-").replace("÷", "/")
    e = e.replace("^", "**").replace("[", "(").replace("]", ")")
    # 'x' como signo de multiplicar. Se exige espacio a ambos lados (o dígitos
    # pegados) para no destrozar nombres de función como max( o variables con x.
    e = re.sub(r"(?<=[\w\)])\s+[xX]\s+(?=[\w\(])", " * ", e)         # n x largo -> n * largo
    e = re.sub(r"(?<=\d)\s*[xX]\s*(?=[\d\(])", " * ", e)             # 3x4 -> 3 * 4
    e = re.sub(r"(?<=\d),(?=\d)", ".", e)                            # 4,20 -> 4.20
    e = e.replace(";", ",")                                          # si(a; b; c)
    return e


def variables_de(expresion: str) -> list[str]:
    """Nombres de variable que aparecen en la fórmula (sin funciones ni constantes)."""
    e = normalizar(expresion)
    nombres: list[str] = []
    for m in _RE_VARIABLE.finditer(e):
        nombre = m.group(1)
        siguiente = e[m.end():].lstrip()
        if siguiente.startswith("("):
            continue                       # es una llamada a función
        if nombre in FUNCIONES or nombre in CONSTANTES:
            continue
        if nombre not in nombres:
            nombres.append(nombre)
    return nombres


def _num(nodo: ast.AST, valores: dict[str, Decimal]) -> Decimal:
    if isinstance(nodo, ast.Constant):
        if isinstance(nodo.value, bool) or not isinstance(nodo.value, (int, float)):
            raise ErrorFormula(f"Valor no numérico en la fórmula: {nodo.value!r}")
        return dec(nodo.value)

    if isinstance(nodo, ast.Name):
        if nodo.id in valores:
            return valores[nodo.id]
        if nodo.id in CONSTANTES:
            return CONSTANTES[nodo.id]
        raise KeyError(nodo.id)

    if isinstance(nodo, ast.UnaryOp):
        v = _num(nodo.operand, valores)
        return -v if isinstance(nodo.op, ast.USub) else +v

    if isinstance(nodo, ast.BinOp):
        a, b = _num(nodo.left, valores), _num(nodo.right, valores)
        op = nodo.op
        if isinstance(op, ast.Add):
            return a + b
        if isinstance(op, ast.Sub):
            return a - b
        if isinstance(op, ast.Mult):
            return a * b
        if isinstance(op, ast.Div):
            if b == 0:
                raise ErrorFormula("División entre cero.")
            return a / b
        if isinstance(op, ast.Mod):
            if b == 0:
                raise ErrorFormula("Módulo entre cero.")
            return a % b
        if isinstance(op, ast.Pow):
            if abs(b) > 100:
                raise ErrorFormula("Exponente fuera de rango.")
            try:
                return a ** b
            except (InvalidOperation, OverflowError) as exc:
                raise ErrorFormula(f"Potencia inválida: {a}**{b}") from exc
        raise ErrorFormula(f"Operador no permitido: {type(op).__name__}")

    if isinstance(nodo, ast.Compare):
        if len(nodo.ops) != 1:
            raise ErrorFormula("Solo se permite una comparación por expresión.")
        a, b = _num(nodo.left, valores), _num(nodo.comparators[0], valores)
        op = nodo.ops[0]
        r = {ast.Lt: a < b, ast.LtE: a <= b, ast.Gt: a > b,
             ast.GtE: a >= b, ast.Eq: a == b, ast.NotEq: a != b}[type(op)]
        return Decimal(1) if r else Decimal(0)

    if isinstance(nodo, ast.Call):
        if not isinstance(nodo.func, ast.Name):
            raise ErrorFormula("Llamada no permitida.")
        nombre = nodo.func.id
        if nombre not in FUNCIONES:
            raise ErrorFormula(
                f"Función no permitida: {nombre}(). Disponibles: {', '.join(sorted(FUNCIONES))}"
            )
        if nodo.keywords:
            raise ErrorFormula("Las funciones no aceptan argumentos con nombre.")
        args = [_num(a, valores) for a in nodo.args]
        try:
            return dec(FUNCIONES[nombre](*args))
        except ErrorFormula:
            raise
        except TypeError as exc:
            raise ErrorFormula(f"Argumentos incorrectos en {nombre}(): {exc}") from exc
        except (InvalidOperation, DivisionByZero, ValueError, OverflowError) as exc:
            raise ErrorFormula(f"Error en {nombre}(): {exc}") from exc

    raise ErrorFormula(f"Elemento no permitido en la fórmula: {type(nodo).__name__}")


def _sustituir(expresion: str, valores: dict[str, Decimal]) -> str:
    """Reescribe la fórmula con los números puestos, para mostrar la trazabilidad."""
    def reemplazo(m: re.Match) -> str:
        nombre = m.group(1)
        resto = expresion[m.end():].lstrip()
        if resto.startswith("(") or nombre in FUNCIONES:
            return nombre
        if nombre in valores:
            return _limpio(valores[nombre])
        if nombre in CONSTANTES:
            return _limpio(CONSTANTES[nombre])
        return nombre
    return _RE_VARIABLE.sub(reemplazo, expresion)


def _limpio(d: Decimal) -> str:
    """Decimal sin ceros de relleno ni notación científica."""
    s = format(d.normalize(), "f")
    return s


def evaluar(expresion: str, variables: dict[str, Any] | None = None) -> Resultado:
    """Evalúa una fórmula y devuelve el resultado CON su trazabilidad.

    Si falta una variable no lanza error: devuelve `valor=None` y la lista de
    `faltantes`, para que la interfaz pida el dato en lugar de inventarlo.
    """
    original = "" if expresion is None else str(expresion)
    if len(original) > MAX_LONGITUD_EXPRESION:
        return Resultado(None, original, "", error="La fórmula es demasiado larga.")

    e = normalizar(original)
    if not e:
        return Resultado(None, original, "", error="Fórmula vacía.")

    # Una fila puede traer datos que NO son variables de la fórmula: el diámetro
    # de la barra ('5/8"'), la marca, el tipo de doblez. Esos acompañan al
    # cálculo como información y no deben romperlo; solo se exige que sea
    # numérico lo que la fórmula realmente usa.
    requeridas_todas = set(variables_de(e))
    valores: dict[str, Decimal] = {}
    no_numericas: dict[str, Any] = {}
    for k, v in (variables or {}).items():
        if v is None or v == "":
            continue
        try:
            valores[str(k)] = dec(v)
        except ValueError:
            if str(k) in requeridas_todas:
                return Resultado(None, original, "",
                                 error=f"El valor de '{k}' no es numérico: {v!r}")
            no_numericas[str(k)] = v

    # Primero la seguridad y la sintaxis; después los datos que falten. Al revés,
    # una expresión maliciosa se reportaría como "faltan datos" y confundiría.
    sustituida = _sustituir(e, valores)
    ok, error_sintaxis, _ = validar(e)
    if not ok:
        return Resultado(None, original, sustituida, {}, [], error=error_sintaxis)

    arbol = ast.parse(e, mode="eval")
    if len(list(ast.walk(arbol))) > MAX_NODOS:
        return Resultado(None, original, sustituida, {}, [],
                         error="La fórmula es demasiado compleja.")

    requeridas = variables_de(e)
    faltantes = [v for v in requeridas if v not in valores and v not in CONSTANTES]
    usadas = {k: valores[k] for k in requeridas if k in valores}

    if faltantes:
        return Resultado(None, original, sustituida, usadas, faltantes,
                         error="Faltan datos: " + ", ".join(faltantes))

    try:
        valor = _num(arbol.body, valores)
    except ErrorFormula as exc:
        return Resultado(None, original, sustituida, usadas, [], error=str(exc))
    except KeyError as exc:
        return Resultado(None, original, sustituida, usadas, [str(exc.args[0])],
                         error=f"Falta el dato: {exc.args[0]}")
    except (InvalidOperation, DivisionByZero, OverflowError) as exc:
        return Resultado(None, original, sustituida, usadas, [], error=f"Error de cálculo: {exc}")

    pasos = [f"{k} = {_limpio(v)}" for k, v in usadas.items()]
    pasos.append(f"{sustituida} = {_limpio(valor)}")
    return Resultado(valor, original, sustituida, usadas, [], pasos)


def validar(expresion: str) -> tuple[bool, str | None, list[str]]:
    """Comprueba la sintaxis sin necesitar valores. Devuelve (ok, error, variables)."""
    e = normalizar(expresion or "")
    if not e:
        return False, "Fórmula vacía.", []
    try:
        arbol = ast.parse(e, mode="eval")
    except SyntaxError as exc:
        return False, f"Error de sintaxis: {exc.msg}", []
    for n in ast.walk(arbol):
        if not isinstance(n, _NODOS_PERMITIDOS):
            return False, f"Elemento no permitido: {type(n).__name__}", []
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id not in FUNCIONES:
            return False, f"Función no permitida: {n.func.id}()", []
    return True, None, variables_de(e)


# --- Plantillas de fórmula ----------------------------------------------------
# Las que pidió el pliego, más las de uso diario. `dimension` es la que produce
# el resultado; el motor la contrasta con la unidad de la partida.

PLANTILLAS: list[dict] = [
    {"clave": "conteo", "nombre": "Conteo simple",
     "expresion": "n", "dimension": "conteo",
     "variables": {"n": "cantidad"},
     "ayuda": "Número de elementos iguales."},

    {"clave": "longitud", "nombre": "Longitud (n × largo)",
     "expresion": "n * largo", "dimension": "longitud",
     "variables": {"n": "cantidad", "largo": "largo (m)"},
     "ayuda": "Tuberías, sardineles, zócalos, vigas por metro lineal."},

    {"clave": "area", "nombre": "Área (n × largo × ancho)",
     "expresion": "n * largo * ancho", "dimension": "area",
     "variables": {"n": "cantidad", "largo": "largo (m)", "ancho": "ancho (m)"},
     "ayuda": "Pisos, losas, encofrado de fondo."},

    {"clave": "volumen", "nombre": "Volumen (n × largo × ancho × alto)",
     "expresion": "n * largo * ancho * alto", "dimension": "volumen",
     "variables": {"n": "cantidad", "largo": "largo (m)", "ancho": "ancho (m)", "alto": "alto o profundidad (m)"},
     "ayuda": "Concreto de zapatas, vigas y columnas; excavación de prisma."},

    {"clave": "perimetro_altura", "nombre": "Perímetro × altura",
     "expresion": "n * perimetro * altura", "dimension": "area",
     "variables": {"n": "cantidad", "perimetro": "perímetro (m)", "altura": "altura (m)"},
     "ayuda": "Encofrado de columnas, tarrajeo de contorno."},

    {"clave": "area_espesor", "nombre": "Área × espesor",
     "expresion": "area * espesor", "dimension": "volumen",
     "variables": {"area": "área (m2)", "espesor": "espesor (m)"},
     "ayuda": "Losas macizas, falso piso, contrapiso, base granular."},

    {"clave": "area_menos_vanos", "nombre": "Área bruta − vanos",
     "expresion": "n * largo * alto - vanos", "dimension": "area",
     "variables": {"n": "cantidad", "largo": "largo (m)", "alto": "alto (m)", "vanos": "área de vanos (m2)"},
     "ayuda": "Muros, tarrajeo y pintura con descuento de puertas y ventanas."},

    {"clave": "peso_longitud", "nombre": "Peso unitario × longitud",
     "expresion": "n * longitud * peso_unitario", "dimension": "masa",
     "variables": {"n": "cantidad", "longitud": "longitud (m)", "peso_unitario": "peso unitario (kg/m)"},
     "ayuda": "Acero de refuerzo y perfiles metálicos."},

    {"clave": "areas_medias", "nombre": "Áreas medias entre secciones",
     "expresion": "(area1 + area2) / 2 * distancia", "dimension": "volumen",
     "variables": {"area1": "área sección 1 (m2)", "area2": "área sección 2 (m2)", "distancia": "distancia (m)"},
     "ayuda": "Movimiento de tierras entre dos secciones transversales."},

    {"clave": "prismoidal", "nombre": "Fórmula prismoidal",
     "expresion": "distancia / 6 * (area1 + 4 * area_media + area2)", "dimension": "volumen",
     "variables": {"area1": "área sección 1 (m2)", "area_media": "área sección media (m2)",
                   "area2": "área sección 2 (m2)", "distancia": "distancia (m)"},
     "ayuda": "Volumen exacto entre secciones cuando el terreno no varía linealmente."},

    {"clave": "zanja", "nombre": "Zanja (largo × ancho × prof. media)",
     "expresion": "largo * ancho * (prof_inicial + prof_final) / 2", "dimension": "volumen",
     "variables": {"largo": "largo (m)", "ancho": "ancho (m)",
                   "prof_inicial": "profundidad inicial (m)", "prof_final": "profundidad final (m)"},
     "ayuda": "Zanjas con pendiente entre buzones."},

    {"clave": "talud", "nombre": "Excavación con talud",
     "expresion": "largo * (ancho_fondo + talud * prof) * prof", "dimension": "volumen",
     "variables": {"largo": "largo (m)", "ancho_fondo": "ancho de fondo (m)",
                   "talud": "relación H:V (ej. 0.5)", "prof": "profundidad (m)"},
     "ayuda": "Sección trapezoidal: ancho superior = fondo + 2·talud·prof."},

    {"clave": "cilindro", "nombre": "Volumen cilíndrico",
     "expresion": "n * PI * (diametro / 2) ** 2 * altura", "dimension": "volumen",
     "variables": {"n": "cantidad", "diametro": "diámetro (m)", "altura": "altura o longitud (m)"},
     "ayuda": "Pilotes, columnas circulares, tanques."},

    {"clave": "libre", "nombre": "Fórmula libre",
     "expresion": "", "dimension": None,
     "variables": {},
     "ayuda": "Escriba su propia expresión con las variables que necesite."},
]

PLANTILLAS_POR_CLAVE = {p["clave"]: p for p in PLANTILLAS}
