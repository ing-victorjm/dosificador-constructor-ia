"""Asistente del proyecto.

Reglas de conducta, no negociables:

1. **Nunca modifica sin confirmar.** Toda instrucción que cambie datos devuelve
   una PROPUESTA con lo que haría; el cambio ocurre solo cuando el usuario
   confirma explícitamente.
2. **Siempre cita la fuente.** Cada cantidad que muestra dice si es un dato
   detectado, ingresado por una persona o un supuesto, y de qué plano sale.
3. **No inventa.** Si falta un dato para responder, lo pide; no lo estima en
   silencio.

Funciona sin conexión con un motor de intenciones determinista sobre los datos
reales del proyecto. `_LLM` deja preparado el enganche con un modelo de lenguaje
para cuando se configure una clave.
"""
from __future__ import annotations

import os
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import security, servicios
from ..db import obtener_sesion
from ..models import Elemento, Item, Ubicacion, Usuario, Version
from ..motor import acero, normas, plantillas
from ..motor.redondeo import dec
from .proyectos import obtener

router = APIRouter(tags=["asistente"])

_LLM = os.environ.get("METRA_LLM_API_KEY")   # sin clave, el asistente es determinista


def _limpiar(t: str) -> str:
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


EJEMPLOS = [
    "Busca elementos que todavía no fueron metrados",
    "Genera el resumen de acero por diámetro",
    "Explícame de dónde sale el metrado de la partida 02.03",
    "Compara la versión v1 con la versión v2",
    "Descuenta los vanos mayores a 0.50 m2",
    "Crea una plantilla de metrados para una vivienda de tres pisos",
    "Exporta únicamente las partidas observadas",
    "¿Qué partidas están sin metrar?",
    "¿Cuánto suma el concreto?",
]


class Pregunta(BaseModel):
    texto: str
    proyecto_id: str | None = None
    item_id: str | None = None


class Confirmacion(BaseModel):
    accion: str
    proyecto_id: str
    parametros: dict = {}


@router.get("/asistente/ejemplos")
def ejemplos():
    return {"ejemplos": EJEMPLOS, "modo": "modelo" if _LLM else "determinista",
            "aviso": "El asistente pide confirmación antes de modificar, eliminar, "
                     "reemplazar o aprobar cualquier dato."}


@router.post("/asistente")
def preguntar(pregunta: Pregunta, db: Session = Depends(obtener_sesion),
              usuario: Usuario = Depends(security.usuario_actual)):
    texto = _limpiar(pregunta.texto)
    if not texto.strip():
        return _respuesta("Escriba qué necesita. Por ejemplo: " + EJEMPLOS[0])

    if not pregunta.proyecto_id:
        return _respuesta(
            "Abra un proyecto para que pueda trabajar sobre sus datos reales. "
            "Sin proyecto no tengo de dónde sacar cantidades, y no voy a inventarlas.")

    p = obtener(db, pregunta.proyecto_id)
    security.exigir(db, usuario, p.id, "ver")

    for detectar, resolver in _INTENCIONES:
        if detectar(texto):
            return resolver(texto, p, db, usuario, pregunta)

    return _respuesta(
        "No reconocí la instrucción. Puedo ayudarle con estas cosas:",
        sugerencias=EJEMPLOS)


def _respuesta(texto: str, *, datos=None, acciones=None, citas=None,
               tabla=None, sugerencias=None) -> dict:
    return {
        "respuesta": texto,
        "datos": datos,
        "tabla": tabla,
        "acciones": acciones or [],
        "citas": citas or [],
        "sugerencias": sugerencias or [],
    }


# --------------------------------------------------------------------------- #
# Intenciones
# --------------------------------------------------------------------------- #

def _partidas(db, p, con_filas=False):
    datos = servicios.arbol(db, p, con_filas=con_filas)
    db.commit()
    return [n for n in servicios.aplanar(datos["items"]) if n["tipo"] == "partida"], datos


