"""Reportes y exportaciones: Excel, PDF y CSV."""
from __future__ import annotations

import csv
import io
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from reportlab.lib.units import mm
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import audit, security, servicios
from ..db import obtener_sesion
from ..export import excel, pdf
from ..models import Observacion, Usuario
from ..motor import costos, validaciones
from ..motor.redondeo import dec
from .calidad import revisar
from .presupuesto import lista_insumos
from .proyectos import _publico, obtener

router = APIRouter(tags=["reportes"])

REPORTES = {
    "metrados": "Planilla de metrados",
    "resumen": "Resumen de metrados",
    "presupuesto": "Presupuesto",
    "insumos": "Lista de insumos",
    "acero": "Cuadro de acero",
    "observaciones": "Reporte de observaciones",
    "calidad": "Reporte de control de calidad",
    "comparacion": "Comparación de versiones",
    "trazabilidad": "Reporte de trazabilidad",
}


@router.get("/reportes")
def catalogo_reportes():
    return {"reportes": [{"clave": k, "nombre": v,
                          "formatos": ["xlsx", "pdf", "csv"]} for k, v in REPORTES.items()]}


def _respuesta(contenido: bytes, nombre: str, formato: str) -> Response:
    tipos = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf",
        "csv": "text/csv; charset=utf-8",
    }
    return Response(
        content=contenido, media_type=tipos[formato],
        headers={"Content-Disposition":
                 f"attachment; filename*=UTF-8''{quote(nombre)}"},
    )


def _csv(encabezados: list[str], filas: list[list]) -> bytes:
    buffer = io.StringIO()
    escritor = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    escritor.writerow(encabezados)
    for f in filas:
        escritor.writerow(["" if c is None else c for c in f])
    return buffer.getvalue().encode("utf-8-sig")


@router.get("/proyectos/{proyecto_id}/exportar/{reporte}")
def exportar(proyecto_id: str, reporte: str,
             formato: str = Query(default="xlsx", pattern="^(xlsx|pdf|csv)$"),
             version_id: str | None = None, especialidad: str | None = None,
             solo_observadas: bool = False, comparar_con: str | None = None,
             db: Session = Depends(obtener_sesion),
             usuario: Usuario = Depends(security.usuario_actual)):
    p = obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "exportar")
    if reporte not in REPORTES:
        raise HTTPException(404, f"Reporte desconocido. Disponibles: {', '.join(REPORTES)}")

    version_id = version_id or p.version_actual_id
    datos = servicios.arbol(db, p, version_id=version_id, con_filas=True)
    db.commit()
    nodos = servicios.aplanar(datos["items"])

    if especialidad:
        nodos = [n for n in nodos if n["tipo"] == "titulo" or n["especialidad"] == especialidad]
    if solo_observadas:
        nodos = [n for n in nodos if n["tipo"] == "partida" and n["estado"] == "observado"]

    filtros = " · ".join(x for x in [
        f"Especialidad: {especialidad}" if especialidad else None,
        "Solo partidas observadas" if solo_observadas else None,
    ] if x)

    proyecto = _publico(p)
    sello = datetime.now().strftime("%Y%m%d-%H%M")
    base = f"{p.codigo or p.id}-{reporte}-{sello}"
    constructor = _CONSTRUCTORES[reporte]
    contenido, nombre = constructor(
        db=db, usuario=usuario, proyecto=proyecto, proyecto_id=proyecto_id,
        nodos=nodos, datos=datos, formato=formato, base=base,
        version_id=version_id, comparar_con=comparar_con, filtros=filtros, p=p)

    audit.registrar(db, accion="exportar" if False else "editar", entidad="reporte",
                    entidad_id=reporte, proyecto_id=proyecto_id,
                    resumen=f"Exportó {REPORTES[reporte]} en {formato.upper()}",
                    usuario=usuario, commit=True)
    return _respuesta(contenido, nombre, formato)


# --------------------------------------------------------------------------- #
# Constructores por reporte
# --------------------------------------------------------------------------- #

