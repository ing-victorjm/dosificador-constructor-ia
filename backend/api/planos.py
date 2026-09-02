"""Archivos, planos, calibración de escala y mediciones sobre el plano.

Decisión clave de coordenadas: el plano se rasteriza SIEMPRE al mismo factor
(`ZOOM_BASE`) y todas las coordenadas de calibración y de trazos se guardan en
esos píxeles. El zoom de la pantalla es una transformación visual del lienzo, no
un cambio de sistema de referencia. Así una medición hecha con zoom 400% vale
exactamente lo mismo que otra hecha al 100%.
"""
from __future__ import annotations

import hashlib
import math
import shutil
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import audit, security
from ..db import DIR_ARCHIVOS, obtener_sesion
from ..models import Archivo, Marcado, Medicion, Plano, Usuario
from ..motor import especialidades
from ..motor.redondeo import dec, redondear
from ..motor.unidades import convertir
from .proyectos import obtener

router = APIRouter(tags=["planos"])

ZOOM_BASE = 2.0          # 144 ppp: suficiente para medir sin inflar la memoria
MAX_MB = 120
EXTENSIONES = {
    ".pdf": "pdf", ".dwg": "dwg", ".dxf": "dxf", ".ifc": "ifc", ".rvt": "rvt",
    ".xlsx": "xlsx", ".xls": "xlsx", ".csv": "csv",
    ".png": "img", ".jpg": "img", ".jpeg": "img", ".webp": "img",
}


def _carpeta(proyecto_id: str) -> Path:
    ruta = DIR_ARCHIVOS / proyecto_id
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


@router.post("/proyectos/{proyecto_id}/archivos", status_code=201)
async def subir(proyecto_id: str, archivo: UploadFile = File(...),
                especialidad: str = Form(default=""),
                db: Session = Depends(obtener_sesion),
                usuario: Usuario = Depends(security.usuario_actual)):
    obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "crear")

    nombre = Path(archivo.filename or "archivo").name
    extension = Path(nombre).suffix.lower()
    tipo = EXTENSIONES.get(extension)
    if not tipo:
        raise HTTPException(
            400,
            f"Formato no admitido ({extension or 'sin extensión'}). "
            f"Se aceptan: {', '.join(sorted(EXTENSIONES))}.")

    contenido = await archivo.read()
    if len(contenido) > MAX_MB * 1024 * 1024:
        raise HTTPException(413, f"El archivo supera {MAX_MB} MB.")
    if not contenido:
        raise HTTPException(400, "El archivo está vacío.")

    huella = hashlib.sha256(contenido).hexdigest()
    repetido = db.scalar(select(Archivo).where(Archivo.proyecto_id == proyecto_id,
                                               Archivo.hash == huella))
    if repetido:
        return {"archivo_id": repetido.id, "repetido": True,
                "mensaje": f"Este archivo ya estaba cargado como «{repetido.nombre}»."}

    destino = _carpeta(proyecto_id) / f"{huella[:16]}{extension}"
    destino.write_bytes(contenido)

    a = Archivo(proyecto_id=proyecto_id, nombre=nombre, tipo=tipo,
                ruta=str(destino), tamano=len(contenido), hash=huella,
                subido_por=usuario.id, estado="procesando")
    db.add(a)
    db.flush()

    mensaje = None
    try:
        if tipo == "pdf":
            a.paginas = _registrar_paginas_pdf(db, a, especialidad)
        elif tipo == "img":
            a.paginas = _registrar_imagen(db, a, especialidad)
        elif tipo == "dxf":
            a.meta = _leer_dxf(destino)
            mensaje = f"DXF leído: {a.meta.get('entidades', 0)} entidades en " \
                      f"{len(a.meta.get('capas', []))} capas."
        elif tipo == "ifc":
            a.meta = _leer_ifc(destino)
            mensaje = a.meta.get("mensaje")
        elif tipo in ("dwg", "rvt"):
            mensaje = ("Archivo guardado. La lectura directa de "
                       f"{tipo.upper()} necesita exportarlo antes a "
                       f"{'DXF' if tipo == 'dwg' else 'IFC'}: son formatos "
                       "propietarios sin lector abierto.")
        a.estado = "listo"
    except Exception as exc:  # el archivo queda guardado aunque falle el análisis
        a.estado = "error"
        a.mensaje = f"{type(exc).__name__}: {exc}"
        mensaje = f"El archivo se guardó pero no se pudo procesar: {exc}"

    a.mensaje = mensaje
    audit.registrar(db, accion="importar", entidad="archivo", entidad_id=a.id,
                    proyecto_id=proyecto_id,
                    resumen=f"Archivo cargado: {nombre} ({tipo})", usuario=usuario)
    db.commit()
    return {"archivo_id": a.id, "tipo": tipo, "paginas": a.paginas,
            "estado": a.estado, "mensaje": mensaje, "meta": a.meta}


