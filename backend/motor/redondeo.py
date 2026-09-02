"""Precisión decimal y reglas de redondeo configurables.

Todo el motor trabaja con `Decimal`. El redondeo NUNCA se aplica dentro de un
cálculo intermedio: se aplica al publicar un valor (parcial, subtotal, total),
porque redondear en cadena arrastra error y descuadra el metrado impreso.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_UP, ROUND_DOWN, InvalidOperation, getcontext
from typing import Any

# 28 dígitos: sobra para cualquier metrado y evita ruido binario.
getcontext().prec = 28

MODOS = {
    "medio_arriba": ROUND_HALF_UP,      # 2.345 -> 2.35   (convención de obra en LatAm)
    "medio_par": ROUND_HALF_EVEN,       # 2.345 -> 2.34   (bancario / ISO 80000)
    "arriba": ROUND_UP,                 # siempre hacia arriba (compra de materiales)
    "abajo": ROUND_DOWN,
}

# Decimales por defecto según lo que se está publicando.
DECIMALES_POR_DEFECTO = {
    "metrado": 2,
    "precio": 2,
    "parcial": 2,
    "peso": 3,
    "longitud": 3,
    "porcentaje": 4,
    "coeficiente": 6,
}


class ReglasRedondeo:
    """Configuración de redondeo de un proyecto."""

    def __init__(
        self,
        decimales_metrado: int = 2,
        decimales_precio: int = 2,
        decimales_parcial: int = 2,
        modo: str = "medio_arriba",
    ) -> None:
        if modo not in MODOS:
            raise ValueError(f"Modo de redondeo desconocido: {modo}. Use uno de {sorted(MODOS)}")
        for nombre, valor in (
            ("decimales_metrado", decimales_metrado),
            ("decimales_precio", decimales_precio),
            ("decimales_parcial", decimales_parcial),
        ):
            if not isinstance(valor, int) or not 0 <= valor <= 8:
                raise ValueError(f"{nombre} debe ser un entero entre 0 y 8, se recibió {valor!r}")
        self.decimales_metrado = decimales_metrado
        self.decimales_precio = decimales_precio
        self.decimales_parcial = decimales_parcial
        self.modo = modo

    @property
    def rounding(self):
        return MODOS[self.modo]

    def metrado(self, valor: Any) -> Decimal:
        return redondear(valor, self.decimales_metrado, self.modo)

    def precio(self, valor: Any) -> Decimal:
        return redondear(valor, self.decimales_precio, self.modo)

    def parcial(self, valor: Any) -> Decimal:
        return redondear(valor, self.decimales_parcial, self.modo)

    def a_dict(self) -> dict:
        return {
            "decimales_metrado": self.decimales_metrado,
            "decimales_precio": self.decimales_precio,
            "decimales_parcial": self.decimales_parcial,
            "modo": self.modo,
        }

    @classmethod
    def desde_dict(cls, d: dict | None) -> "ReglasRedondeo":
        d = d or {}
        return cls(
            decimales_metrado=int(d.get("decimales_metrado", 2)),
            decimales_precio=int(d.get("decimales_precio", 2)),
            decimales_parcial=int(d.get("decimales_parcial", 2)),
            modo=str(d.get("modo", "medio_arriba")),
        )


DEFECTO = ReglasRedondeo()


def dec(valor: Any) -> Decimal:
    """Convierte a Decimal sin pasar por float (evita 0.1+0.2 = 0.30000000000000004)."""
    if isinstance(valor, Decimal):
        return valor
    if valor is None or valor == "":
        return Decimal("0")
    if isinstance(valor, bool):
        return Decimal(1) if valor else Decimal(0)
    if isinstance(valor, int):
        return Decimal(valor)
    if isinstance(valor, float):
        # repr() da la representación más corta que reconstruye el float.
        return Decimal(repr(valor))
    texto = str(valor).strip().replace(" ", "")
    if texto.count(",") and texto.count("."):
        # "1.234,56" (es-PE con miles) vs "1,234.56" (en-US)
        texto = texto.replace(".", "").replace(",", ".") if texto.rfind(",") > texto.rfind(".") else texto.replace(",", "")
    elif texto.count(","):
        texto = texto.replace(",", ".")
    try:
        return Decimal(texto)
    except InvalidOperation as exc:
        raise ValueError(f"No es un número válido: {valor!r}") from exc


def redondear(valor: Any, decimales: int = 2, modo: str = "medio_arriba") -> Decimal:
    cuantia = Decimal(1).scaleb(-decimales)
    return dec(valor).quantize(cuantia, rounding=MODOS[modo])


def es_cero(valor: Any, tol: str = "1E-9") -> bool:
    return abs(dec(valor)) < Decimal(tol)


def a_float(valor: Any) -> float:
    """Solo para serializar a JSON. Nunca para calcular."""
    return float(dec(valor))


def formato(valor: Any, decimales: int = 2, sep_miles: str = ",", sep_decimal: str = ".") -> str:
    """Formatea para mostrar. `sep_*` vienen de la configuración del país."""
    d = redondear(valor, decimales)
    negativo = d < 0
    entero, _, frac = f"{abs(d):.{decimales}f}".partition(".")
    grupos = []
    while len(entero) > 3:
        grupos.insert(0, entero[-3:])
        entero = entero[:-3]
    grupos.insert(0, entero)
    salida = sep_miles.join(grupos)
    if decimales:
        salida = f"{salida}{sep_decimal}{frac}"
    return f"-{salida}" if negativo else salida