def _metrados(*, proyecto, nodos, usuario, formato, base, version_id, filtros, **_):
    if formato == "xlsx":
        return excel.planilla_metrados(proyecto, nodos, usuario.nombre, version_id,
                                       filtros), f"{base}.xlsx"
    encabezados = ["ÍTEM", "DESCRIPCIÓN", "UND.", "CANT.", "VECES", "LARGO", "ANCHO",
                   "ALTO", "PARCIAL", "LÁMINA"]
    filas = []
    for n in nodos:
        if n["tipo"] == "titulo":
            filas.append([f"§{n['item']}", n["descripcion"].upper(), "", "", "", "", "", "", "", ""])
            continue
        filas.append([f"§{n['item']}", n["descripcion"], n.get("unidad"), "", "", "", "", "",
                      n.get("metrado"), ""])
        for f in n.get("filas") or []:
            filas.append(["", f.get("descripcion") or "", "", f.get("n") or "",
                          f.get("veces") or "", f.get("largo") or "", f.get("ancho") or "",
                          f.get("alto") or "", f.get("parcial") or "", f.get("lamina") or ""])
    if formato == "csv":
        return _csv(encabezados, filas), f"{base}.csv"
    anchos = [18, 92, 14, 16, 16, 18, 18, 18, 22, 20]
    return pdf.reporte("Planilla de metrados", proyecto, encabezados, filas,
                       [a * mm for a in anchos], usuario.nombre, version_id, filtros,
                       alineacion_derecha={3, 4, 5, 6, 7, 8}, marcar_titulos=True), f"{base}.pdf"


def _resumen(*, proyecto, nodos, usuario, formato, base, version_id, filtros, **_):
    encabezados = ["ÍTEM", "CÓDIGO", "DESCRIPCIÓN", "UND.", "METRADO", "ESPECIALIDAD", "ESTADO"]
    filas = [[n["item"], n.get("codigo") or "", n["descripcion"], n.get("unidad"),
              n.get("metrado"), n.get("especialidad"), n.get("estado")]
             for n in nodos if n["tipo"] == "partida"]
    if formato == "csv":
        return _csv(encabezados, filas), f"{base}.csv"
    if formato == "xlsx":
        return excel.generico("Resumen de metrados", proyecto, encabezados, filas,
                              usuario.nombre, [12, 16, 70, 10, 14, 22, 14]), f"{base}.xlsx"
    return pdf.reporte("Resumen de metrados", proyecto, encabezados, filas,
                       [18 * mm, 22 * mm, 110 * mm, 14 * mm, 24 * mm, 32 * mm, 22 * mm],
                       usuario.nombre, version_id, filtros,
                       alineacion_derecha={4}), f"{base}.pdf"


def _presupuesto(*, db, p, proyecto, nodos, datos, usuario, formato, base, version_id, **_):
    reglas_proyecto = p.reglas or {}
    impuesto = reglas_proyecto.get("impuesto") or {"nombre": "IGV", "tasa": "18"}
    pie = costos.resumen(datos["costo_directo"],
                         gg_pct=reglas_proyecto.get("gastos_generales_pct", 0),
                         utilidad_pct=reglas_proyecto.get("utilidad_pct", 0),
                         impuesto_pct=impuesto.get("tasa", 0),
                         nombre_impuesto=impuesto.get("nombre", "IGV"),
                         reglas=servicios.reglas_de(p))
    if formato == "xlsx":
        return excel.presupuesto(proyecto, nodos, pie, usuario.nombre,
                                 version_id), f"{base}.xlsx"
    encabezados = ["ÍTEM", "DESCRIPCIÓN", "UND.", "METRADO", "P.U.", "PARCIAL"]
    filas = []
    for n in nodos:
        if n["tipo"] == "titulo":
            filas.append([f"§{n['item']}", n["descripcion"].upper(), "", "", "", n.get("parcial")])
        else:
            filas.append([n["item"], n["descripcion"], n.get("unidad"), n.get("metrado"),
                          n.get("precio_unitario") or "0.00", n.get("parcial")])
    if formato == "csv":
        return _csv(encabezados, filas), f"{base}.csv"
    totales = [("Costo directo", pie["costo_directo"]),
               (f"Gastos generales ({pie['gastos_generales_pct']}%)", pie["gastos_generales"]),
               (f"Utilidad ({pie['utilidad_pct']}%)", pie["utilidad"]),
               ("Subtotal", pie["subtotal"]),
               (f"{pie['nombre_impuesto']} ({pie['impuesto_pct']}%)", pie["impuesto"]),
               ("TOTAL DEL PRESUPUESTO", pie["total"])]
    return pdf.reporte("Presupuesto de obra", proyecto, encabezados, filas,
                       [18 * mm, 118 * mm, 14 * mm, 26 * mm, 26 * mm, 30 * mm],
                       usuario.nombre, version_id, "", alineacion_derecha={3, 4, 5},
                       pie_extra=pdf.bloque_totales(totales),
                       marcar_titulos=True), f"{base}.pdf"


