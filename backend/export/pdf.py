"""Reportes en PDF: portada, datos del proyecto, tabla y espacio de firmas."""
from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

AZUL = colors.HexColor("#1D5BD8")
GRIS = colors.HexColor("#51607A")
GRIS_CLARO = colors.HexColor("#F4F6FB")
BORDE = colors.HexColor("#DFE5EF")
VERDE = colors.HexColor("#0D9463")

_base = getSampleStyleSheet()
E = {
    "titulo": ParagraphStyle("titulo", parent=_base["Title"], fontName="Helvetica-Bold",
                             fontSize=20, textColor=AZUL, alignment=TA_LEFT, spaceAfter=2),
    "subtitulo": ParagraphStyle("subtitulo", parent=_base["Normal"], fontName="Helvetica",
                                fontSize=11, textColor=GRIS, spaceAfter=10),
    "seccion": ParagraphStyle("seccion", parent=_base["Heading2"], fontName="Helvetica-Bold",
                              fontSize=11, textColor=AZUL, spaceBefore=10, spaceAfter=4),
    "texto": ParagraphStyle("texto", parent=_base["Normal"], fontName="Helvetica",
                            fontSize=8.5, leading=11),
    "celda": ParagraphStyle("celda", parent=_base["Normal"], fontName="Helvetica",
                            fontSize=7.5, leading=9.5),
    "celda_fuerte": ParagraphStyle("celda_fuerte", parent=_base["Normal"],
                                   fontName="Helvetica-Bold", fontSize=7.5, leading=9.5),
    "pie": ParagraphStyle("pie", parent=_base["Normal"], fontName="Helvetica",
                          fontSize=7, textColor=GRIS, alignment=TA_CENTER),
}


def _pie_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRIS)
    ancho, _alto = doc.pagesize
    canvas.drawString(15 * mm, 10 * mm, doc._metra_pie)
    canvas.drawRightString(ancho - 15 * mm, 10 * mm, f"Página {doc.page}")
    canvas.setStrokeColor(BORDE)
    canvas.line(15 * mm, 13 * mm, ancho - 15 * mm, 13 * mm)
    canvas.restoreState()


def _portada(proyecto: dict, titulo: str, usuario: str, version: str | None,
             filtros: str) -> list:
    datos = [
        ["Proyecto", proyecto.get("nombre") or "—"],
        ["Código", proyecto.get("codigo") or "—"],
        ["Cliente", proyecto.get("cliente") or "—"],
        ["Ubicación", proyecto.get("ubicacion_texto") or "—"],
        ["Responsable", proyecto.get("responsable") or "—"],
        ["Etapa", (proyecto.get("etapa") or "—").capitalize()],
        ["Normativa aplicada", proyecto.get("normativa") or "—"],
        ["Moneda", proyecto.get("moneda") or "—"],
        ["Versión", version or "—"],
        ["Filtros aplicados", filtros or "Ninguno"],
        ["Emitido por", usuario],
        ["Fecha de emisión", datetime.now().strftime("%d/%m/%Y %H:%M")],
    ]
    tabla = Table([[Paragraph(f"<b>{a}</b>", E["texto"]), Paragraph(str(b), E["texto"])]
                   for a, b in datos], colWidths=[45 * mm, 120 * mm])
    tabla.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, BORDE),
        ("BACKGROUND", (0, 0), (0, -1), GRIS_CLARO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return [
        Paragraph("METRA AI", E["titulo"]),
        Paragraph(titulo, E["subtitulo"]),
        Spacer(1, 4 * mm), tabla, Spacer(1, 6 * mm),
    ]


def _firmas() -> list:
    fila = [Paragraph("<br/><br/><br/>_____________________________<br/>"
                      "<font size=7>Elaboró — metrador<br/>Nombre / CIP / Fecha</font>",
                      E["celda"]),
            Paragraph("<br/><br/><br/>_____________________________<br/>"
                      "<font size=7>Revisó<br/>Nombre / CIP / Fecha</font>", E["celda"]),
            Paragraph("<br/><br/><br/>_____________________________<br/>"
                      "<font size=7>Aprobó — supervisor<br/>Nombre / CIP / Fecha</font>",
                      E["celda"])]
    tabla = Table([fila], colWidths=[60 * mm] * 3)
    tabla.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    return [Spacer(1, 10 * mm), KeepTogether([Paragraph("Firmas", E["seccion"]), tabla])]


def _tabla(encabezados: list[str], filas: list[list], anchos: list[float],
           alineacion_derecha: set[int] | None = None,
           marcar_titulos: bool = False) -> Table:
    derecha = alineacion_derecha or set()
    datos = [[Paragraph(f"<b>{h}</b>", ParagraphStyle(
        "th", parent=E["celda"], textColor=colors.white, fontName="Helvetica-Bold"))
        for h in encabezados]]
    estilos_fila = []
    for i, fila in enumerate(filas, start=1):
        es_titulo = marcar_titulos and fila and str(fila[0]).startswith("§")
        limpia = [str(c).lstrip("§") if j == 0 else c for j, c in enumerate(fila)]
        datos.append([Paragraph(str(c) if c is not None else "",
                                E["celda_fuerte"] if es_titulo else E["celda"])
                      for c in limpia])
        if es_titulo:
            estilos_fila.append(("BACKGROUND", (0, i), (-1, i), GRIS_CLARO))
            estilos_fila.append(("TEXTCOLOR", (0, i), (-1, i), AZUL))

    tabla = Table(datos, colWidths=anchos, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), GRIS),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFBFE")]),
    ]
    for c in derecha:
        estilo.append(("ALIGN", (c, 1), (c, -1), "RIGHT"))
    tabla.setStyle(TableStyle(estilo + estilos_fila))
    return tabla