def _registrar_paginas_pdf(db: Session, a: Archivo, especialidad: str) -> int:
    import fitz
    documento = fitz.open(a.ruta)
    try:
        for i, pagina in enumerate(documento, start=1):
            rect = pagina.rect
            texto = pagina.get_text("text")[:4000]
            db.add(Plano(
                proyecto_id=a.proyecto_id, archivo_id=a.id, pagina=i,
                codigo=_codigo_lamina(texto), titulo=_titulo_lamina(texto) or f"Página {i}",
                especialidad=especialidades.normalizar(especialidad) if especialidad else None,
                ancho_px=int(rect.width * ZOOM_BASE), alto_px=int(rect.height * ZOOM_BASE),
                escala_texto=_escala_detectada(texto),
            ))
        return documento.page_count
    finally:
        documento.close()


def _registrar_imagen(db: Session, a: Archivo, especialidad: str) -> int:
    from PIL import Image
    with Image.open(a.ruta) as img:
        ancho, alto = img.size
    db.add(Plano(proyecto_id=a.proyecto_id, archivo_id=a.id, pagina=1,
                 titulo=a.nombre, ancho_px=ancho, alto_px=alto,
                 especialidad=especialidades.normalizar(especialidad) if especialidad else None))
    return 1


def _codigo_lamina(texto: str) -> str | None:
    import re
    m = re.search(r"\b([AEISM]{1,2}\s?-\s?\d{1,3}(?:\.\d+)?)\b", texto or "")
    return m.group(1).replace(" ", "") if m else None


def _titulo_lamina(texto: str) -> str | None:
    for linea in (texto or "").splitlines():
        limpia = linea.strip()
        if 8 <= len(limpia) <= 80 and limpia.upper() == limpia and any(c.isalpha() for c in limpia):
            return limpia
    return None


def _escala_detectada(texto: str) -> str | None:
    import re
    m = re.search(r"\b(1\s?[:/]\s?\d{1,4})\b", texto or "")
    return m.group(1).replace(" ", "") if m else None


def _leer_dxf(ruta: Path) -> dict:
    import ezdxf
    doc = ezdxf.readfile(str(ruta))
    modelo = doc.modelspace()
    capas = sorted({e.dxf.layer for e in modelo if hasattr(e.dxf, "layer")})
    conteo: dict[str, int] = {}
    longitud_total = 0.0
    for e in modelo:
        conteo[e.dxftype()] = conteo.get(e.dxftype(), 0) + 1
        try:
            if e.dxftype() == "LINE":
                longitud_total += (e.dxf.end - e.dxf.start).magnitude
            elif e.dxftype() in ("LWPOLYLINE", "POLYLINE"):
                puntos = list(e.vertices()) if hasattr(e, "vertices") else []
                for i in range(1, len(puntos)):
                    a, b = puntos[i - 1], puntos[i]
                    longitud_total += math.dist(a[:2], b[:2])
        except (AttributeError, TypeError, ValueError):
            continue
    return {"capas": capas, "entidades": sum(conteo.values()),
            "por_tipo": conteo, "unidades_dibujo": doc.header.get("$INSUNITS", 0),
            "longitud_total_dibujo": round(longitud_total, 3)}