def _insumos(*, db, proyecto_id, proyecto, usuario, formato, base, **_):
    datos = lista_insumos(proyecto_id, db=db, usuario=usuario)
    encabezados = ["TIPO", "DESCRIPCIÓN", "UND.", "CANTIDAD", "PRECIO", "PARCIAL"]
    filas = [[i["tipo"], i["descripcion"], i["unidad"], i["cantidad"], i["precio"], i["parcial"]]
             for i in datos["insumos"]]
    if formato == "csv":
        return _csv(encabezados, filas), f"{base}.csv"
    if formato == "xlsx":
        return excel.generico("Lista de insumos", proyecto, encabezados, filas,
                              usuario.nombre, [10, 66, 10, 16, 14, 16]), f"{base}.xlsx"
    return pdf.reporte("Lista de insumos", proyecto, encabezados, filas,
                       [16 * mm, 120 * mm, 14 * mm, 26 * mm, 24 * mm, 26 * mm],
                       usuario.nombre, None, "", alineacion_derecha={3, 4, 5}), f"{base}.pdf"


def _acero(*, nodos, proyecto, usuario, formato, base, **_):
    from ..motor import acero as motor_acero
    barras = []
    for n in nodos:
        if n["tipo"] != "partida" or n.get("unidad") != "kg":
            continue
        for f in n.get("filas") or []:
            variables = f.get("variables") or {}
            if variables.get("diametro"):
                barras.append({**variables, "elemento": n["descripcion"],
                               "marca": f.get("descripcion")})
    cuadro = motor_acero.cuadro(barras)
    encabezados = ["MARCA", "ELEMENTO", "Ø", "N°", "LONG. UNIT. (m)",
                   "LONG. TOTAL (m)", "PESO UNIT. (kg/m)", "PESO (kg)"]
    filas = [[b["marca"], b["elemento"], b["diametro"], b["cantidad"],
              b["longitud_unitaria"], b["longitud_total"], b["peso_unitario"], b["peso"]]
             for b in cuadro["barras"]]
    for r in cuadro["resumen_por_diametro"]:
        filas.append(["§RESUMEN", f"Total Ø {r['diametro']}", r["diametro"], r["cantidad"],
                      "", r["longitud_total"], r["peso_unitario"], r["peso"]])
    filas.append(["§TOTAL", "PESO TOTAL DE ACERO", "", "", "", "", "", cuadro["peso_total"]])
    if formato == "csv":
        return _csv(encabezados, filas), f"{base}.csv"
    if formato == "xlsx":
        return excel.generico("Cuadro de acero", proyecto, encabezados, filas,
                              usuario.nombre, [12, 46, 10, 8, 16, 16, 16, 14]), f"{base}.xlsx"
    return pdf.reporte("Cuadro de acero", proyecto, encabezados, filas,
                       [20 * mm, 76 * mm, 16 * mm, 14 * mm, 28 * mm, 28 * mm, 30 * mm, 24 * mm],
                       usuario.nombre, None, "", alineacion_derecha={3, 4, 5, 6, 7},
                       marcar_titulos=True), f"{base}.pdf"


def _observaciones(*, db, proyecto_id, proyecto, usuario, formato, base, **_):
    filas_db = list(db.scalars(select(Observacion)
                               .where(Observacion.proyecto_id == proyecto_id)
                               .order_by(Observacion.creado_en.desc())))
    autores = {u.id: u.nombre for u in db.scalars(select(Usuario))}
    encabezados = ["FECHA", "GRAVEDAD", "TIPO", "ESTADO", "OBSERVACIÓN", "AUTOR"]
    filas = [[o.creado_en.strftime("%d/%m/%Y") if o.creado_en else "", o.gravedad, o.tipo,
              o.estado, o.texto, autores.get(o.autor, "—")] for o in filas_db]
    if formato == "csv":
        return _csv(encabezados, filas), f"{base}.csv"
    if formato == "xlsx":
        return excel.generico("Observaciones", proyecto, encabezados, filas,
                              usuario.nombre, [12, 12, 16, 12, 80, 20]), f"{base}.xlsx"
    return pdf.reporte("Reporte de observaciones", proyecto, encabezados, filas,
                       [22 * mm, 22 * mm, 26 * mm, 22 * mm, 130 * mm, 30 * mm],
                       usuario.nombre, None, ""), f"{base}.pdf"


