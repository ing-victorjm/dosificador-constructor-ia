"""Especialidades: identidad, color y orden de presentación.

El color no es decoración: es el código con el que se pintan los trazos en el
plano, las filas de la planilla y las barras del panel. Que una tubería de agua
sea siempre del mismo azul es lo que permite leer un plano marcado de un vistazo.
"""
from __future__ import annotations

ESPECIALIDADES: list[dict] = [
    {"clave": "preliminares", "nombre": "Obras provisionales y trabajos preliminares",
     "corto": "Preliminares", "codigo": "OE.1", "color": "#8593ab", "icono": "cerca", "orden": 1},
    {"clave": "movimiento_tierras", "nombre": "Movimiento de tierras",
     "corto": "Mov. de tierras", "codigo": "OE.2.1", "color": "#a16207", "icono": "excavadora", "orden": 2},
    {"clave": "estructuras", "nombre": "Estructuras",
     "corto": "Estructuras", "codigo": "OE.2", "color": "#d6455d", "icono": "columna", "orden": 3},
    {"clave": "arquitectura", "nombre": "Arquitectura",
     "corto": "Arquitectura", "codigo": "OE.3", "color": "#1d5bd8", "icono": "plano", "orden": 4},
    {"clave": "sanitarias", "nombre": "Instalaciones sanitarias",
     "corto": "Sanitarias", "codigo": "OE.4", "color": "#0891b2", "icono": "gota", "orden": 5},
    {"clave": "electricas", "nombre": "Instalaciones eléctricas",
     "corto": "Eléctricas", "codigo": "OE.5", "color": "#c07b10", "icono": "rayo", "orden": 6},
    {"clave": "mecanicas", "nombre": "Instalaciones mecánicas",
     "corto": "Mecánicas", "codigo": "OE.5.6", "color": "#9333ea", "icono": "engranaje", "orden": 7},
    {"clave": "comunicaciones", "nombre": "Instalaciones de comunicaciones",
     "corto": "Comunicaciones", "codigo": "OE.6", "color": "#0d9463", "icono": "antena", "orden": 8},
    {"clave": "exteriores", "nombre": "Obras exteriores e infraestructura",
     "corto": "Exteriores", "codigo": "OU", "color": "#65a30d", "icono": "arbol", "orden": 9},
    {"clave": "seguridad", "nombre": "Seguridad y salud en obra",
     "corto": "Seguridad", "codigo": "OE.1.6", "color": "#ea580c", "icono": "casco", "orden": 10},
    {"clave": "varios", "nombre": "Varios y trabajos finales",
     "corto": "Varios", "codigo": "OE.3.13", "color": "#64748b", "icono": "escoba", "orden": 11},
]

POR_CLAVE = {e["clave"]: e for e in ESPECIALIDADES}
CLAVES = [e["clave"] for e in ESPECIALIDADES]


def color(clave: str) -> str:
    return POR_CLAVE.get(clave, POR_CLAVE["varios"])["color"]


def nombre(clave: str) -> str:
    return POR_CLAVE.get(clave, POR_CLAVE["varios"])["nombre"]


def normalizar(texto: str | None) -> str:
    """Acepta 'Estructuras', 'ESTRUCTURA', 'OE.2' y devuelve la clave interna."""
    if not texto:
        return "varios"
    t = str(texto).strip().lower()
    if t in POR_CLAVE:
        return t
    for e in ESPECIALIDADES:
        if t in (e["nombre"].lower(), e["corto"].lower(), (e["codigo"] or "").lower()):
            return e["clave"]
    equivalencias = {
        "estructura": "estructuras", "arquitectonicas": "arquitectura",
        "sanitaria": "sanitarias", "electrica": "electricas", "iiee": "electricas",
        "iiss": "sanitarias", "mecanica": "mecanicas", "hvac": "mecanicas",
        "tierras": "movimiento_tierras", "excavaciones": "movimiento_tierras",
        "acabados": "arquitectura", "obras exteriores": "exteriores",
    }
    return equivalencias.get(t, "varios")