def _leer_ifc(ruta: Path) -> dict:
    try:
        import ifcopenshell
    except ImportError:
        return {"mensaje": "Para leer IFC instale ifcopenshell."}
    modelo = ifcopenshell.open(str(ruta))
    tipos = ("IfcWall", "IfcColumn", "IfcBeam", "IfcSlab", "IfcDoor", "IfcWindow",
             "IfcStair", "IfcFooting", "IfcPipeSegment", "IfcDuctSegment")
    conteo = {t: len(modelo.by_type(t)) for t in tipos if modelo.by_type(t)}
    return {"esquema": modelo.schema, "elementos": conteo,
            "mensaje": f"Modelo IFC {modelo.schema} con "
                       f"{sum(conteo.values())} elementos reconocidos."}


@router.get("/proyectos/{proyecto_id}/archivos")
def listar_archivos(proyecto_id: str, db: Session = Depends(obtener_sesion),
                    usuario: Usuario = Depends(security.usuario_actual)):
    security.exigir(db, usuario, proyecto_id, "ver")
    filas = list(db.scalars(select(Archivo).where(Archivo.proyecto_id == proyecto_id)
                            .order_by(Archivo.creado_en.desc())))
    return {"archivos": [{
        "id": a.id, "nombre": a.nombre, "tipo": a.tipo, "tamano": a.tamano,
        "paginas": a.paginas, "estado": a.estado, "mensaje": a.mensaje,
        "meta": a.meta or {},
        "creado_en": a.creado_en.isoformat() if a.creado_en else None,
    } for a in filas]}


@router.delete("/archivos/{archivo_id}")
def eliminar_archivo(archivo_id: str, db: Session = Depends(obtener_sesion),
                     usuario: Usuario = Depends(security.usuario_actual)):
    a = db.get(Archivo, archivo_id)
    if not a:
        raise HTTPException(404, "Archivo no encontrado.")
    security.exigir(db, usuario, a.proyecto_id, "eliminar")
    usos = db.scalar(select(func.count(Medicion.id)).join(Plano, Medicion.plano_id == Plano.id)
                     .where(Plano.archivo_id == archivo_id)) or 0
    if usos:
        raise HTTPException(
            409, f"No se puede eliminar: {usos} fila(s) de metrado citan planos de este archivo. "
                 "Quedarían sin sustento.")
    Path(a.ruta).unlink(missing_ok=True)
    audit.registrar(db, accion="eliminar", entidad="archivo", entidad_id=a.id,
                    proyecto_id=a.proyecto_id, resumen=f"Archivo eliminado: {a.nombre}",
                    usuario=usuario)
    db.delete(a)
    db.commit()
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Planos
# --------------------------------------------------------------------------- #

@router.get("/proyectos/{proyecto_id}/planos")
def listar_planos(proyecto_id: str, db: Session = Depends(obtener_sesion),
                  usuario: Usuario = Depends(security.usuario_actual)):
    security.exigir(db, usuario, proyecto_id, "ver")
    filas = list(db.scalars(select(Plano).where(Plano.proyecto_id == proyecto_id)
                            .order_by(Plano.archivo_id, Plano.pagina)))
    archivos = {a.id: a.nombre for a in db.scalars(
        select(Archivo).where(Archivo.proyecto_id == proyecto_id))}
    return {"planos": [{
        "id": pl.id, "archivo_id": pl.archivo_id, "archivo": archivos.get(pl.archivo_id),
        "pagina": pl.pagina, "codigo": pl.codigo, "titulo": pl.titulo,
        "especialidad": pl.especialidad, "ancho_px": pl.ancho_px, "alto_px": pl.alto_px,
        "escala_texto": pl.escala_texto, "metros_por_px": pl.metros_por_px,
        "calibrado": bool(pl.metros_por_px), "rotacion": pl.rotacion,
    } for pl in filas]}


