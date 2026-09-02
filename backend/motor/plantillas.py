"""Plantillas de metrados por tipo de proyecto.

Cada línea referencia un CÓDIGO REAL de la Norma Técnica de Metrados. No se
inventan códigos: si un código no está en el catálogo cargado, la partida se
crea por su nombre literal y sin código, y así queda marcado.
"""
from __future__ import annotations

T = "titulo"
P = "partida"


def _p(codigo, descripcion, unidad, especialidad, familia=None):
    return {"tipo": P, "codigo": codigo, "descripcion": descripcion, "unidad": unidad,
            "especialidad": especialidad, "familia_descuento": familia}


def _t(descripcion, especialidad, hijos):
    return {"tipo": T, "descripcion": descripcion, "especialidad": especialidad,
            "hijos": hijos}


EDIFICACION = [
    _t("OBRAS PROVISIONALES Y TRABAJOS PRELIMINARES", "preliminares", [
        _p("OE.1.1.1.8", "Cartel de identificación de la obra", "und", "preliminares"),
        _p("OE.1.1.3", "Cerco de obra", "m", "preliminares"),
        _p("OE.1.1.9", "Trazos, niveles y replanteo", "m2", "preliminares"),
        _p("OE.1.1.9.1", "Trazo, niveles y replanteo preliminar", "m2", "preliminares"),
    ]),
    _t("MOVIMIENTO DE TIERRAS", "movimiento_tierras", [
        _p("OE.2.1.1", "Nivelación de terreno", "m2", "movimiento_tierras"),
        _p("OE.2.1.2.1", "Excavación masiva", "m3", "movimiento_tierras"),
        _p("OE.2.1.2", "Excavación para zapatas", "m3", "movimiento_tierras"),
        _p("OE.2.1.2", "Excavación para cimientos corridos", "m3", "movimiento_tierras"),
        _p("OE.2.1.4", "Relleno con material propio compactado", "m3", "movimiento_tierras"),
        _p("OE.2.1.5", "Nivelación interior y apisonado", "m2", "movimiento_tierras"),
        _p("OE.2.1.6", "Eliminación de material excedente", "m3", "movimiento_tierras"),
    ]),
    _t("OBRAS DE CONCRETO SIMPLE", "estructuras", [
        _p("OE.2.2.1", "Cimientos corridos", "m3", "estructuras"),
        _p("OE.2.2.3", "Solado", "m2", "estructuras"),
        _p("OE.2.2.6", "Sobrecimientos", "m3", "estructuras"),
        _p("OE.2.2.9", "Falso piso", "m2", "estructuras"),
    ]),
    _t("OBRAS DE CONCRETO ARMADO", "estructuras", [
        _t("Zapatas", "estructuras", [
            _p("OE.2.3.2.1", "Zapatas — concreto f'c=210 kg/cm2", "m3", "estructuras"),
            _p("OE.2.3.2.2", "Zapatas — encofrado y desencofrado", "m2", "estructuras"),
            _p("OE.2.3.2.3", "Zapatas — acero de refuerzo fy=4200", "kg", "estructuras"),
        ]),
        _t("Vigas de cimentación", "estructuras", [
            _p("OE.2.3.3.1", "Vigas de cimentación — concreto f'c=210", "m3", "estructuras"),
            _p("OE.2.3.3.2", "Vigas de cimentación — encofrado", "m2", "estructuras"),
            _p("OE.2.3.3.3", "Vigas de cimentación — acero", "kg", "estructuras"),
        ]),
        _t("Columnas", "estructuras", [
            _p("OE.2.3.7.1", "Columnas — concreto f'c=210 kg/cm2", "m3", "estructuras"),
            _p("OE.2.3.7.2", "Columnas — encofrado y desencofrado", "m2", "estructuras"),
            _p("OE.2.3.7.3", "Columnas — acero de refuerzo fy=4200", "kg", "estructuras"),
        ]),
        _t("Vigas", "estructuras", [
            _p("OE.2.3.8.1", "Vigas — concreto f'c=210 kg/cm2", "m3", "estructuras"),
            _p("OE.2.3.8.2", "Vigas — encofrado y desencofrado", "m2", "estructuras"),
            _p("OE.2.3.8.3", "Vigas — acero de refuerzo fy=4200", "kg", "estructuras"),
        ]),
        _t("Losas aligeradas", "estructuras", [
            _p("OE.2.3.9.2.1", "Losa aligerada — concreto f'c=210", "m3", "estructuras"),
            _p("OE.2.3.9.2.2", "Losa aligerada — encofrado y desencofrado", "m2", "estructuras"),
            _p("OE.2.3.9.2.3", "Losa aligerada — acero de refuerzo", "kg", "estructuras"),
            _p("OE.2.3.9.2.4", "Losa aligerada — ladrillo de techo 15x30x30", "und", "estructuras"),
        ]),
        _t("Escaleras", "estructuras", [
            _p("OE.2.3.11.1", "Escalera — concreto f'c=210", "m3", "estructuras"),
            _p("OE.2.3.11.2", "Escalera — encofrado y desencofrado", "m2", "estructuras"),
            _p("OE.2.3.11.3", "Escalera — acero de refuerzo", "kg", "estructuras"),
        ]),
    ]),
    _t("ARQUITECTURA — MUROS Y TABIQUES", "arquitectura", [
        _p("OE.3.1.1", "Muro de ladrillo King Kong de arcilla, aparejo de soga",
           "m2", "arquitectura", "muros"),
        _p("OE.3.1.3", "Muro de ladrillo pandereta, aparejo de soga",
           "m2", "arquitectura", "muros"),
    ]),
    _t("ARQUITECTURA — REVOQUES Y ENLUCIDOS", "arquitectura", [
        _p("OE.3.2.2", "Tarrajeo en interiores", "m2", "arquitectura", "revoques"),
        _p("OE.3.2.3", "Tarrajeo en exteriores", "m2", "arquitectura", "revoques"),
        _p("OE.3.2.5", "Tarrajeo en columnas", "m2", "arquitectura", "revoques"),
        _p("OE.3.2.6", "Tarrajeo en vigas", "m2", "arquitectura", "revoques"),
        _p("OE.3.2.19", "Vestidura de derrames", "m", "arquitectura", "sin_descuento"),
    ]),
    _t("ARQUITECTURA — CIELORRASOS", "arquitectura", [
        _p("OE.3.3.1", "Cielorraso con yeso", "m2", "arquitectura", "cielorrasos"),
    ]),
    _t("ARQUITECTURA — PISOS Y PAVIMENTOS", "arquitectura", [
        _p("OE.3.4.1", "Contrapiso e=48 mm", "m2", "arquitectura", "pisos"),
        _p("OE.3.4.2", "Piso cerámico 0.45x0.45 m", "m2", "arquitectura", "pisos"),
        _p("OE.3.4.3", "Piso de concreto pulido", "m2", "arquitectura", "pisos"),
    ]),
    _t("ARQUITECTURA — ZÓCALOS Y CONTRAZÓCALOS", "arquitectura", [
        _p("OE.3.5.1", "Zócalo cerámico h=1.20 m", "m2", "arquitectura", "sin_descuento"),
        _p("OE.3.5.2", "Contrazócalo cerámico h=0.10 m", "m", "arquitectura", "sin_descuento"),
    ]),
    _t("ARQUITECTURA — CARPINTERÍA Y VIDRIOS", "arquitectura", [
        _p("OE.3.7.1", "Puerta contraplacada de madera", "und", "arquitectura"),
        _p("OE.3.7.2", "Ventana de madera", "und", "arquitectura"),
        _p("OE.3.9.1", "Vidrio simple incoloro", "m2", "arquitectura"),
        _p("OE.3.10.1", "Cerradura de perilla para puerta", "und", "arquitectura"),
    ]),
    _t("ARQUITECTURA — PINTURA", "arquitectura", [
        _p("OE.3.11.1", "Pintura látex en cielorrasos, vigas, columnas y paredes",
           "m2", "arquitectura", "pintura"),
        _p("OE.3.11.2", "Pintura de puertas", "m2", "arquitectura", "sin_descuento"),
    ]),
    _t("INSTALACIONES SANITARIAS", "sanitarias", [
        _p("OE.4.1.1", "Suministro de aparatos sanitarios", "und", "sanitarias"),
        _p("OE.4.1.3", "Instalación de aparatos sanitarios", "und", "sanitarias"),
        _p("OE.4.2.1", "Salida de agua fría", "pto", "sanitarias"),
        _p("OE.4.2.2", "Red de distribución de agua fría PVC", "m", "sanitarias"),
        _p("OE.4.3.1", "Salida de desagüe PVC", "pto", "sanitarias"),
        _p("OE.4.3.2", "Red de derivación de desagüe PVC", "m", "sanitarias"),
    ]),
    _t("INSTALACIONES ELÉCTRICAS", "electricas", [
        _p("OE.5.1.1", "Salida para alumbrado en techo", "pto", "electricas"),
        _p("OE.5.1.2", "Salida para tomacorriente bipolar doble", "pto", "electricas"),
        _p("OE.5.2.2", "Tubería PVC-SEL Ø 20 mm", "m", "electricas"),
        _p("OE.5.2.3", "Conductor THW 2.5 mm2", "m", "electricas"),
        _p("OE.5.2.7", "Tablero de distribución", "und", "electricas"),
        _p("OE.5.4", "Pozo de puesta a tierra", "und", "electricas"),
        _p("OE.5.5.1", "Artefacto de iluminación", "und", "electricas"),
    ]),
    _t("VARIOS Y TRABAJOS FINALES", "varios", [
        _p("OE.3.13.1", "Limpieza permanente de obra", "m2", "varios"),
        _p("OE.3.13.2", "Limpieza final de obra", "m2", "varios"),
    ]),
]