def _sin_metrar(texto, p, db, usuario, _pregunta):
    partidas, _ = _partidas(db, p)
    faltan = [n for n in partidas if (n.get("resumen") or {}).get("origen") == "vacio"]
    elementos = list(db.scalars(select(Elemento).where(Elemento.proyecto_id == p.id,
                                                       Elemento.metrado.is_(False))))
    if not faltan and not elementos:
        return _respuesta("Todas las partidas del proyecto tienen sustento y no hay "
                          "elementos registrados sin metrar. Buen estado.")
    tabla = {
        "columnas": ["Ítem", "Partida", "Unidad", "Especialidad"],
        "filas": [[n["item"], n["descripcion"], n.get("unidad"), n.get("especialidad")]
                  for n in faltan[:60]],
    }
    extra = (f" Además hay {len(elementos)} elemento(s) registrados que ninguna partida "
             "usa todavía.") if elementos else ""
    return _respuesta(
        f"Encontré {len(faltan)} partida(s) sin ninguna fila de metrado.{extra} "
        "Ninguna cantidad fue asumida: están vacías de verdad.",
        tabla=tabla,
        acciones=[{"tipo": "ir", "descripcion": "Abrir la hoja de metrados filtrada",
                   "ruta": f"#/proyecto/{p.id}/metrados"}])


def _resumen_acero(texto, p, db, usuario, _pregunta):
    partidas, _ = _partidas(db, p, con_filas=True)
    barras = []
    for n in partidas:
        if n.get("unidad") != "kg":
            continue
        for f in n.get("filas") or []:
            variables = f.get("variables") or {}
            if variables.get("diametro"):
                barras.append({**variables, "elemento": n["descripcion"],
                               "marca": f.get("descripcion")})
    if not barras:
        return _respuesta(
            "No hay barras despiezadas todavía. El resumen de acero se arma del despiece "
            "(diámetro, longitud, ganchos, traslapes y cantidad), no de un ratio kg/m³.",
            citas=[{"texto": normas.REGLA_KG_M3["aviso"], "etiqueta": normas.COSTUMBRE_OBRA}])
    cuadro = acero.cuadro(barras)
    return _respuesta(
        f"Resumen de acero por diámetro. Peso total: {cuadro['peso_total']} kg "
        f"({len(cuadro['barras'])} barras despiezadas"
        + (f", {cuadro['barras_incompletas']} incompletas" if cuadro["barras_incompletas"] else "")
        + ").",
        tabla={"columnas": ["Diámetro", "Cantidad", "Longitud total (m)", "Peso (kg)"],
               "filas": [[r["diametro"], r["cantidad"], r["longitud_total"], r["peso"]]
                         for r in cuadro["resumen_por_diametro"]]},
        datos=cuadro,
        citas=[{"texto": normas.REGLA_ARRANQUES["explicacion"], "etiqueta": normas.NORMA}])


def _explicar(texto, p, db, usuario, pregunta):
    item = None
    if pregunta.item_id:
        item = db.get(Item, pregunta.item_id)
    else:
        codigo = re.search(r"\b(\d{2}(?:\.\d{2})+)\b", texto)
        partidas, _ = _partidas(db, p)
        if codigo:
            objetivo = next((n for n in partidas if n["item"] == codigo.group(1)), None)
            item = db.get(Item, objetivo["id"]) if objetivo else None
        if not item:
            palabras = [w for w in texto.split() if len(w) > 4]
            objetivo = next((n for n in partidas
                             if any(w in _limpiar(n["descripcion"]) for w in palabras)), None)
            item = db.get(Item, objetivo["id"]) if objetivo else None

    if not item:
        return _respuesta(
            "Dígame qué partida quiere que le explique: puede darme su número de ítem "
            "(por ejemplo 02.03.01) o parte de su descripción.")

    from .metrados import trazabilidad
    traza = trazabilidad(item.id, db=db, usuario=usuario)
    resumen = traza["resumen"]
    lineas = [
        f"«{item.descripcion}» suma {resumen['total']} {item.unidad or ''}.",
        f"Sale de {resumen['filas_ok']} fila(s) de sustento.",
    ]
    if resumen["deducciones"] and dec(resumen["deducciones"]) != 0:
        lineas.append(f"Incluye {resumen['deducciones']} de deducciones sobre un bruto de "
                      f"{resumen['bruto']}.")
    if resumen["filas_incompletas"]:
        lineas.append(f"Atención: {resumen['filas_incompletas']} fila(s) sin calcular por "
                      "datos faltantes. Ese total está incompleto.")
    origenes = ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in traza["origenes"].items())
    if origenes:
        lineas.append(f"Origen de las filas: {origenes}.")

    citas = []
    if item.regla_medicion:
        citas.append({"texto": item.regla_medicion, "codigo": item.codigo,
                      "etiqueta": item.etiqueta_fuente or normas.NORMA})
    return _respuesta(
        " ".join(lineas),
        tabla={"columnas": ["Fila", "Cálculo", "Parcial", "Origen", "Lámina"],
               "filas": [[d["descripcion"] or "—", d["sustento"], d["parcial"],
                          d["origen"], d["lamina"] or "—"] for d in traza["detalle"]]},
        datos=traza, citas=citas)