@router.get("/planos/{plano_id}/imagen")
def imagen(plano_id: str, db: Session = Depends(obtener_sesion),
           usuario: Usuario = Depends(security.usuario_actual)):
    """Rasteriza la página al factor canónico y la cachea en disco."""
    pl = db.get(Plano, plano_id)
    if not pl:
        raise HTTPException(404, "Plano no encontrado.")
    security.exigir(db, usuario, pl.proyecto_id, "ver")
    a = db.get(Archivo, pl.archivo_id)
    if not a or not Path(a.ruta).exists():
        raise HTTPException(410, "El archivo original ya no está disponible.")

    if a.tipo == "img":
        return FileResponse(a.ruta)

    cache = _carpeta(pl.proyecto_id) / "render" / f"{pl.id}.png"
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        import fitz
        documento = fitz.open(a.ruta)
        try:
            pagina = documento[pl.pagina - 1]
            pix = pagina.get_pixmap(matrix=fitz.Matrix(ZOOM_BASE, ZOOM_BASE), alpha=False)
            pix.save(str(cache))
            if pl.ancho_px != pix.width or pl.alto_px != pix.height:
                pl.ancho_px, pl.alto_px = pix.width, pix.height
                db.commit()
        finally:
            documento.close()
    return FileResponse(cache, media_type="image/png",
                        headers={"Cache-Control": "public, max-age=86400"})


class Calibracion(BaseModel):
    p1: list[float]
    p2: list[float]
    distancia_real: str
    unidad: str = "m"
    escala_texto: str | None = None


@router.put("/planos/{plano_id}/calibrar")
def calibrar(plano_id: str, datos: Calibracion, db: Session = Depends(obtener_sesion),
             usuario: Usuario = Depends(security.usuario_actual)):
    """Fija la escala midiendo una distancia conocida del plano."""
    pl = db.get(Plano, plano_id)
    if not pl:
        raise HTTPException(404, "Plano no encontrado.")
    security.exigir(db, usuario, pl.proyecto_id, "editar")

    if len(datos.p1) != 2 or len(datos.p2) != 2:
        raise HTTPException(400, "Marque dos puntos sobre el plano.")
    distancia_px = math.dist(datos.p1, datos.p2)
    if distancia_px < 5:
        raise HTTPException(
            400, "Los dos puntos están demasiado juntos. Use una distancia larga y conocida "
                 "(una cota de varios metros): mientras más larga, más exacta la escala.")
    real = dec(datos.distancia_real)
    if real <= 0:
        raise HTTPException(400, "La distancia real debe ser mayor que cero.")

    metros = convertir(real, datos.unidad, "m")
    pl.metros_por_px = str(metros / dec(distancia_px))
    pl.escala_texto = datos.escala_texto or pl.escala_texto
    pl.calibracion = {
        "p1": datos.p1, "p2": datos.p2, "distancia_px": round(distancia_px, 3),
        "distancia_real": str(real), "unidad": datos.unidad,
        "por": usuario.nombre, "fecha": date.today().isoformat(),
    }
    audit.registrar(db, accion="editar", entidad="plano", entidad_id=pl.id,
                    proyecto_id=pl.proyecto_id,
                    resumen=f"Plano calibrado: {real} {datos.unidad} en "
                            f"{round(distancia_px)} px",
                    usuario=usuario)
    db.commit()
    escala = 1 / (float(metros) / distancia_px * 1000 / (25.4 / 72 / ZOOM_BASE * 1000)) \
        if distancia_px else 0
    return {"metros_por_px": pl.metros_por_px, "calibracion": pl.calibracion,
            "escala_estimada": f"1:{round(abs(escala))}" if escala else None}


class DatosPlano(BaseModel):
    codigo: str | None = None
    titulo: str | None = None
    especialidad: str | None = None
    ubicacion_id: str | None = None
    rotacion: int | None = None