def reporte(titulo: str, proyecto: dict, encabezados: list[str], filas: list[list],
            anchos: list[float], usuario: str, version: str | None = None,
            filtros: str = "", horizontal: bool = True,
            alineacion_derecha: set[int] | None = None,
            pie_extra: list | None = None, marcar_titulos: bool = False) -> bytes:
    salida = io.BytesIO()
    tamano = landscape(A4) if horizontal else A4
    doc = SimpleDocTemplate(
        salida, pagesize=tamano,
        leftMargin=15 * mm, rightMargin=15 * mm, topMargin=14 * mm, bottomMargin=18 * mm,
        title=f"{titulo} — {proyecto.get('nombre', '')}", author="METRA AI",
    )
    doc._metra_pie = (f"{proyecto.get('codigo') or ''} · {proyecto.get('nombre') or ''} · "
                      f"{titulo} · v{version or '—'} · METRA AI")

    historia = _portada(proyecto, titulo, usuario, version, filtros)
    historia.append(PageBreak())
    historia.append(Paragraph(titulo, E["seccion"]))
    if filas:
        historia.append(_tabla(encabezados, filas, anchos, alineacion_derecha, marcar_titulos))
    else:
        historia.append(Paragraph(
            "No hay datos que mostrar con los filtros aplicados.", E["texto"]))
    if pie_extra:
        historia.extend(pie_extra)
    historia.extend(_firmas())

    doc.build(historia, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
    return salida.getvalue()


def bloque_totales(lineas: list[tuple[str, str]], destacar_ultima: bool = True) -> list:
    filas = []
    for i, (etiqueta, valor) in enumerate(lineas):
        fuerte = destacar_ultima and i == len(lineas) - 1
        estilo = E["celda_fuerte"] if fuerte else E["celda"]
        filas.append([Paragraph(etiqueta, estilo), Paragraph(str(valor), estilo)])
    tabla = Table(filas, colWidths=[70 * mm, 40 * mm], hAlign="RIGHT")
    tabla.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, BORDE),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BACKGROUND", (0, len(filas) - 1), (-1, len(filas) - 1), GRIS_CLARO),
        ("TEXTCOLOR", (0, len(filas) - 1), (-1, len(filas) - 1), VERDE),
    ]))
    return [Spacer(1, 5 * mm), tabla]