def _comparar(texto, p, db, usuario, _pregunta):
    versiones = list(db.scalars(select(Version).where(Version.proyecto_id == p.id)
                                .order_by(Version.numero)))
    if len(versiones) < 2:
        return _respuesta(
            "El proyecto tiene una sola versión. Cree una nueva versión para poder comparar: "
            "al hacerlo, la actual queda congelada como referencia.")
    encontradas = re.findall(r"v?\s?(\d+)", texto)
    numeros = [int(x) for x in encontradas if x.isdigit()][:2]
    a = next((v for v in versiones if v.numero == numeros[0]), versiones[-2]) if numeros else versiones[-2]
    b = next((v for v in versiones if v.numero == numeros[1]), versiones[-1]) if len(numeros) > 1 else versiones[-1]

    from .proyectos import comparar_versiones
    resultado = comparar_versiones(p.id, a=a.id, b=b.id, db=db, usuario=usuario)
    r = resultado["resumen"]
    return _respuesta(
        f"Comparación de {a.nombre} contra {b.nombre}: {r['modificadas']} partida(s) "
        f"modificadas, {r['agregadas']} agregadas y {r['eliminadas']} eliminadas.",
        tabla={"columnas": ["Ítem", "Partida", "Und.", a.nombre, b.nombre, "Diferencia", "Estado"],
               "filas": [[c["item"], c["descripcion"], c.get("unidad"), c.get("metrado_a"),
                          c.get("metrado_b"), c.get("diferencia"), c["estado"]]
                         for c in resultado["comparacion"][:80]]},
        datos=resultado)


def _vanos(texto, p, db, usuario, _pregunta):
    umbral = re.search(r"(\d+[.,]?\d*)\s*m2?", texto)
    valor = umbral.group(1).replace(",", ".") if umbral else None
    aviso = []
    if valor and dec(valor) == dec("2.00"):
        aviso.append(normas.UMBRAL_MITO["aviso"])
    familias = "\n".join(
        f"· {f.nombre}: {'descuenta todo vano' if f.umbral_m2 == 0 else f'descuenta desde {f.umbral_m2} m²'}"
        f" ({f.codigo})"
        for f in normas.FAMILIAS.values() if f.descuenta)
    return _respuesta(
        ("El descuento de vanos no se decide con un umbral único: depende de la familia de la "
         "partida.\n\n" + familias +
         ("\n\n" + " ".join(aviso) if aviso else "") +
         "\n\nAbra la partida y use «Descontar vanos»: METRA AI aplicará el umbral que "
         "corresponde y dejará escrito, vano por vano, por qué se descontó o no."),
        citas=[{"texto": f.cita, "codigo": f.codigo, "etiqueta": f.etiqueta}
               for f in normas.FAMILIAS.values() if f.descuenta],
        acciones=[{"tipo": "ir", "descripcion": "Ir a la hoja de metrados",
                   "ruta": f"#/proyecto/{p.id}/metrados"}])