@router.put("/planos/{plano_id}")
def actualizar_plano(plano_id: str, datos: DatosPlano, db: Session = Depends(obtener_sesion),
                     usuario: Usuario = Depends(security.usuario_actual)):
    pl = db.get(Plano, plano_id)
    if not pl:
        raise HTTPException(404, "Plano no encontrado.")
    security.exigir(db, usuario, pl.proyecto_id, "editar")
    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(pl, campo, valor)
    db.commit()
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Mediciones sobre el plano
# --------------------------------------------------------------------------- #

class DatosMarcado(BaseModel):
    tipo: str                    # longitud | area | conteo | nota
    puntos: list[list[float]]
    etiqueta: str | None = None
    especialidad: str | None = None
    color: str | None = None
    item_id: str | None = None   # si viene, se crea la fila de metrado
    descripcion: str | None = None
    ubicacion_id: str | None = None


def _medir(tipo: str, puntos: list[list[float]], metros_por_px) -> tuple[str, str]:
    """Devuelve (valor, unidad) en unidades reales."""
    m = dec(metros_por_px)
    if tipo == "conteo":
        return str(len(puntos)), "und"
    if tipo == "longitud":
        total = sum(math.dist(puntos[i - 1], puntos[i]) for i in range(1, len(puntos)))
        return str(redondear(dec(total) * m, 3)), "m"
    if tipo == "area":
        if len(puntos) < 3:
            raise HTTPException(400, "Un área necesita al menos tres puntos.")
        # Fórmula del polígono (Gauss).
        suma = 0.0
        for i in range(len(puntos)):
            x1, y1 = puntos[i]
            x2, y2 = puntos[(i + 1) % len(puntos)]
            suma += x1 * y2 - x2 * y1
        area_px = abs(suma) / 2
        return str(redondear(dec(area_px) * m * m, 3)), "m2"
    return "0", "und"


@router.post("/planos/{plano_id}/marcados", status_code=201)
def crear_marcado(plano_id: str, datos: DatosMarcado, db: Session = Depends(obtener_sesion),
                  usuario: Usuario = Depends(security.usuario_actual)):
    pl = db.get(Plano, plano_id)
    if not pl:
        raise HTTPException(404, "Plano no encontrado.")
    security.exigir(db, usuario, pl.proyecto_id, "crear")
    if datos.tipo != "nota" and not pl.metros_por_px:
        raise HTTPException(
            409,
            "El plano no está calibrado. Marque primero una distancia conocida: sin escala, "
            "cualquier medición sobre este plano sería inventada.")

    valor, unidad = ("0", "und")
    if datos.tipo != "nota":
        valor, unidad = _medir(datos.tipo, datos.puntos, pl.metros_por_px)

    m = Marcado(proyecto_id=pl.proyecto_id, plano_id=plano_id, tipo=datos.tipo,
                puntos=datos.puntos, valor=valor, unidad=unidad,
                etiqueta=datos.etiqueta, especialidad=datos.especialidad,
                color=datos.color or (especialidades.color(datos.especialidad)
                                      if datos.especialidad else None),
                autor=usuario.id)
    db.add(m)
    db.flush()

    medicion_id = None
    if datos.item_id:
        from ..models import Item
        it = db.get(Item, datos.item_id)
        if not it:
            raise HTTPException(404, "La partida indicada no existe.")
        if it.bloqueado:
            raise HTTPException(409, "La partida está aprobada y bloqueada.")
        orden = (db.scalar(select(func.max(Medicion.orden))
                           .where(Medicion.item_id == it.id)) or 0) + 10
        columna = {"longitud": "largo", "area": None, "conteo": "n"}[datos.tipo]
        fila = Medicion(
            item_id=it.id, proyecto_id=pl.proyecto_id, orden=orden,
            descripcion=datos.descripcion or datos.etiqueta or f"Medido en {pl.codigo or pl.titulo}",
            plano_id=plano_id, lamina=pl.codigo, ubicacion_id=datos.ubicacion_id,
            unidad=it.unidad, origen="medido_plano", responsable=usuario.id,
            fecha=date.today().isoformat(),
        )
        if columna:
            setattr(fila, columna, valor)
        else:
            fila.formula = "area_medida"
            fila.variables = {"area_medida": valor}
        db.add(fila)
        db.flush()
        m.medicion_id = fila.id
        medicion_id = fila.id

    audit.registrar(db, accion="crear", entidad="marcado", entidad_id=m.id,
                    proyecto_id=pl.proyecto_id,
                    resumen=f"Medición sobre plano: {datos.tipo} = {valor} {unidad}",
                    usuario=usuario)
    db.commit()
    return {"marcado": {"id": m.id, "tipo": m.tipo, "valor": m.valor, "unidad": m.unidad,
                        "color": m.color, "etiqueta": m.etiqueta},
            "medicion_id": medicion_id}


