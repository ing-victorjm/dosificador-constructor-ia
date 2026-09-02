"""Datos iniciales: catálogo normativo, insumos y proyecto de demostración.

Todo es idempotente: se puede ejecutar en cada arranque sin duplicar nada.
"""
from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import sesion
from .models import Insumo, PartidaCatalogo, Usuario
from .motor import especialidades, formulas, normas, tablas
from .motor.unidades import existe as unidad_existe
from .security import asegurar_usuario_local

log = logging.getLogger("metra.semillas")

# La norma etiqueta las especialidades con su código; aquí se traducen a las
# claves internas para poder pintar colores y filtrar por disciplina.
MAPA_ESPECIALIDAD = {
    "OE.1": "preliminares",
    "OE.2": "estructuras",
    "OE.3": "arquitectura",
    "OE.4": "sanitarias",
    "OE.5": "electricas",
    "OE.6": "comunicaciones",
    "OE.7": "mecanicas",
    "HU.1": "preliminares",
    "HU.2": "exteriores",
    "HU.3": "sanitarias",
    "HU.4": "electricas",
    "HU.5": "comunicaciones",
    "HU.6": "mecanicas",
}

# Dentro de Estructuras, el capítulo OE.2.1 es movimiento de tierras.
PREFIJOS_FINOS = [
    ("OE.2.1", "movimiento_tierras"),
    ("OE.1.6", "seguridad"),
    ("OE.3.13", "varios"),
    ("OE.5.6", "mecanicas"),
]


def _especialidad_de(codigo: str, texto: str) -> str:
    for prefijo, clave in PREFIJOS_FINOS:
        if codigo.startswith(prefijo):
            return clave
    raiz = ".".join(codigo.split(".")[:2]) if codigo.count(".") >= 1 else codigo
    if raiz in MAPA_ESPECIALIDAD:
        return MAPA_ESPECIALIDAD[raiz]
    return especialidades.normalizar(texto)


GENERICAS = ("PARA ", "DEL ", "DE LA ", "SUMINISTRO", "INSTALACIÓN", "INSTALACION")


def _descripcion_completa(codigo: str, descripcion: str, titulos: dict[str, str]) -> str:
    """«PARA EL CONCRETO» → «COLUMNAS — PARA EL CONCRETO»."""
    if not descripcion.upper().startswith(GENERICAS):
        return descripcion
    partes = codigo.split(".")
    for corte in range(len(partes) - 1, 1, -1):
        padre = titulos.get(".".join(partes[:corte]), "").strip()
        if padre and not padre.upper().startswith(GENERICAS):
            return f"{padre} — {descripcion}"
    return descripcion


def _plantilla_para(unidad: str | None, descripcion: str) -> tuple[str | None, str | None]:
    """Sugiere plantilla de fórmula y expresión según la unidad de la partida."""
    if not unidad:
        return None, None
    t = (descripcion or "").lower()
    if unidad == "m3":
        if any(p in t for p in ("excavaci", "relleno", "corte", "elimina")):
            return "volumen", "n * largo * ancho * alto"
        return "volumen", "n * largo * ancho * alto"
    if unidad == "m2":
        if any(p in t for p in ("encofrado", "muro", "tarrajeo", "pintura", "revoque")):
            return "area_menos_vanos", None
        return "area", "n * largo * ancho"
    if unidad in ("m", "km"):
        return "longitud", "n * largo"
    if unidad == "kg":
        return "peso_longitud", "n * longitud * peso_unitario"
    if unidad in ("und", "pto", "glb", "h"):
        return "conteo", "n"
    return None, None