def _plantilla(texto, p, db, usuario, _pregunta):
    clave = "edificacion"
    if "estructura" in texto and "acabado" not in texto:
        clave = "estructuras"
    elif "acabado" in texto or "arquitectura" in texto:
        clave = "acabados"
    plantilla = plantillas.PLANTILLAS[clave]
    pisos = re.search(r"(\d+)\s*piso", texto)
    n = int(pisos.group(1)) if pisos else p.pisos

    existentes = db.scalar(select(Item).where(Item.proyecto_id == p.id))
    advertencia = (" El proyecto YA tiene partidas: la plantilla se agregará al final, "
                   "sin borrar nada.") if existentes else ""
    return _respuesta(
        f"Puedo volcar la plantilla «{plantilla['nombre']}»: "
        f"{plantillas.contar(plantilla['arbol'])} partidas enlazadas a los códigos reales de "
        f"la norma, organizadas por especialidad.{advertencia}\n\n"
        f"El proyecto tiene {n} piso(s); después podrá repetir las filas de un piso típico "
        "a los demás niveles con un clic. ¿Lo aplico?",
        acciones=[{
            "tipo": "confirmar",
            "accion": "aplicar_plantilla",
            "descripcion": f"Aplicar «{plantilla['nombre']}» ({plantillas.contar(plantilla['arbol'])} partidas)",
            "parametros": {"clave": clave},
            "requiere_confirmacion": True,
        }])


def _exportar(texto, p, db, usuario, _pregunta):
    solo_observadas = "observ" in texto
    formato = "pdf" if "pdf" in texto else "xlsx"
    reporte = "presupuesto" if "presupuesto" in texto else (
        "acero" if "acero" in texto else (
            "calidad" if "calidad" in texto else "metrados"))
    ruta = (f"/api/proyectos/{p.id}/exportar/{reporte}?formato={formato}"
            + ("&solo_observadas=true" if solo_observadas else ""))
    return _respuesta(
        f"Listo para exportar {'solo las partidas observadas' if solo_observadas else 'la planilla completa'} "
        f"en {formato.upper()}. El archivo lleva portada, filtros aplicados, versión, "
        "responsable y espacio de firmas.",
        acciones=[{"tipo": "descargar", "descripcion": f"Descargar {reporte} ({formato})",
                   "ruta": ruta}])


def _totales(texto, p, db, usuario, _pregunta):
    partidas, datos = _partidas(db, p)
    palabras = [w for w in re.findall(r"[a-z]{5,}", texto)
                if w not in ("cuanto", "cuanta", "suman", "total", "partida", "partidas")]
    filtradas = [n for n in partidas
                 if not palabras or any(w in _limpiar(n["descripcion"]) for w in palabras)]
    if not filtradas:
        return _respuesta("No encontré partidas que coincidan con esa descripción.")
    por_unidad: dict[str, list] = {}
    for n in filtradas:
        por_unidad.setdefault(n.get("unidad") or "—", []).append(n)
    lineas = []
    for unidad, grupo in por_unidad.items():
        total = sum(dec(n.get("metrado") or 0) for n in grupo)
        lineas.append(f"{total} {unidad} en {len(grupo)} partida(s)")
    return _respuesta(
        "Suma de lo que coincide: " + "; ".join(lineas) +
        ". Las unidades no se mezclan: sumar m² con m³ sería un error de metrado.",
        tabla={"columnas": ["Ítem", "Partida", "Und.", "Metrado"],
               "filas": [[n["item"], n["descripcion"], n.get("unidad"), n.get("metrado")]
                         for n in filtradas[:60]]})


def _metrar_elementos(texto, p, db, usuario, _pregunta):
    ubicaciones = list(db.scalars(select(Ubicacion).where(Ubicacion.proyecto_id == p.id)))
    nombres = [u.nombre for u in ubicaciones]
    return _respuesta(
        "Para metrar automáticamente necesito las dimensiones reales, y no las voy a suponer. "
        "Dos caminos honestos:\n\n"
        "1. Registre los elementos (muro, columna, zapata) con sus medidas en «Elementos»: "
        "de cada uno salen sus partidas de concreto, encofrado y acero.\n"
        "2. Mida sobre el plano calibrado: cada trazo crea la fila de sustento con su lámina.\n\n"
        f"Ubicaciones disponibles en este proyecto: {', '.join(nombres[:12]) or 'ninguna todavía'}.",
        acciones=[
            {"tipo": "ir", "descripcion": "Registrar elementos",
             "ruta": f"#/proyecto/{p.id}/elementos"},
            {"tipo": "ir", "descripcion": "Abrir el visor de planos",
             "ruta": f"#/proyecto/{p.id}/planos"},
        ])


