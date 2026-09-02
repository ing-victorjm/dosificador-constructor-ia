"""Datos de referencia que la interfaz necesita para construirse.

Una sola llamada al arrancar: unidades, especialidades, reglas normativas con su
cita, plantillas de fórmula, países, roles y tipos de elemento.
"""
from __future__ import annotations

from fastapi import APIRouter

from ..motor import especialidades, formulas, normas, paises, tablas
from ..motor import unidades as u
from ..security import DESCRIPCION_ROLES, PERMISOS

router = APIRouter(tags=["referencia"])

TIPOS_PROYECTO = [
    {"clave": "vivienda", "nombre": "Vivienda unifamiliar"},
    {"clave": "edificio", "nombre": "Edificio multifamiliar"},
    {"clave": "comercio", "nombre": "Local comercial"},
    {"clave": "oficinas", "nombre": "Oficinas"},
    {"clave": "industria", "nombre": "Industria"},
    {"clave": "salud", "nombre": "Salud"},
    {"clave": "educacion", "nombre": "Educación"},
    {"clave": "carretera", "nombre": "Carretera"},
    {"clave": "saneamiento", "nombre": "Saneamiento"},
    {"clave": "habilitacion", "nombre": "Habilitación urbana"},
    {"clave": "otro", "nombre": "Otro"},
]

ETAPAS = [
    {"clave": "anteproyecto", "nombre": "Anteproyecto"},
    {"clave": "expediente", "nombre": "Expediente técnico"},
    {"clave": "licitacion", "nombre": "Licitación"},
    {"clave": "ejecucion", "nombre": "Ejecución"},
    {"clave": "liquidacion", "nombre": "Liquidación"},
]

ESTADOS_PARTIDA = [
    {"clave": "borrador", "nombre": "Borrador", "color": "#8593ab"},
    {"clave": "revisado", "nombre": "Revisado", "color": "#2563eb"},
    {"clave": "observado", "nombre": "Observado", "color": "#c07b10"},
    {"clave": "aprobado", "nombre": "Aprobado", "color": "#0d9463"},
]

ORIGENES = [
    {"clave": "ingresado", "nombre": "Ingresado a mano", "icono": "teclado",
     "descripcion": "El metrador escribió la dimensión."},
    {"clave": "medido_plano", "nombre": "Medido en el plano", "icono": "regla",
     "descripcion": "Sale de un trazo sobre el plano calibrado."},
    {"clave": "importado", "nombre": "Importado", "icono": "archivo",
     "descripcion": "Vino de Excel, CAD o BIM."},
    {"clave": "detectado_ia", "nombre": "Detectado por IA", "icono": "chispa",
     "descripcion": "Sugerencia automática. Requiere revisión y aprobación humana."},
    {"clave": "supuesto", "nombre": "Supuesto", "icono": "alerta",
     "descripcion": "No hay dato en el plano; se asumió un valor que debe justificarse."},
]


@router.get("/referencia")
def referencia():
    return {
        "unidades": u.catalogo(),
        "dimensiones": [u.LONGITUD, u.AREA, u.VOLUMEN, u.MASA, u.CONTEO, u.GLOBAL, u.TIEMPO],
        "especialidades": especialidades.ESPECIALIDADES,
        "tipos_elemento": especialidades.TIPOS_ELEMENTO,
        "plantillas_formula": formulas.PLANTILLAS,
        "funciones_formula": sorted(formulas.FUNCIONES),
        "reglas": normas.catalogo_reglas(),
        "paises": paises.todos(),
        "monedas": paises.MONEDAS_COMUNES,
        "tipos_proyecto": TIPOS_PROYECTO,
        "etapas": ETAPAS,
        "estados_partida": ESTADOS_PARTIDA,
        "origenes": ORIGENES,
        "roles": [{"clave": k, "nombre": k.capitalize(), "descripcion": v,
                   "permisos": sorted(PERMISOS.get(k, set()))}
                  for k, v in DESCRIPCION_ROLES.items()],
    }


@router.get("/referencia/tablas")
def inventario_tablas():
    """Qué tablas técnicas hay cargadas y cuántas filas verificadas tienen."""
    return {"tablas": tablas.inventario()}


@router.get("/referencia/tablas/{nombre}")
def ver_tabla(nombre: str):
    return {"nombre": nombre, "datos": tablas.cargar(nombre, [])}


@router.post("/formula/validar")
def validar_formula(datos: dict):
    """Valida una expresión y, si vienen variables, la evalúa mostrando el paso a paso."""
    expresion = datos.get("expresion") or datos.get("formula") or ""
    ok, error, variables = formulas.validar(expresion)
    salida = {"ok": ok, "error": error, "variables": variables}
    if ok and datos.get("variables"):
        salida["resultado"] = formulas.evaluar(expresion, datos["variables"]).a_dict()
    return salida