def _calidad(*, db, proyecto_id, proyecto, usuario, formato, base, version_id, **_):
    resultado = revisar(proyecto_id, version_id=version_id, db=db, usuario=usuario)
    encabezados = ["GRAVEDAD", "TIPO", "TÍTULO", "DETALLE", "CÓMO SE CORRIGE", "NORMA"]
    filas = [[a["gravedad"].upper(), a["tipo"], a["titulo"], a["detalle"], a["solucion"],
              a.get("referencia") or ""] for a in resultado["alertas"]]
    if formato == "csv":
        return _csv(encabezados, filas), f"{base}.csv"
    if formato == "xlsx":
        return excel.generico("Control de calidad", proyecto, encabezados, filas,
                              usuario.nombre, [12, 20, 34, 60, 60, 16]), f"{base}.xlsx"
    return pdf.reporte("Reporte de control de calidad", proyecto, encabezados, filas,
                       [20 * mm, 28 * mm, 44 * mm, 76 * mm, 76 * mm, 22 * mm],
                       usuario.nombre, version_id, ""), f"{base}.pdf"


def _comparacion(*, db, proyecto_id, proyecto, usuario, formato, base, version_id,
                 comparar_con, **_):
    if not comparar_con:
        raise HTTPException(400, "Indique con qué versión comparar (parámetro comparar_con).")
    from .proyectos import comparar_versiones
    resultado = comparar_versiones(proyecto_id, a=comparar_con, b=version_id,
                                   db=db, usuario=usuario)
    encabezados = ["ÍTEM", "DESCRIPCIÓN", "UND.", "VERSIÓN A", "VERSIÓN B",
                   "DIFERENCIA", "ESTADO"]
    filas = [[c["item"], c["descripcion"], c.get("unidad"), c.get("metrado_a"),
              c.get("metrado_b"), c.get("diferencia"), c["estado"].upper()]
             for c in resultado["comparacion"]]
    if formato == "csv":
        return _csv(encabezados, filas), f"{base}.csv"
    if formato == "xlsx":
        return excel.generico("Comparación de versiones", proyecto, encabezados, filas,
                              usuario.nombre, [12, 60, 10, 16, 16, 16, 16]), f"{base}.xlsx"
    return pdf.reporte("Comparación de versiones", proyecto, encabezados, filas,
                       [18 * mm, 106 * mm, 14 * mm, 26 * mm, 26 * mm, 26 * mm, 26 * mm],
                       usuario.nombre, version_id, f"Versión A: {comparar_con}",
                       alineacion_derecha={3, 4, 5}), f"{base}.pdf"


def _trazabilidad(*, nodos, proyecto, usuario, formato, base, version_id, **_):
    encabezados = ["ÍTEM", "PARTIDA", "FILA", "CÁLCULO", "PARCIAL", "ORIGEN",
                   "LÁMINA", "RESPONSABLE", "FECHA"]
    filas = []
    for n in nodos:
        if n["tipo"] != "partida":
            continue
        for f in n.get("filas") or []:
            filas.append([n["item"], n["descripcion"], f.get("descripcion") or "",
                          f.get("sustento") or "", f.get("parcial") or "",
                          f.get("origen") or "", f.get("lamina") or "",
                          f.get("responsable") or "", f.get("fecha") or ""])
    if formato == "csv":
        return _csv(encabezados, filas), f"{base}.csv"
    if formato == "xlsx":
        return excel.generico("Trazabilidad", proyecto, encabezados, filas,
                              usuario.nombre, [12, 40, 30, 34, 12, 14, 12, 18, 12]), f"{base}.xlsx"
    return pdf.reporte("Reporte de trazabilidad", proyecto, encabezados, filas,
                       [16 * mm, 60 * mm, 44 * mm, 52 * mm, 20 * mm, 22 * mm,
                        18 * mm, 26 * mm, 20 * mm],
                       usuario.nombre, version_id, "",
                       alineacion_derecha={4}), f"{base}.pdf"


_CONSTRUCTORES = {
    "metrados": _metrados, "resumen": _resumen, "presupuesto": _presupuesto,
    "insumos": _insumos, "acero": _acero, "observaciones": _observaciones,
    "calidad": _calidad, "comparacion": _comparacion, "trazabilidad": _trazabilidad,
}