@router.get("/planos/{plano_id}/marcados")
def listar_marcados(plano_id: str, db: Session = Depends(obtener_sesion),
                    usuario: Usuario = Depends(security.usuario_actual)):
    pl = db.get(Plano, plano_id)
    if not pl:
        raise HTTPException(404, "Plano no encontrado.")
    security.exigir(db, usuario, pl.proyecto_id, "ver")
    filas = list(db.scalars(select(Marcado).where(Marcado.plano_id == plano_id)
                            .order_by(Marcado.creado_en)))
    return {"marcados": [{
        "id": m.id, "tipo": m.tipo, "puntos": m.puntos, "valor": m.valor,
        "unidad": m.unidad, "color": m.color, "etiqueta": m.etiqueta,
        "especialidad": m.especialidad, "medicion_id": m.medicion_id,
    } for m in filas],
        "plano": {"id": pl.id, "ancho_px": pl.ancho_px, "alto_px": pl.alto_px,
                  "metros_por_px": pl.metros_por_px, "calibrado": bool(pl.metros_por_px),
                  "codigo": pl.codigo, "titulo": pl.titulo,
                  "calibracion": pl.calibracion}}


@router.delete("/marcados/{marcado_id}")
def eliminar_marcado(marcado_id: str, borrar_medicion: bool = False,
                     db: Session = Depends(obtener_sesion),
                     usuario: Usuario = Depends(security.usuario_actual)):
    m = db.get(Marcado, marcado_id)
    if not m:
        raise HTTPException(404, "Marcado no encontrado.")
    security.exigir(db, usuario, m.proyecto_id, "editar")
    if borrar_medicion and m.medicion_id:
        fila = db.get(Medicion, m.medicion_id)
        if fila:
            db.delete(fila)
    db.delete(m)
    db.commit()
    return {"ok": True}


@router.get("/planos/comparar")
def comparar_planos(a: str, b: str, db: Session = Depends(obtener_sesion),
                    usuario: Usuario = Depends(security.usuario_actual)):
    """Datos para superponer dos versiones de un plano."""
    pa, pb = db.get(Plano, a), db.get(Plano, b)
    if not pa or not pb:
        raise HTTPException(404, "Uno de los planos no existe.")
    security.exigir(db, usuario, pa.proyecto_id, "ver")
    avisos = []
    if pa.metros_por_px and pb.metros_por_px:
        ra, rb = dec(pa.metros_por_px), dec(pb.metros_por_px)
        if abs(ra - rb) / max(ra, rb) > dec("0.02"):
            avisos.append("Los dos planos están calibrados a escalas distintas: la "
                          "superposición no coincidirá. Recalibre uno de ellos.")
    else:
        avisos.append("Al menos uno de los planos no está calibrado.")
    return {
        "a": {"id": pa.id, "codigo": pa.codigo, "titulo": pa.titulo,
              "ancho_px": pa.ancho_px, "alto_px": pa.alto_px,
              "metros_por_px": pa.metros_por_px},
        "b": {"id": pb.id, "codigo": pb.codigo, "titulo": pb.titulo,
              "ancho_px": pb.ancho_px, "alto_px": pb.alto_px,
              "metros_por_px": pb.metros_por_px},
        "avisos": avisos,
    }
