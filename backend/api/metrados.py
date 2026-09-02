"""Hoja de metrados: partidas, filas de sustento, pegado masivo y trazabilidad."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import audit, security, servicios
from ..db import obtener_sesion
from ..models import Item, Medicion, PartidaCatalogo, Proyecto, Ubicacion, Usuario
from ..motor import formulas, medicion as mot, normas
from ..motor.unidades import ErrorUnidad, existe as unidad_existe
from .proyectos import obtener

router = APIRouter(tags=["metrados"])

# Orden de columnas del pegado desde Excel: es la cabecera de la planilla de
# sustento de cualquier expediente técnico.
COLUMNAS_PEGADO = ["descripcion", "n", "veces", "largo", "ancho", "alto", "lamina", "eje"]


def _item(db: Session, item_id: str) -> Item:
    it = db.get(Item, item_id)
    if not it:
        raise HTTPException(404, "La partida no existe.")
    return it


def _exigir_editable(db: Session, usuario: Usuario, it: Item) -> None:
    security.exigir(db, usuario, it.proyecto_id, "editar")
    if it.bloqueado:
        raise HTTPException(
            409,
            "La partida está aprobada y bloqueada. Un supervisor debe desbloquearla "
            "antes de modificar su metrado.",
        )


# --------------------------------------------------------------------------- #
# Lectura
# --------------------------------------------------------------------------- #

@router.get("/proyectos/{proyecto_id}/metrados")
def hoja(proyecto_id: str, version_id: str | None = None,
         especialidad: str | None = None, con_filas: bool = Query(default=False),
         db: Session = Depends(obtener_sesion),
         usuario: Usuario = Depends(security.usuario_actual)):
    p = obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "ver")
    datos = servicios.arbol(db, p, version_id=version_id or p.version_actual_id,
                            con_filas=con_filas)
    if especialidad:
        datos["items"] = [n for n in datos["items"]
                          if _tiene_especialidad(n, especialidad)]
    return datos


def _tiene_especialidad(nodo: dict, especialidad: str) -> bool:
    if nodo["tipo"] == "partida":
        return nodo["especialidad"] == especialidad
    nodo["hijos"] = [h for h in nodo.get("hijos", []) if _tiene_especialidad(h, especialidad)]
    return bool(nodo["hijos"])


@router.get("/items/{item_id}")
def ver_item(item_id: str, db: Session = Depends(obtener_sesion),
             usuario: Usuario = Depends(security.usuario_actual)):
    it = _item(db, item_id)
    security.exigir(db, usuario, it.proyecto_id, "ver")
    p = db.get(Proyecto, it.proyecto_id)
    calculo = servicios.calcular_item(db, it, servicios.reglas_de(p), refrescar=True)
    db.commit()
    familia = normas.FAMILIAS.get(it.familia_descuento or "")
    return {
        "item": {
            "id": it.id, "tipo": it.tipo, "codigo": it.codigo,
            "descripcion": it.descripcion, "unidad": it.unidad,
            "especialidad": it.especialidad, "estado": it.estado,
            "bloqueado": it.bloqueado, "desperdicio_pct": it.desperdicio_pct,
            "precio_unitario": it.precio_unitario,
            "cantidad_manual": it.cantidad_manual,
            "cantidad_contratada": it.cantidad_contratada,
            "cantidad_ejecutada": it.cantidad_ejecutada,
            "familia_descuento": it.familia_descuento,
            "regla_medicion": it.regla_medicion,
            "etiqueta_fuente": it.etiqueta_fuente,
            "observaciones": it.observaciones,
        },
        "filas": calculo["filas"],
        "resumen": calculo["total"].a_dict(),
        "familia": {"clave": familia.clave, "nombre": familia.nombre,
                    "cita": familia.cita, "umbral_m2": str(familia.umbral_m2),
                    "codigo": familia.codigo} if familia else None,
    }


@router.get("/items/{item_id}/trazabilidad")
def trazabilidad(item_id: str, db: Session = Depends(obtener_sesion),
                 usuario: Usuario = Depends(security.usuario_actual)):
    """«¿De dónde sale esta cantidad?» — la respuesta completa, fila por fila."""
    it = _item(db, item_id)
    security.exigir(db, usuario, it.proyecto_id, "ver")
    p = db.get(Proyecto, it.proyecto_id)
    calculo = servicios.calcular_item(db, it, servicios.reglas_de(p), refrescar=True)
    db.commit()

    ubicaciones = {u.id: u.nombre for u in db.scalars(
        select(Ubicacion).where(Ubicacion.proyecto_id == it.proyecto_id))}

    detalle = []
    for f in calculo["filas"]:
        detalle.append({
            "id": f["id"],
            "descripcion": f.get("descripcion"),
            "ubicacion": ubicaciones.get(f.get("ubicacion_id")),
            "eje": f.get("eje"),
            "lamina": f.get("lamina"),
            "metodo": f["metodo"],
            "sustento": f["sustento"],
            "pasos": f["pasos"],
            "parcial": f["parcial"],
            "origen": f["origen"],
            "confianza": f.get("confianza"),
            "supuesto": f.get("supuesto"),
            "error": f.get("error"),
            "aviso": f.get("aviso"),
        })

    origenes = {}
    for f in calculo["filas"]:
        origenes[f["origen"]] = origenes.get(f["origen"], 0) + 1

    return {
        "item": {"id": it.id, "codigo": it.codigo, "descripcion": it.descripcion,
                 "unidad": it.unidad},
        "regla_medicion": it.regla_medicion,
        "etiqueta_fuente": it.etiqueta_fuente,
        "resumen": calculo["total"].a_dict(),
        "detalle": detalle,
        "origenes": origenes,
        "nota_desperdicio": normas.REGLA_DESPERDICIO if it.desperdicio_pct else None,
    }


# --------------------------------------------------------------------------- #
# Partidas
# --------------------------------------------------------------------------- #

class DatosItem(BaseModel):
    tipo: str = "partida"
    descripcion: str | None = None
    codigo: str | None = None
    unidad: str | None = None
    especialidad: str | None = None
    padre_id: str | None = None
    catalogo_id: str | None = None
    orden: int | None = None
    version_id: str | None = None
    desperdicio_pct: str | None = None
    precio_unitario: str | None = None
    familia_descuento: str | None = None


@router.post("/proyectos/{proyecto_id}/items", status_code=201)
def crear_item(proyecto_id: str, datos: DatosItem,
               db: Session = Depends(obtener_sesion),
               usuario: Usuario = Depends(security.usuario_actual)):
    p = obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "crear")

    catalogo = db.get(PartidaCatalogo, datos.catalogo_id) if datos.catalogo_id else None
    descripcion = datos.descripcion or (catalogo.descripcion if catalogo else None)
    if not descripcion:
        raise HTTPException(400, "Escriba la descripción de la partida o elija una del catálogo.")

    unidad = datos.unidad or (catalogo.unidad if catalogo else None)
    if datos.tipo == "partida":
        if not unidad:
            raise HTTPException(400, "La partida necesita una unidad de medida.")
        if not unidad_existe(unidad):
            raise ErrorUnidad(f"Unidad desconocida: {unidad!r}")

    especialidad = datos.especialidad or (catalogo.especialidad if catalogo else "arquitectura")
    familia = datos.familia_descuento or (
        normas.familia_por_defecto(especialidad, descripcion) if datos.tipo == "partida" else None)

    orden = datos.orden
    if orden is None:
        orden = (db.scalar(select(func.max(Item.orden)).where(
            Item.proyecto_id == proyecto_id,
            Item.padre_id == datos.padre_id)) or 0) + 10

    it = Item(
        proyecto_id=proyecto_id,
        version_id=datos.version_id or p.version_actual_id,
        padre_id=datos.padre_id,
        catalogo_id=catalogo.id if catalogo else None,
        tipo=datos.tipo,
        codigo=datos.codigo or (catalogo.codigo if catalogo else None),
        descripcion=descripcion,
        unidad=unidad if datos.tipo == "partida" else None,
        especialidad=especialidad,
        orden=orden,
        desperdicio_pct=datos.desperdicio_pct,
        precio_unitario=datos.precio_unitario,
        familia_descuento=familia,
        regla_medicion=catalogo.regla_medicion if catalogo else None,
        etiqueta_fuente=normas.NORMA if (catalogo and catalogo.verificado) else normas.USUARIO,
        responsable=usuario.id,
    )
    db.add(it)
    audit.registrar(db, accion="crear", entidad="item", entidad_id=it.id,
                    proyecto_id=proyecto_id,
                    resumen=f"{it.tipo}: {it.descripcion[:120]}", usuario=usuario)
    db.commit()
    return {"item": {"id": it.id, "descripcion": it.descripcion, "unidad": it.unidad,
                     "especialidad": it.especialidad, "tipo": it.tipo,
                     "familia_descuento": it.familia_descuento,
                     "regla_medicion": it.regla_medicion}}


class CambioItem(BaseModel):
    descripcion: str | None = None
    codigo: str | None = None
    unidad: str | None = None
    especialidad: str | None = None
    padre_id: str | None = None
    orden: int | None = None
    desperdicio_pct: str | None = None
    precio_unitario: str | None = None
    cantidad_manual: str | None = None
    cantidad_contratada: str | None = None
    cantidad_ejecutada: str | None = None
    familia_descuento: str | None = None
    observaciones: str | None = None


@router.put("/items/{item_id}")
def actualizar_item(item_id: str, cambio: CambioItem,
                    db: Session = Depends(obtener_sesion),
                    usuario: Usuario = Depends(security.usuario_actual)):
    it = _item(db, item_id)
    _exigir_editable(db, usuario, it)
    datos = cambio.model_dump(exclude_unset=True)
    if "unidad" in datos and datos["unidad"] and not unidad_existe(datos["unidad"]):
        raise ErrorUnidad(f"Unidad desconocida: {datos['unidad']!r}")
    if datos.get("padre_id") == item_id:
        raise HTTPException(400, "Una partida no puede colgar de sí misma.")
    antes = audit.instantanea(it)
    for campo, valor in datos.items():
        setattr(it, campo, valor)
    audit.registrar_cambio(db, entidad="item", entidad_id=it.id, proyecto_id=it.proyecto_id,
                           antes=antes, despues=audit.instantanea(it),
                           resumen=f"Partida editada: {it.descripcion[:100]}", usuario=usuario)
    db.commit()
    return {"ok": True}


@router.delete("/items/{item_id}")
def eliminar_item(item_id: str, db: Session = Depends(obtener_sesion),
                  usuario: Usuario = Depends(security.usuario_actual)):
    it = _item(db, item_id)
    security.exigir(db, usuario, it.proyecto_id, "eliminar")
    if it.bloqueado:
        raise HTTPException(409, "No se puede eliminar una partida aprobada y bloqueada.")
    audit.registrar(db, accion="eliminar", entidad="item", entidad_id=it.id,
                    proyecto_id=it.proyecto_id,
                    resumen=f"Partida eliminada: {it.descripcion[:120]}",
                    antes=audit.instantanea(it), usuario=usuario)
    db.delete(it)
    db.commit()
    return {"ok": True}


class CambioEstado(BaseModel):
    estado: str
    comentario: str | None = None


@router.post("/items/{item_id}/estado")
def cambiar_estado(item_id: str, datos: CambioEstado,
                   db: Session = Depends(obtener_sesion),
                   usuario: Usuario = Depends(security.usuario_actual)):
    """Flujo de revisión. Aprobar bloquea la partida; desbloquear exige permiso."""
    it = _item(db, item_id)
    validos = {"borrador", "revisado", "observado", "aprobado"}
    if datos.estado not in validos:
        raise HTTPException(400, f"Estado no válido. Use uno de: {', '.join(sorted(validos))}")

    accion = {"revisado": "revisar", "observado": "revisar", "aprobado": "aprobar",
              "borrador": "desbloquear"}[datos.estado]
    security.exigir(db, usuario, it.proyecto_id, accion)

    if it.bloqueado and datos.estado != "borrador":
        raise HTTPException(409, "La partida está bloqueada. Desbloquéela primero.")

    from ..models import Aprobacion
    anterior = it.estado
    it.estado = datos.estado
    it.bloqueado = datos.estado == "aprobado"
    db.add(Aprobacion(proyecto_id=it.proyecto_id, item_id=it.id, accion=accion,
                      usuario_id=usuario.id, comentario=datos.comentario))
    audit.registrar(db, accion=accion, entidad="item", entidad_id=it.id,
                    proyecto_id=it.proyecto_id,
                    resumen=f"{anterior} → {datos.estado}: {it.descripcion[:100]}",
                    antes={"estado": anterior}, despues={"estado": datos.estado},
                    usuario=usuario)
    db.commit()
    return {"estado": it.estado, "bloqueado": it.bloqueado}


# --------------------------------------------------------------------------- #
# Filas de sustento
# --------------------------------------------------------------------------- #

class DatosMedicion(BaseModel):
    descripcion: str | None = None
    ubicacion_id: str | None = None
    elemento_id: str | None = None
    plano_id: str | None = None
    lamina: str | None = None
    eje: str | None = None
    n: str | None = None
    veces: str | None = None
    largo: str | None = None
    ancho: str | None = None
    alto: str | None = None
    formula: str | None = None
    plantilla_formula: str | None = None
    variables: dict | None = None
    signo: int = 1
    origen: str = "ingresado"
    confianza: str | None = None
    supuesto: str | None = None
    observacion: str | None = None
    orden: int | None = None


def _aplicar(m: Medicion, datos: dict) -> None:
    for campo, valor in datos.items():
        if campo in ("variables",) and valor is None:
            continue
        setattr(m, campo, valor)


@router.post("/items/{item_id}/mediciones", status_code=201)
def crear_medicion(item_id: str, datos: DatosMedicion,
                   db: Session = Depends(obtener_sesion),
                   usuario: Usuario = Depends(security.usuario_actual)):
    it = _item(db, item_id)
    _exigir_editable(db, usuario, it)
    p = db.get(Proyecto, it.proyecto_id)

    orden = datos.orden
    if orden is None:
        orden = (db.scalar(select(func.max(Medicion.orden))
                           .where(Medicion.item_id == item_id)) or 0) + 10

    m = Medicion(item_id=item_id, proyecto_id=it.proyecto_id, orden=orden,
                 unidad=it.unidad, responsable=usuario.id, fecha=date.today().isoformat())
    _aplicar(m, datos.model_dump(exclude_unset=True, exclude={"orden"}))

    reglas = servicios.reglas_de(p)
    prueba = mot.calcular_fila({**datos.model_dump(), "id": None}, it.unidad, reglas)
    if prueba.error and (p.reglas or {}).get("bloquear_dimension_incompatible", True):
        if "dimensional" in (prueba.error or ""):
            raise HTTPException(422, prueba.error)

    db.add(m)
    audit.registrar(db, accion="crear", entidad="medicion", entidad_id=m.id,
                    proyecto_id=it.proyecto_id,
                    resumen=f"Fila en {it.descripcion[:80]}: {prueba.sustento}",
                    usuario=usuario)
    db.commit()
    calculo = servicios.calcular_item(db, it, reglas, refrescar=True)
    db.commit()
    return {"medicion_id": m.id, "fila": prueba.a_dict(),
            "resumen": calculo["total"].a_dict()}


@router.put("/mediciones/{medicion_id}")
def actualizar_medicion(medicion_id: str, datos: DatosMedicion,
                        db: Session = Depends(obtener_sesion),
                        usuario: Usuario = Depends(security.usuario_actual)):
    m = db.get(Medicion, medicion_id)
    if not m:
        raise HTTPException(404, "La fila no existe.")
    it = _item(db, m.item_id)
    _exigir_editable(db, usuario, it)
    p = db.get(Proyecto, it.proyecto_id)

    antes = audit.instantanea(m)
    _aplicar(m, datos.model_dump(exclude_unset=True))
    m.responsable = usuario.id
    m.fecha = date.today().isoformat()

    reglas = servicios.reglas_de(p)
    calculo = servicios.calcular_item(db, it, reglas, refrescar=True)
    audit.registrar_cambio(db, entidad="medicion", entidad_id=m.id, proyecto_id=it.proyecto_id,
                           antes=antes, despues=audit.instantanea(m),
                           resumen=f"Fila editada en {it.descripcion[:80]}", usuario=usuario)
    db.commit()
    fila = next((f for f in calculo["filas"] if f["id"] == m.id), None)
    return {"fila": fila, "resumen": calculo["total"].a_dict()}


@router.delete("/mediciones/{medicion_id}")
def eliminar_medicion(medicion_id: str, db: Session = Depends(obtener_sesion),
                      usuario: Usuario = Depends(security.usuario_actual)):
    m = db.get(Medicion, medicion_id)
    if not m:
        raise HTTPException(404, "La fila no existe.")
    it = _item(db, m.item_id)
    _exigir_editable(db, usuario, it)
    audit.registrar(db, accion="eliminar", entidad="medicion", entidad_id=m.id,
                    proyecto_id=it.proyecto_id,
                    resumen=f"Fila eliminada de {it.descripcion[:80]}",
                    antes=audit.instantanea(m), usuario=usuario)
    db.delete(m)
    db.commit()
    p = db.get(Proyecto, it.proyecto_id)
    calculo = servicios.calcular_item(db, it, servicios.reglas_de(p), refrescar=True)
    db.commit()
    return {"ok": True, "resumen": calculo["total"].a_dict()}


# --------------------------------------------------------------------------- #
# Pegado masivo y repetición: la razón por la que esto gana a una hoja de Excel
# --------------------------------------------------------------------------- #

class Pegado(BaseModel):
    texto: str = Field(description="Filas separadas por salto de línea, columnas por tabulador.")
    columnas: list[str] | None = None
    reemplazar: bool = False


@router.post("/items/{item_id}/mediciones/pegar")
def pegar(item_id: str, datos: Pegado, db: Session = Depends(obtener_sesion),
          usuario: Usuario = Depends(security.usuario_actual)):
    """Pega un bloque copiado de Excel directamente en la planilla.

    Se aceptan columnas en el orden estándar de la planilla de sustento. Las
    celdas vacías se dejan VACÍAS, no en cero: es lo que distingue «no aplica»
    de «mide cero».
    """
    it = _item(db, item_id)
    _exigir_editable(db, usuario, it)
    p = db.get(Proyecto, it.proyecto_id)
    reglas = servicios.reglas_de(p)
    columnas = datos.columnas or COLUMNAS_PEGADO

    if datos.reemplazar:
        for m in list(it.mediciones):
            db.delete(m)
        db.flush()

    base = (db.scalar(select(func.max(Medicion.orden)).where(Medicion.item_id == item_id)) or 0)
    creadas, rechazadas = [], []
    for i, linea in enumerate(datos.texto.replace("\r\n", "\n").replace("\r", "\n").split("\n")):
        if not linea.strip():
            continue
        celdas = linea.split("\t") if "\t" in linea else linea.split(";")
        fila = {}
        for j, columna in enumerate(columnas):
            if j < len(celdas):
                valor = celdas[j].strip()
                fila[columna] = valor or None
        if not any(fila.get(c) for c in ("n", "veces", "largo", "ancho", "alto")):
            rechazadas.append({"linea": i + 1, "texto": linea[:120],
                               "motivo": "No trae ninguna cantidad ni dimensión."})
            continue
        prueba = mot.calcular_fila(fila, it.unidad, reglas)
        if prueba.error and "dimensional" in prueba.error:
            rechazadas.append({"linea": i + 1, "texto": linea[:120], "motivo": prueba.error})
            continue
        base += 10
        m = Medicion(item_id=item_id, proyecto_id=it.proyecto_id, orden=base,
                     unidad=it.unidad, origen="importado", responsable=usuario.id,
                     fecha=date.today().isoformat())
        _aplicar(m, {k: v for k, v in fila.items() if k in DatosMedicion.model_fields})
        db.add(m)
        creadas.append(m)

    db.flush()
    audit.registrar(db, accion="importar", entidad="item", entidad_id=it.id,
                    proyecto_id=it.proyecto_id,
                    resumen=f"Pegado de {len(creadas)} fila(s) en {it.descripcion[:80]}",
                    usuario=usuario)
    db.commit()
    calculo = servicios.calcular_item(db, it, reglas, refrescar=True)
    db.commit()
    return {"creadas": len(creadas), "rechazadas": rechazadas,
            "filas": calculo["filas"], "resumen": calculo["total"].a_dict()}


class Repeticion(BaseModel):
    medicion_ids: list[str]
    ubicacion_ids: list[str] = []
    ejes: list[str] = []
    prefijo_descripcion: str | None = None


@router.post("/items/{item_id}/mediciones/repetir")
def repetir(item_id: str, datos: Repeticion, db: Session = Depends(obtener_sesion),
            usuario: Usuario = Depends(security.usuario_actual)):
    """Repite filas por niveles y por ejes. Un piso típico se metra una vez.

    Es la operación que más tiempo ahorra: se metra el piso típico y se replica
    a los niveles 2, 3 y 4 conservando la trazabilidad de cada nivel.
    """
    it = _item(db, item_id)
    _exigir_editable(db, usuario, it)
    p = db.get(Proyecto, it.proyecto_id)

    origen = [m for m in it.mediciones if m.id in set(datos.medicion_ids)]
    if not origen:
        raise HTTPException(400, "Seleccione al menos una fila para repetir.")

    destinos_ubicacion = datos.ubicacion_ids or [None]
    destinos_eje = datos.ejes or [None]
    nombres = {u.id: u.nombre for u in db.scalars(
        select(Ubicacion).where(Ubicacion.proyecto_id == it.proyecto_id))}

    base = (db.scalar(select(func.max(Medicion.orden)).where(Medicion.item_id == item_id)) or 0)
    nuevas = 0
    for ubicacion_id in destinos_ubicacion:
        for eje in destinos_eje:
            for m in origen:
                base += 10
                etiqueta = " · ".join(x for x in [
                    datos.prefijo_descripcion,
                    nombres.get(ubicacion_id) if ubicacion_id else None,
                    f"Eje {eje}" if eje else None,
                ] if x)
                descripcion = " — ".join(x for x in [m.descripcion, etiqueta] if x) or etiqueta
                db.add(Medicion(
                    item_id=item_id, proyecto_id=it.proyecto_id, orden=base,
                    descripcion=descripcion or None,
                    ubicacion_id=ubicacion_id or m.ubicacion_id,
                    elemento_id=m.elemento_id, plano_id=m.plano_id,
                    lamina=m.lamina, eje=eje or m.eje,
                    n=m.n, veces=m.veces, largo=m.largo, ancho=m.ancho, alto=m.alto,
                    formula=m.formula, plantilla_formula=m.plantilla_formula,
                    variables=dict(m.variables or {}), unidad=m.unidad, signo=m.signo,
                    origen=m.origen, supuesto=m.supuesto,
                    responsable=usuario.id, fecha=date.today().isoformat(),
                ))
                nuevas += 1

    audit.registrar(db, accion="crear", entidad="item", entidad_id=it.id,
                    proyecto_id=it.proyecto_id,
                    resumen=f"{nuevas} fila(s) repetidas en {it.descripcion[:80]}",
                    usuario=usuario)
    db.commit()
    calculo = servicios.calcular_item(db, it, servicios.reglas_de(p), refrescar=True)
    db.commit()
    return {"creadas": nuevas, "filas": calculo["filas"],
            "resumen": calculo["total"].a_dict()}


class Vanos(BaseModel):
    vanos: list[dict]
    familia: str | None = None
    insertar: bool = True


@router.post("/items/{item_id}/vanos")
def descontar_vanos(item_id: str, datos: Vanos, db: Session = Depends(obtener_sesion),
                    usuario: Usuario = Depends(security.usuario_actual)):
    """Aplica el descuento de vanos con el umbral de la familia normativa.

    Los vanos que NO se descuentan también se devuelven, con la leyenda que
    explica por qué. El revisor busca justamente esa leyenda.
    """
    it = _item(db, item_id)
    _exigir_editable(db, usuario, it)
    p = db.get(Proyecto, it.proyecto_id)
    reglas = servicios.reglas_de(p)
    familia = datos.familia or it.familia_descuento or normas.familia_por_defecto(
        it.especialidad, it.descripcion)

    evaluados = mot.filas_deduccion_vanos(datos.vanos, familia, reglas)
    creadas = 0
    if datos.insertar:
        base = (db.scalar(select(func.max(Medicion.orden))
                          .where(Medicion.item_id == item_id)) or 0)
        for v in evaluados:
            if not v.get("aplica"):
                continue
            base += 10
            db.add(Medicion(
                item_id=item_id, proyecto_id=it.proyecto_id, orden=base,
                descripcion=f"Menos {v['descripcion']}",
                n=v.get("n"), ancho=v.get("ancho"), alto=v.get("alto"),
                signo=-1, unidad=it.unidad, origen="ingresado",
                observacion=v.get("motivo"), responsable=usuario.id,
                fecha=date.today().isoformat(),
            ))
            creadas += 1
        it.familia_descuento = familia
        db.commit()

    calculo = servicios.calcular_item(db, it, reglas, refrescar=True)
    db.commit()
    f = normas.FAMILIAS[familia]
    return {
        "familia": {"clave": f.clave, "nombre": f.nombre, "codigo": f.codigo,
                    "cita": f.cita, "umbral_m2": str(f.umbral_m2), "nota": f.nota},
        "evaluados": evaluados,
        "creadas": creadas,
        "resumen": calculo["total"].a_dict(),
        "advertencia_umbral": normas.UMBRAL_MITO,
    }


@router.post("/items/{item_id}/formula/probar")
def probar_formula(item_id: str, datos: dict, db: Session = Depends(obtener_sesion),
                   usuario: Usuario = Depends(security.usuario_actual)):
    """Evalúa una fórmula contra valores de prueba antes de guardarla."""
    it = _item(db, item_id)
    security.exigir(db, usuario, it.proyecto_id, "ver")
    expresion = datos.get("formula") or ""
    ok, error, variables = formulas.validar(expresion)
    if not ok:
        return {"ok": False, "error": error}
    resultado = formulas.evaluar(expresion, datos.get("variables") or {})
    return {"ok": True, "variables": variables, "resultado": resultado.a_dict(),
            "unidad": it.unidad}