VIVIENDA = EDIFICACION

PLANTILLAS: dict[str, dict] = {
    "edificacion": {
        "clave": "edificacion",
        "nombre": "Edificación (vivienda o edificio)",
        "descripcion": "Estructura completa de una edificación: preliminares, movimiento de "
                       "tierras, concreto simple y armado, arquitectura, sanitarias y eléctricas.",
        "tipos": ["vivienda", "edificio", "comercio", "oficinas", "salud", "educacion"],
        "arbol": EDIFICACION,
    },
    "estructuras": {
        "clave": "estructuras",
        "nombre": "Solo estructuras",
        "descripcion": "Movimiento de tierras, concreto simple y concreto armado.",
        "tipos": ["edificio", "industria"],
        "arbol": [n for n in EDIFICACION
                  if n["especialidad"] in ("preliminares", "movimiento_tierras", "estructuras")],
    },
    "acabados": {
        "clave": "acabados",
        "nombre": "Solo acabados",
        "descripcion": "Arquitectura completa: muros, revoques, cielorrasos, pisos, zócalos, "
                       "carpintería y pintura.",
        "tipos": ["vivienda", "comercio", "oficinas"],
        "arbol": [n for n in EDIFICACION if n["especialidad"] == "arquitectura"],
    },
}


def contar(arbol: list[dict]) -> int:
    total = 0
    for n in arbol:
        if n["tipo"] == P:
            total += 1
        else:
            total += contar(n.get("hijos") or [])
    return total


def catalogo() -> list[dict]:
    return [{"clave": p["clave"], "nombre": p["nombre"], "descripcion": p["descripcion"],
             "tipos": p["tipos"], "partidas": contar(p["arbol"])}
            for p in PLANTILLAS.values()]
