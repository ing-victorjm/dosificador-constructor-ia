"""Pruebas del motor de cálculo.

Se prueba lo que puede arruinar un expediente: la aritmética, las reglas
normativas y los casos en los que la app DEBE negarse a inventar un número.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from backend.motor import acero, costos, formulas, medicion, normas, unidades
from backend.motor.redondeo import ReglasRedondeo, dec, redondear


# --------------------------------------------------------------------------- #
# Precisión decimal
# --------------------------------------------------------------------------- #

def test_suma_decimal_exacta():
    """0.1 + 0.2 debe dar 0.3, no 0.30000000000000004."""
    assert dec("0.1") + dec("0.2") == dec("0.3")


def test_redondeo_medio_arriba_vs_medio_par():
    assert redondear("2.345", 2, "medio_arriba") == dec("2.35")
    assert redondear("2.345", 2, "medio_par") == dec("2.34")


def test_parseo_de_miles_en_ambas_convenciones():
    assert dec("1,234.56") == dec("1234.56")
    assert dec("1.234,56") == dec("1234.56")


# --------------------------------------------------------------------------- #
# Unidades
# --------------------------------------------------------------------------- #

def test_conversion_imperial_metrica():
    assert unidades.convertir(1, "sf", "m2") == dec("0.09290304")
    assert unidades.convertir(1, "cy", "m3") == dec("0.764554857984")


def test_no_convierte_entre_dimensiones_distintas():
    with pytest.raises(unidades.ErrorUnidad):
        unidades.convertir(1, "m2", "m3")


def test_unidad_desconocida_falla_con_mensaje_util():
    with pytest.raises(unidades.ErrorUnidad) as exc:
        unidades.unidad("metros lineales cuadrados")
    assert "desconocida" in str(exc.value).lower()


# --------------------------------------------------------------------------- #
# Fórmulas
# --------------------------------------------------------------------------- #

def test_formula_con_x_de_obra_y_coma_decimal():
    r = formulas.evaluar("n x largo x ancho x alto",
                         {"n": 3, "largo": "4,20", "ancho": "0.25", "alto": "0.60"})
    assert r.valor == dec("1.89")
    assert r.sustituida == "3 * 4.2 * 0.25 * 0.6"


def test_formula_no_asume_cero_cuando_falta_un_dato():
    r = formulas.evaluar("n * largo * alto - vanos", {"n": 1, "largo": 5, "alto": 2.4})
    assert r.valor is None
    assert r.faltantes == ["vanos"]


def test_formula_rechaza_codigo_arbitrario():
    assert formulas.evaluar("__import__('os').system('dir')").valor is None
    assert "no permitida" in formulas.evaluar("open('x')").error.lower()


def test_formula_ignora_variables_no_numericas_que_no_usa():
    """El diámetro '5/8\"' acompaña al cálculo como dato, no debe romperlo."""
    r = formulas.evaluar("n * longitud * peso_unitario",
                         {"n": 12, "longitud": "1.60", "peso_unitario": "1.552",
                          "diametro": '5/8"', "marca": "Z-1"})
    assert r.valor == dec("29.7984")


def test_division_entre_cero_no_revienta():
    r = formulas.evaluar("area / 0", {"area": 5})
    assert r.valor is None
    assert "cero" in r.error.lower()


# --------------------------------------------------------------------------- #
# Planilla: la regla de los campos vacíos
# --------------------------------------------------------------------------- #

def test_campo_vacio_se_omite_no_vale_cero():
    """Es la regla que rompía la app anterior: vacío ≠ cero."""
    f = medicion.calcular_fila({"n": "1", "largo": "5.00", "ancho": "3.00"}, "m2")
    assert f.parcial == dec("15.00")


def test_cero_declarado_si_anula_el_parcial():
    f = medicion.calcular_fila({"n": "1", "largo": "5.00", "ancho": "0"}, "m2")
    assert f.parcial == dec("0.00")


def test_bloqueo_dimensional_area_alimentada_por_volumen():
    f = medicion.calcular_fila({"n": "1", "largo": "5", "ancho": "3", "alto": "2.4"}, "m2")
    assert f.parcial is None
    assert "dimensional" in f.error.lower()


def test_valor_precalculado_avisa_pero_no_bloquea():
    """Un área tomada del plano y escrita en una sola celda es legítima."""
    f = medicion.calcular_fila({"n": "1", "largo": "108.00"}, "m2")
    assert f.parcial == dec("108.00")
    assert f.aviso is not None


def test_total_suma_parciales_ya_redondeados():
    """La planilla impresa debe cuadrar línea a línea con una calculadora."""
    reglas = ReglasRedondeo()
    filas = [medicion.calcular_fila({"n": "1", "largo": "3.333"}, "m", reglas) for _ in range(3)]
    total = medicion.total_partida(filas, "m", reglas=reglas)
    assert total.total == dec("9.99")     # 3.33 × 3, no 9.999 → 10.00


def test_desperdicio_no_entra_al_metrado():
    reglas = ReglasRedondeo()
    filas = [medicion.calcular_fila({"n": "1", "largo": "100"}, "m2", reglas)]
    total = medicion.total_partida(filas, "m2", desperdicio_pct="7", reglas=reglas)
    assert total.total == dec("100.00")
    assert total.cantidad_a_comprar == dec("107.00")


def test_cantidad_manual_se_marca_como_sin_sustento():
    total = medicion.total_partida([], "m2", cantidad_manual="250")
    assert total.total == dec("250.00")
    assert total.origen == "manual"
    assert any("sustento" in a for a in total.avisos)


# --------------------------------------------------------------------------- #
# Reglas normativas
# --------------------------------------------------------------------------- #

def test_muros_descuentan_todo_vano_sin_umbral():
    aplica, motivo, area = normas.descontar_vano("0.16", "muros")
    assert aplica is True
    assert area == dec("0.16")
    assert "OE.3.1" in motivo


def test_pisos_no_descuentan_huecos_menores_a_025():
    aplica, motivo, area = normas.descontar_vano("0.16", "pisos")
    assert aplica is False
    assert area == 0
    assert "0.25" in motivo


def test_revestimientos_espana_descuentan_solo_el_exceso():
    """Un umbral binario sobremetraría el descuento en España."""
    aplica, _motivo, area = normas.descontar_vano("5.00", "revestimientos_es")
    assert aplica is True
    assert area == dec("1.00")          # 5.00 − 4.00, no 5.00


def test_vacio_por_lleno_no_descuenta_nada():
    aplica, _motivo, area = normas.descontar_vano("9.00", "vacio_por_lleno")
    assert aplica is False
    assert area == 0


def test_umbral_de_dos_metros_esta_marcado_como_costumbre():
    assert normas.UMBRAL_MITO["etiqueta"] == normas.COSTUMBRE_OBRA
    assert "NO figura" in normas.UMBRAL_MITO["aviso"]


def test_familia_por_defecto_reconoce_el_texto_de_la_partida():
    assert normas.familia_por_defecto("arquitectura", "Muro de ladrillo King Kong") == "muros"
    assert normas.familia_por_defecto("arquitectura", "Tarrajeo en interiores") == "revoques"
    assert normas.familia_por_defecto("arquitectura", "Contrapiso e=48 mm") == "pisos"


def test_deduccion_de_vanos_conserva_los_no_descontados():
    """El revisor busca justamente la leyenda del vano que NO se descontó."""
    filas = medicion.filas_deduccion_vanos(
        [{"descripcion": "Rejilla", "n": 1, "ancho": "0.40", "alto": "0.40"}], "pisos")
    assert filas[0]["aplica"] is False
    assert "no se descuenta" in filas[0]["motivo"]


# --------------------------------------------------------------------------- #
# Acero
# --------------------------------------------------------------------------- #

def test_cuadro_de_acero_calcula_peso_y_resume_por_diametro():
    cuadro = acero.cuadro([
        {"marca": "Z-1", "elemento": "Zapata", "diametro": '5/8"',
         "cantidad": "10", "longitud": "1.60"},
        {"marca": "Z-1", "elemento": "Zapata", "diametro": '5/8"',
         "cantidad": "10", "longitud": "1.60"},
    ])
    assert cuadro["barras_incompletas"] == 0
    assert len(cuadro["resumen_por_diametro"]) == 1
    assert dec(cuadro["peso_total"]) > 0


def test_barra_sin_longitud_no_inventa_peso():
    cuadro = acero.cuadro([{"marca": "C-1", "diametro": '1/2"', "cantidad": "8"}])
    assert cuadro["barras_incompletas"] == 1
    assert cuadro["peso_total"] == "0.00"


def test_ratio_kg_m3_avisa_que_no_es_metrado():
    control = acero.control_por_ratio("1600", "8", "columna")
    assert control["aplica"] is True
    assert "no aparece" in control["aviso"].lower() or "ESTIMACIÓN" in control["aviso"]


# --------------------------------------------------------------------------- #
# Costos
# --------------------------------------------------------------------------- #

def test_apu_cantidad_mano_de_obra_por_rendimiento():
    """Convención S10: cuadrilla × 8 h / rendimiento."""
    r = costos.analisis(
        [{"tipo": "MO", "descripcion": "Operario", "unidad": "hh",
          "cuadrilla": "2", "precio": "23.00"}],
        rendimiento_partida="16")
    assert r["lineas"][0]["cantidad"] == "1.0000"     # 2 × 8 / 16, a 4 decimales
    assert r["pu"] == "23.00"


def test_herramientas_menores_como_porcentaje_de_mano_de_obra():
    r = costos.analisis([
        {"tipo": "MO", "descripcion": "Operario", "unidad": "hh",
         "cuadrilla": "1", "precio": "20.00"},
        {"tipo": "EQ", "descripcion": "Herramientas", "unidad": "pct", "cantidad": "3"},
    ], rendimiento_partida="8")
    # MO = 1 × 8 / 8 = 1 hh × 20 = 20.00 ; herramientas = 3% de 20 = 0.60
    assert r["por_tipo"]["EQ"] == "0.60"


def test_resumen_de_presupuesto_encadena_gg_utilidad_e_impuesto():
    r = costos.resumen("100000", gg_pct="10", utilidad_pct="5", impuesto_pct="18")
    assert r["gastos_generales"] == "10000.00"
    assert r["utilidad"] == "5000.00"
    assert r["subtotal"] == "115000.00"
    assert r["impuesto"] == "20700.00"
    assert r["total"] == "135700.00"