TIPOS_ELEMENTO: list[dict] = [
    {"clave": "zapata", "nombre": "Zapata", "especialidad": "estructuras",
     "dimensiones": ["largo", "ancho", "peralte", "profundidad"], "partidas": ["concreto", "encofrado", "acero", "excavacion"]},
    {"clave": "cimiento_corrido", "nombre": "Cimiento corrido", "especialidad": "estructuras",
     "dimensiones": ["longitud", "ancho", "altura", "profundidad"], "partidas": ["concreto", "excavacion"]},
    {"clave": "sobrecimiento", "nombre": "Sobrecimiento", "especialidad": "estructuras",
     "dimensiones": ["longitud", "ancho", "altura"], "partidas": ["concreto", "encofrado"]},
    {"clave": "columna", "nombre": "Columna", "especialidad": "estructuras",
     "dimensiones": ["lado_a", "lado_b", "altura"], "partidas": ["concreto", "encofrado", "acero"]},
    {"clave": "placa", "nombre": "Placa / muro de corte", "especialidad": "estructuras",
     "dimensiones": ["longitud", "espesor", "altura"], "partidas": ["concreto", "encofrado", "acero"]},
    {"clave": "viga", "nombre": "Viga", "especialidad": "estructuras",
     "dimensiones": ["longitud", "base", "peralte"], "partidas": ["concreto", "encofrado", "acero"]},
    {"clave": "viga_cimentacion", "nombre": "Viga de cimentación", "especialidad": "estructuras",
     "dimensiones": ["longitud", "base", "peralte", "profundidad"], "partidas": ["concreto", "encofrado", "acero", "excavacion"]},
    {"clave": "losa_maciza", "nombre": "Losa maciza", "especialidad": "estructuras",
     "dimensiones": ["largo", "ancho", "espesor"], "partidas": ["concreto", "encofrado", "acero"]},
    {"clave": "losa_aligerada", "nombre": "Losa aligerada", "especialidad": "estructuras",
     "dimensiones": ["largo", "ancho", "altura"], "partidas": ["concreto", "encofrado", "acero", "ladrillo_techo"]},
    {"clave": "escalera", "nombre": "Escalera", "especialidad": "estructuras",
     "dimensiones": ["ancho", "n_pasos", "paso", "contrapaso", "garganta"], "partidas": ["concreto", "encofrado", "acero"]},
    {"clave": "muro_contencion", "nombre": "Muro de contención", "especialidad": "estructuras",
     "dimensiones": ["longitud", "espesor", "altura"], "partidas": ["concreto", "encofrado", "acero"]},
    {"clave": "platea", "nombre": "Platea de cimentación", "especialidad": "estructuras",
     "dimensiones": ["largo", "ancho", "espesor"], "partidas": ["concreto", "encofrado", "acero"]},
    {"clave": "muro", "nombre": "Muro de albañilería", "especialidad": "arquitectura",
     "dimensiones": ["longitud", "altura", "espesor"], "partidas": ["albanileria", "tarrajeo", "pintura"]},
    {"clave": "puerta", "nombre": "Puerta", "especialidad": "arquitectura",
     "dimensiones": ["ancho", "alto"], "partidas": ["carpinteria", "cerrajeria", "pintura"]},
    {"clave": "ventana", "nombre": "Ventana", "especialidad": "arquitectura",
     "dimensiones": ["ancho", "alto"], "partidas": ["carpinteria", "vidrio"]},
    {"clave": "ambiente", "nombre": "Ambiente", "especialidad": "arquitectura",
     "dimensiones": ["largo", "ancho", "altura"], "partidas": ["piso", "contrapiso", "cielorraso", "contrazocalo"]},
    {"clave": "tuberia", "nombre": "Tubería", "especialidad": "sanitarias",
     "dimensiones": ["longitud", "diametro"], "partidas": ["red"]},
    {"clave": "aparato_sanitario", "nombre": "Aparato sanitario", "especialidad": "sanitarias",
     "dimensiones": [], "partidas": ["aparato"]},
    {"clave": "salida_electrica", "nombre": "Salida eléctrica", "especialidad": "electricas",
     "dimensiones": [], "partidas": ["salida"]},
    {"clave": "luminaria", "nombre": "Luminaria", "especialidad": "electricas",
     "dimensiones": [], "partidas": ["artefacto"]},
    {"clave": "ducto", "nombre": "Ducto HVAC", "especialidad": "mecanicas",
     "dimensiones": ["longitud", "ancho", "alto"], "partidas": ["ducto", "aislamiento"]},
]

TIPOS_POR_CLAVE = {t["clave"]: t for t in TIPOS_ELEMENTO}