def _calidad(texto, p, db, usuario, _pregunta):
    from .calidad import revisar
    resultado = revisar(p.id, db=db, usuario=usuario)
    r = resultado["resumen"]
    if not r["total"]:
        return _respuesta("El control de calidad no encontró incidencias. "
                          f"Se revisaron {resultado['revisadas']['partidas']} partidas.")
    return _respuesta(
        f"El control de calidad encontró {r['total']} incidencia(s): "
        f"{r['por_gravedad']['alta']} de gravedad alta, {r['por_gravedad']['media']} media y "
        f"{r['por_gravedad']['baja']} baja.",
        tabla={"columnas": ["Gravedad", "Título", "Detalle", "Cómo se corrige"],
               "filas": [[a["gravedad"], a["titulo"], a["detalle"], a["solucion"]]
                         for a in resultado["alertas"][:40]]},
        acciones=[{"tipo": "ir", "descripcion": "Abrir control de calidad",
                   "ruta": f"#/proyecto/{p.id}/calidad"}])


def _contiene(*palabras):
    return lambda t: any(w in t for w in palabras)


_INTENCIONES = [
    (_contiene("no fueron metrad", "sin metrar", "falta metrar", "no metrad", "pendiente"),
     _sin_metrar),
    (_contiene("acero", "varilla", "diametro", "despiece"), _resumen_acero),
    (_contiene("de donde sale", "explica", "explicame", "trazabilidad", "sustento"), _explicar),
    (_contiene("compara", "version"), _comparar),
    (_contiene("vano", "descuenta", "descontar", "puerta y ventana"), _vanos),
    (_contiene("plantilla", "crea las partidas", "estructura de metrados"), _plantilla),
    (_contiene("exporta", "descarga", "excel", "reporte"), _exportar),
    (_contiene("calidad", "revisa", "errores", "inconsistencia", "alerta"), _calidad),
    (_contiene("metra ", "metrar", "calcula"), _metrar_elementos),
    (_contiene("cuanto", "cuanta", "suma", "total"), _totales),
]


# --------------------------------------------------------------------------- #
# Ejecución confirmada
# --------------------------------------------------------------------------- #

ACCIONES_PERMITIDAS = {"aplicar_plantilla"}


@router.post("/asistente/confirmar")
def confirmar(datos: Confirmacion, db: Session = Depends(obtener_sesion),
              usuario: Usuario = Depends(security.usuario_actual)):
    """Ejecuta una acción que el asistente propuso y el usuario aceptó."""
    if datos.accion not in ACCIONES_PERMITIDAS:
        raise HTTPException(400, f"Acción no permitida: {datos.accion}")
    p = obtener(db, datos.proyecto_id)
    security.exigir(db, usuario, p.id, "crear")

    if datos.accion == "aplicar_plantilla":
        clave = datos.parametros.get("clave", "edificacion")
        resultado = servicios.aplicar_plantilla(db, p, clave, usuario.id)
        from .. import audit
        audit.registrar(db, accion="crear", entidad="item", proyecto_id=p.id,
                        resumen=f"Plantilla aplicada por el asistente: {resultado['plantilla']}",
                        usuario=usuario, commit=True)
        mensaje = (f"Listo: {resultado['partidas']} partidas en "
                   f"{resultado['titulos']} capítulos.")
        if resultado["sin_codigo"]:
            mensaje += (f" {len(resultado['sin_codigo'])} quedaron sin código normativo porque "
                        "ese código no está en el catálogo cargado; se emiten por su nombre "
                        "literal, sin inventar códigos.")
        return _respuesta(mensaje, datos=resultado)

    raise HTTPException(400, "Acción no implementada.")