def sembrar_catalogo(db: Session) -> int:
    """Importa el catálogo normativo desde `datos/tablas/partidas_pe.json`."""
    datos = tablas.cargar("partidas_pe", [])
    if not datos:
        log.warning("No hay catálogo normativo que sembrar (datos/tablas/partidas_pe.json).")
        return 0

    ya = {c for c in db.scalars(select(PartidaCatalogo.codigo).where(PartidaCatalogo.empresa_id.is_(None)))}
    # La norma escribe las subpartidas como «PARA EL CONCRETO» colgando de
    # «COLUMNAS». Aisladas no se entienden: se les antepone la partida madre.
    titulos = {(x.get("codigo") or "").strip(): (x.get("descripcion") or "").strip()
               for x in datos}
    nuevas = 0
    for p in datos:
        codigo = (p.get("codigo") or "").strip()
        if not codigo or codigo in ya:
            continue
        unidad = (p.get("unidad") or "").strip() or None
        if unidad and not unidad_existe(unidad):
            log.warning("Unidad no registrada en %s: %s", codigo, unidad)
            unidad = None
        descripcion = _descripcion_completa(codigo, (p.get("descripcion") or "").strip(), titulos)
        esp = _especialidad_de(codigo, p.get("especialidad") or "")
        plantilla, formula = _plantilla_para(unidad, descripcion)
        db.add(PartidaCatalogo(
            empresa_id=None,
            codigo=codigo,
            descripcion=descripcion,
            unidad=unidad or "glb",
            especialidad=esp,
            capitulo=p.get("especialidad"),
            formula=formula,
            plantilla_formula=plantilla,
            regla_medicion=p.get("regla_medicion"),
            norma=p.get("fuente"),
            pais="PE",
            verificado=bool(p.get("verificado")),
            fuente=p.get("url_fuente"),
            etiquetas=[x for x in [
                p.get("origen_unidad") and f"unidad: {p['origen_unidad']}",
                p.get("origen_regla") and f"regla: {p['origen_regla']}",
                None if unidad else "sin unidad en la norma",
            ] if x],
        ))
        ya.add(codigo)
        nuevas += 1
    if nuevas:
        db.commit()
        log.info("Catálogo normativo: %s partidas nuevas.", nuevas)
    return nuevas


INSUMOS_BASE = [
    ("MO01", "Capataz", "hh", "MO"),
    ("MO02", "Operario", "hh", "MO"),
    ("MO03", "Oficial", "hh", "MO"),
    ("MO04", "Peón", "hh", "MO"),
    ("MT01", "Cemento Portland Tipo I (42.5 kg)", "bls", "MAT"),
    ("MT02", "Arena gruesa", "m3", "MAT"),
    ("MT03", "Arena fina", "m3", "MAT"),
    ("MT04", "Piedra chancada 1/2\"", "m3", "MAT"),
    ("MT05", "Agua", "m3", "MAT"),
    ("MT06", "Acero corrugado fy=4200 kg/cm2", "kg", "MAT"),
    ("MT07", "Alambre negro N° 16", "kg", "MAT"),
    ("MT08", "Clavos para madera", "kg", "MAT"),
    ("MT09", "Madera tornillo para encofrado", "p2", "MAT"),
    ("MT10", "Ladrillo King Kong 18 huecos 9x13x24", "und", "MAT"),
    ("MT11", "Ladrillo de techo 15x30x30", "und", "MAT"),
    ("EQ01", "Herramientas manuales", "pct", "EQ"),
    ("EQ02", "Mezcladora de concreto 9-11 p3", "hm", "EQ"),
    ("EQ03", "Vibrador de concreto 4 HP", "hm", "EQ"),
    ("EQ04", "Retroexcavadora sobre llantas 80 HP", "hm", "EQ"),
    ("EQ05", "Camión volquete 15 m3", "hm", "EQ"),
]


def sembrar_insumos(db: Session) -> int:
    ya = {c for c in db.scalars(select(Insumo.codigo).where(Insumo.empresa_id.is_(None)))}
    nuevos = 0
    for codigo, descripcion, unidad, tipo in INSUMOS_BASE:
        if codigo in ya:
            continue
        db.add(Insumo(empresa_id=None, codigo=codigo, descripcion=descripcion,
                      unidad=unidad, tipo=tipo, moneda="PEN"))
        nuevos += 1
    if nuevos:
        db.commit()
    return nuevos


def sembrar() -> dict:
    """Punto de entrada del arranque."""
    resumen = {}
    with sesion() as db:
        asegurar_usuario_local(db)
        resumen["catalogo"] = sembrar_catalogo(db)
        resumen["insumos"] = sembrar_insumos(db)
        resumen["usuarios"] = db.scalar(select(func.count(Usuario.id)))
        resumen["partidas_catalogo"] = db.scalar(select(func.count(PartidaCatalogo.id)))
    return resumen


def estado() -> dict:
    """Diagnóstico que la interfaz muestra en Configuración."""
    with sesion() as db:
        total = db.scalar(select(func.count(PartidaCatalogo.id)))
        verificadas = db.scalar(select(func.count(PartidaCatalogo.id))
                                .where(PartidaCatalogo.verificado.is_(True)))
    return {
        "partidas_catalogo": total,
        "partidas_verificadas": verificadas,
        "tablas": tablas.inventario(),
        "plantillas_formula": len(formulas.PLANTILLAS),
        "familias_descuento": len(normas.FAMILIAS),
    }
