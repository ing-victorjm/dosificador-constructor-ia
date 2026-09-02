"""Proyectos, estructura física (edificio → nivel → ambiente), elementos y versiones."""
from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import audit, security, servicios
from ..db import obtener_sesion
from ..models import (
    Archivo, Elemento, Item, MiembroProyecto, Observacion, Proyecto, Ubicacion, Usuario, Version,
)
from ..motor import especialidades, paises

router = APIRouter(tags=["proyectos"])

TIPOS_UBICACION = ["edificio", "bloque", "sector", "nivel", "ambiente", "tramo", "progresiva"]


class DatosProyecto(BaseModel):
    nombre: str = Field(min_length=3, max_length=300)
    codigo: str | None = Field(default=None, max_length=60)
    cliente: str | None = None
    ubicacion_texto: str | None = None
    responsable: str | None = None
    tipo: str = "edificio"
    pisos: int = Field(default=1, ge=0, le=200)
    sotanos: int = Field(default=0, ge=0, le=20)
    sectores: int = Field(default=1, ge=1, le=100)
    pais: str = "PE"
    moneda: str | None = None
    sistema_unidades: str = "metrico"
    etapa: str = "expediente"
    fecha: str | None = None
    normativa: str | None = None
    notas: str | None = None
    generar_estructura: bool = True


class CambioProyecto(BaseModel):
    nombre: str | None = None
    codigo: str | None = None
    cliente: str | None = None
    ubicacion_texto: str | None = None
    responsable: str | None = None
    tipo: str | None = None
    pisos: int | None = None
    sotanos: int | None = None
    sectores: int | None = None
    pais: str | None = None
    moneda: str | None = None
    sistema_unidades: str | None = None
    etapa: str | None = None
    fecha: str | None = None
    normativa: str | None = None
    notas: str | None = None
    estado: str | None = None
    reglas: dict | None = None


def obtener(db: Session, proyecto_id: str) -> Proyecto:
    p = db.get(Proyecto, proyecto_id)
    if not p:
        raise HTTPException(404, "El proyecto no existe o fue eliminado.")
    return p


def _publico(p: Proyecto) -> dict:
    return {
        "id": p.id, "codigo": p.codigo, "nombre": p.nombre, "cliente": p.cliente,
        "ubicacion_texto": p.ubicacion_texto, "responsable": p.responsable,
        "tipo": p.tipo, "pisos": p.pisos, "sotanos": p.sotanos, "sectores": p.sectores,
        "pais": p.pais, "normativa": p.normativa, "moneda": p.moneda,
        "sistema_unidades": p.sistema_unidades, "etapa": p.etapa, "fecha": p.fecha,
        "estado": p.estado, "reglas": p.reglas or {}, "notas": p.notas,
        "version_actual_id": p.version_actual_id,
        "creado_en": p.creado_en.isoformat() if p.creado_en else None,
        "actualizado_en": p.actualizado_en.isoformat() if p.actualizado_en else None,
        "moneda_formato": paises.moneda(p.pais),
    }


# --------------------------------------------------------------------------- #
# Proyectos
# --------------------------------------------------------------------------- #

@router.get("/proyectos")
def listar(db: Session = Depends(obtener_sesion),
           usuario: Usuario = Depends(security.usuario_actual),
           incluir_resumen: bool = Query(default=True)):
    q = select(Proyecto).where(Proyecto.estado != "eliminado")
    if usuario.rol != "administrador" and usuario.empresa_id:
        q = q.where(Proyecto.empresa_id == usuario.empresa_id)
    proyectos = list(db.scalars(q.order_by(Proyecto.actualizado_en.desc())))
    salida = []
    for p in proyectos:
        fila = _publico(p)
        if incluir_resumen:
            fila["resumen"] = servicios.resumen_proyecto(db, p)
        salida.append(fila)
    return {"proyectos": salida, "total": len(salida)}


@router.post("/proyectos", status_code=201)
def crear(datos: DatosProyecto, db: Session = Depends(obtener_sesion),
          usuario: Usuario = Depends(security.usuario_actual)):
    security.exigir(db, usuario, None, "crear")
    pais = paises.por_codigo(datos.pais)
    codigo = (datos.codigo or "").strip() or _codigo_automatico(db)

    p = Proyecto(
        empresa_id=usuario.empresa_id,
        codigo=codigo, nombre=datos.nombre.strip(), cliente=datos.cliente,
        ubicacion_texto=datos.ubicacion_texto,
        responsable=datos.responsable or usuario.nombre,
        tipo=datos.tipo, pisos=datos.pisos, sotanos=datos.sotanos, sectores=datos.sectores,
        pais=datos.pais.upper(),
        normativa=datos.normativa or (pais.get("normas") or [{}])[0].get("nombre"),
        moneda=(datos.moneda or pais["moneda"]["iso"]).upper(),
        sistema_unidades=datos.sistema_unidades,
        etapa=datos.etapa, fecha=datos.fecha or date.today().isoformat(),
        reglas=paises.reglas_iniciales(datos.pais),
        notas=datos.notas, creado_por=usuario.id,
    )
    db.add(p)
    db.flush()

    v = Version(proyecto_id=p.id, nombre="v1", numero=1,
                descripcion="Versión inicial", creada_por=usuario.id)
    db.add(v)
    db.flush()
    p.version_actual_id = v.id

    db.add(MiembroProyecto(proyecto_id=p.id, usuario_id=usuario.id,
                           rol="administrador" if usuario.rol == "administrador" else "metrador"))

    if datos.generar_estructura:
        _generar_estructura(db, p)

    audit.registrar(db, accion="crear", entidad="proyecto", entidad_id=p.id,
                    proyecto_id=p.id, resumen=f"Proyecto creado: {p.nombre}",
                    despues=audit.instantanea(p), usuario=usuario)
    db.commit()
    return {"proyecto": _publico(p)}


def _codigo_automatico(db: Session) -> str:
    n = (db.scalar(select(func.count(Proyecto.id))) or 0) + 1
    return f"PRY-{datetime.now(timezone.utc).year}-{n:03d}"


def _generar_estructura(db: Session, p: Proyecto) -> None:
    """Crea edificio → sectores → niveles según los datos del proyecto."""
    edificio = Ubicacion(proyecto_id=p.id, tipo="edificio", nombre="Edificio principal",
                         codigo="ED-01", orden=1)
    db.add(edificio)
    db.flush()

    padres = [edificio]
    if p.sectores > 1:
        padres = []
        for s in range(1, p.sectores + 1):
            sec = Ubicacion(proyecto_id=p.id, padre_id=edificio.id, tipo="sector",
                            nombre=f"Sector {s}", codigo=f"S-{s:02d}", orden=s)
            db.add(sec)
            db.flush()
            padres.append(sec)

    for padre in padres:
        orden = 0
        for s in range(p.sotanos, 0, -1):
            orden += 1
            db.add(Ubicacion(proyecto_id=p.id, padre_id=padre.id, tipo="nivel",
                             nombre=f"Sótano {s}", codigo=f"S{s}", orden=orden,
                             cota=f"-{s * 2.8:.2f}", altura_piso="2.80"))
        for n in range(1, p.pisos + 1):
            orden += 1
            nombre = "Piso 1" if n == 1 else f"Piso {n}"
            db.add(Ubicacion(proyecto_id=p.id, padre_id=padre.id, tipo="nivel",
                             nombre=nombre, codigo=f"N{n}", orden=orden,
                             cota=f"{(n - 1) * 2.8:.2f}", altura_piso="2.80"))
        orden += 1
        db.add(Ubicacion(proyecto_id=p.id, padre_id=padre.id, tipo="nivel",
                         nombre="Azotea", codigo="AZ", orden=orden,
                         cota=f"{p.pisos * 2.8:.2f}"))


@router.get("/proyectos/{proyecto_id}")
def ver(proyecto_id: str, db: Session = Depends(obtener_sesion),
        usuario: Usuario = Depends(security.usuario_actual)):
    p = obtener(db, proyecto_id)
    rol = security.exigir(db, usuario, proyecto_id, "ver")
    versiones = list(db.scalars(select(Version).where(Version.proyecto_id == p.id)
                                .order_by(Version.numero)))
    return {
        "proyecto": _publico(p),
        "rol": rol,
        "permisos": sorted(security.PERMISOS.get(rol, set())),
        "ubicaciones": servicios.arbol_ubicaciones(db, p.id),
        "versiones": [{"id": v.id, "nombre": v.nombre, "numero": v.numero,
                       "estado": v.estado, "descripcion": v.descripcion,
                       "creado_en": v.creado_en.isoformat() if v.creado_en else None}
                      for v in versiones],
        "resumen": servicios.resumen_proyecto(db, p),
        "archivos": db.scalar(select(func.count(Archivo.id))
                              .where(Archivo.proyecto_id == p.id)) or 0,
        "observaciones_abiertas": db.scalar(
            select(func.count(Observacion.id))
            .where(Observacion.proyecto_id == p.id, Observacion.estado == "abierta")) or 0,
    }


@router.put("/proyectos/{proyecto_id}")
def actualizar(proyecto_id: str, cambio: CambioProyecto,
               db: Session = Depends(obtener_sesion),
               usuario: Usuario = Depends(security.usuario_actual)):
    p = obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "editar")
    antes = audit.instantanea(p)
    for campo, valor in cambio.model_dump(exclude_none=True).items():
        if campo == "reglas":
            p.reglas = {**(p.reglas or {}), **valor}
        else:
            setattr(p, campo, valor)
    audit.registrar_cambio(db, entidad="proyecto", entidad_id=p.id, proyecto_id=p.id,
                           antes=antes, despues=audit.instantanea(p),
                           resumen="Datos del proyecto actualizados", usuario=usuario)
    db.commit()
    return {"proyecto": _publico(p)}


@router.delete("/proyectos/{proyecto_id}")
def eliminar(proyecto_id: str, definitivo: bool = False,
             db: Session = Depends(obtener_sesion),
             usuario: Usuario = Depends(security.usuario_actual)):
    p = obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "eliminar")
    audit.registrar(db, accion="eliminar", entidad="proyecto", entidad_id=p.id,
                    proyecto_id=p.id, resumen=f"Proyecto eliminado: {p.nombre}",
                    antes=audit.instantanea(p), usuario=usuario)
    if definitivo:
        db.delete(p)
    else:
        p.estado = "eliminado"
    db.commit()
    return {"ok": True, "definitivo": definitivo}


@router.get("/proyectos/{proyecto_id}/panel")
def panel(proyecto_id: str, db: Session = Depends(obtener_sesion),
          usuario: Usuario = Depends(security.usuario_actual)):
    """Datos del panel general del proyecto."""
    p = obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "ver")
    a = servicios.arbol(db, p)
    planos = servicios.aplanar(a["items"])

    # Comparación prevista / contratada / ejecutada
    comparacion = []
    for n in planos:
        if n["tipo"] != "partida":
            continue
        if n.get("cantidad_contratada") or n.get("cantidad_ejecutada"):
            comparacion.append({
                "id": n["id"], "item": n["item"], "descripcion": n["descripcion"],
                "unidad": n["unidad"], "prevista": n.get("metrado"),
                "contratada": n.get("cantidad_contratada"),
                "ejecutada": n.get("cantidad_ejecutada"),
            })

    pendientes = [
        {"id": n["id"], "item": n["item"], "descripcion": n["descripcion"],
         "estado": n["estado"], "unidad": n["unidad"], "metrado": n.get("metrado"),
         "motivo": _motivo_pendiente(n)}
        for n in planos
        if n["tipo"] == "partida" and _motivo_pendiente(n)
    ]

    return {
        "proyecto": _publico(p),
        "resumen": {"costo_directo": a["costo_directo"], "avance_pct": a["avance_pct"],
                    "conteo": a["conteo"]},
        "por_especialidad": a["por_especialidad"],
        "pendientes": pendientes[:50],
        "total_pendientes": len(pendientes),
        "comparacion": comparacion[:50],
        "especialidades": especialidades.ESPECIALIDADES,
    }


def _motivo_pendiente(n: dict) -> str | None:
    r = n.get("resumen") or {}
    if r.get("origen") == "vacio":
        return "Sin metrado: la partida no tiene ninguna fila de sustento."
    if r.get("filas_con_error"):
        return f"{r['filas_con_error']} fila(s) con error de cálculo."
    if r.get("filas_incompletas"):
        return f"{r['filas_incompletas']} fila(s) con datos faltantes."
    if n.get("estado") == "observado":
        return "Partida observada, pendiente de levantar."
    if r.get("origen") == "manual":
        return "Cantidad ingresada a mano, sin sustento."
    return None


# --------------------------------------------------------------------------- #
# Estructura física
# --------------------------------------------------------------------------- #

class DatosUbicacion(BaseModel):
    tipo: str = "nivel"
    nombre: str = Field(min_length=1, max_length=200)
    codigo: str | None = None
    padre_id: str | None = None
    orden: int = 0
    cota: str | None = None
    altura_piso: str | None = None
    area: str | None = None
    perimetro: str | None = None
    atributos: dict | None = None


@router.get("/proyectos/{proyecto_id}/ubicaciones")
def listar_ubicaciones(proyecto_id: str, db: Session = Depends(obtener_sesion),
                       usuario: Usuario = Depends(security.usuario_actual)):
    obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "ver")
    return {"ubicaciones": servicios.arbol_ubicaciones(db, proyecto_id),
            "tipos": TIPOS_UBICACION}


@router.post("/proyectos/{proyecto_id}/ubicaciones", status_code=201)
def crear_ubicacion(proyecto_id: str, datos: DatosUbicacion,
                    db: Session = Depends(obtener_sesion),
                    usuario: Usuario = Depends(security.usuario_actual)):
    obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "editar")
    if datos.tipo not in TIPOS_UBICACION:
        raise HTTPException(400, f"Tipo de ubicación no válido: {datos.tipo}")
    if datos.padre_id and not db.get(Ubicacion, datos.padre_id):
        raise HTTPException(400, "La ubicación padre no existe.")
    u = Ubicacion(proyecto_id=proyecto_id, **datos.model_dump(exclude_none=True))
    db.add(u)
    audit.registrar(db, accion="crear", entidad="ubicacion", entidad_id=u.id,
                    proyecto_id=proyecto_id, resumen=f"Nueva ubicación: {u.nombre}",
                    usuario=usuario)
    db.commit()
    return {"ubicacion": {"id": u.id, "nombre": u.nombre, "tipo": u.tipo}}


@router.put("/proyectos/{proyecto_id}/ubicaciones/{ubicacion_id}")
def actualizar_ubicacion(proyecto_id: str, ubicacion_id: str, datos: DatosUbicacion,
                         db: Session = Depends(obtener_sesion),
                         usuario: Usuario = Depends(security.usuario_actual)):
    security.exigir(db, usuario, proyecto_id, "editar")
    u = db.get(Ubicacion, ubicacion_id)
    if not u or u.proyecto_id != proyecto_id:
        raise HTTPException(404, "Ubicación no encontrada.")
    if datos.padre_id == ubicacion_id:
        raise HTTPException(400, "Una ubicación no puede ser su propio padre.")
    antes = audit.instantanea(u)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(u, campo, valor)
    audit.registrar_cambio(db, entidad="ubicacion", entidad_id=u.id, proyecto_id=proyecto_id,
                           antes=antes, despues=audit.instantanea(u),
                           resumen=f"Ubicación editada: {u.nombre}", usuario=usuario)
    db.commit()
    return {"ok": True}


@router.delete("/proyectos/{proyecto_id}/ubicaciones/{ubicacion_id}")
def eliminar_ubicacion(proyecto_id: str, ubicacion_id: str,
                       db: Session = Depends(obtener_sesion),
                       usuario: Usuario = Depends(security.usuario_actual)):
    security.exigir(db, usuario, proyecto_id, "eliminar")
    u = db.get(Ubicacion, ubicacion_id)
    if not u or u.proyecto_id != proyecto_id:
        raise HTTPException(404, "Ubicación no encontrada.")
    audit.registrar(db, accion="eliminar", entidad="ubicacion", entidad_id=u.id,
                    proyecto_id=proyecto_id, resumen=f"Ubicación eliminada: {u.nombre}",
                    antes=audit.instantanea(u), usuario=usuario)
    db.delete(u)
    db.commit()
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Elementos
# --------------------------------------------------------------------------- #

class DatosElemento(BaseModel):
    tipo: str
    marca: str | None = None
    nombre: str | None = None
    especialidad: str = "estructuras"
    ubicacion_id: str | None = None
    cantidad: str = "1"
    propiedades: dict = {}
    plano_id: str | None = None
    origen: str = "ingresado"
    confianza: str | None = None


@router.get("/proyectos/{proyecto_id}/elementos")
def listar_elementos(proyecto_id: str, tipo: str | None = None,
                     ubicacion_id: str | None = None,
                     db: Session = Depends(obtener_sesion),
                     usuario: Usuario = Depends(security.usuario_actual)):
    security.exigir(db, usuario, proyecto_id, "ver")
    q = select(Elemento).where(Elemento.proyecto_id == proyecto_id)
    if tipo:
        q = q.where(Elemento.tipo == tipo)
    if ubicacion_id:
        q = q.where(Elemento.ubicacion_id == ubicacion_id)
    filas = list(db.scalars(q.order_by(Elemento.tipo, Elemento.marca)))
    return {"elementos": [{
        "id": e.id, "tipo": e.tipo, "marca": e.marca, "nombre": e.nombre,
        "especialidad": e.especialidad, "ubicacion_id": e.ubicacion_id,
        "cantidad": e.cantidad, "propiedades": e.propiedades or {},
        "plano_id": e.plano_id, "origen": e.origen, "confianza": e.confianza,
        "metrado": e.metrado,
    } for e in filas],
        "tipos": especialidades.TIPOS_ELEMENTO}


@router.post("/proyectos/{proyecto_id}/elementos", status_code=201)
def crear_elemento(proyecto_id: str, datos: DatosElemento,
                   db: Session = Depends(obtener_sesion),
                   usuario: Usuario = Depends(security.usuario_actual)):
    obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "crear")
    e = Elemento(proyecto_id=proyecto_id, **datos.model_dump())
    db.add(e)
    audit.registrar(db, accion="crear", entidad="elemento", entidad_id=e.id,
                    proyecto_id=proyecto_id,
                    resumen=f"Elemento {e.tipo} {e.marca or ''}".strip(), usuario=usuario)
    db.commit()
    return {"elemento": {"id": e.id, "tipo": e.tipo, "marca": e.marca}}


@router.put("/proyectos/{proyecto_id}/elementos/{elemento_id}")
def actualizar_elemento(proyecto_id: str, elemento_id: str, datos: DatosElemento,
                        db: Session = Depends(obtener_sesion),
                        usuario: Usuario = Depends(security.usuario_actual)):
    security.exigir(db, usuario, proyecto_id, "editar")
    e = db.get(Elemento, elemento_id)
    if not e or e.proyecto_id != proyecto_id:
        raise HTTPException(404, "Elemento no encontrado.")
    antes = audit.instantanea(e)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(e, campo, valor)
    audit.registrar_cambio(db, entidad="elemento", entidad_id=e.id, proyecto_id=proyecto_id,
                           antes=antes, despues=audit.instantanea(e),
                           resumen=f"Elemento editado: {e.marca or e.tipo}", usuario=usuario)
    db.commit()
    return {"ok": True}


@router.delete("/proyectos/{proyecto_id}/elementos/{elemento_id}")
def eliminar_elemento(proyecto_id: str, elemento_id: str,
                      db: Session = Depends(obtener_sesion),
                      usuario: Usuario = Depends(security.usuario_actual)):
    security.exigir(db, usuario, proyecto_id, "eliminar")
    e = db.get(Elemento, elemento_id)
    if not e or e.proyecto_id != proyecto_id:
        raise HTTPException(404, "Elemento no encontrado.")
    db.delete(e)
    db.commit()
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Versiones
# --------------------------------------------------------------------------- #

class DatosVersion(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    copiar_metrados: bool = True


@router.post("/proyectos/{proyecto_id}/versiones", status_code=201)
def crear_version(proyecto_id: str, datos: DatosVersion,
                  db: Session = Depends(obtener_sesion),
                  usuario: Usuario = Depends(security.usuario_actual)):
    """Congela la versión vigente y abre una nueva sobre una copia del metrado."""
    p = obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "crear")

    actual = db.get(Version, p.version_actual_id) if p.version_actual_id else None
    if actual:
        actual.instantanea = servicios.arbol(db, p, version_id=actual.id, con_filas=True)
        actual.estado = "congelada"
        actual.congelada_en = datetime.now(timezone.utc)

    numero = (db.scalar(select(func.max(Version.numero))
                        .where(Version.proyecto_id == proyecto_id)) or 0) + 1
    nueva = Version(proyecto_id=proyecto_id, numero=numero,
                    nombre=datos.nombre or f"v{numero}",
                    descripcion=datos.descripcion, creada_por=usuario.id)
    db.add(nueva)
    db.flush()

    if datos.copiar_metrados and actual:
        _copiar_items(db, proyecto_id, actual.id, nueva.id)

    p.version_actual_id = nueva.id
    audit.registrar(db, accion="crear", entidad="version", entidad_id=nueva.id,
                    proyecto_id=proyecto_id,
                    resumen=f"Nueva versión {nueva.nombre}", usuario=usuario)
    db.commit()
    return {"version": {"id": nueva.id, "nombre": nueva.nombre, "numero": nueva.numero}}


def _copiar_items(db: Session, proyecto_id: str, origen_id: str, destino_id: str) -> None:
    from ..models import Medicion
    items = list(db.scalars(select(Item).where(Item.proyecto_id == proyecto_id,
                                               Item.version_id == origen_id)
                            .order_by(Item.orden)))
    mapa: dict[str, str] = {}
    for it in items:
        copia = Item(
            proyecto_id=proyecto_id, version_id=destino_id, padre_id=None,
            catalogo_id=it.catalogo_id, tipo=it.tipo, codigo=it.codigo,
            descripcion=it.descripcion, unidad=it.unidad, especialidad=it.especialidad,
            orden=it.orden, desperdicio_pct=it.desperdicio_pct,
            cantidad_manual=it.cantidad_manual, precio_unitario=it.precio_unitario,
            estado="borrador", familia_descuento=it.familia_descuento,
            regla_medicion=it.regla_medicion, etiqueta_fuente=it.etiqueta_fuente,
            reglas=dict(it.reglas or {}),
        )
        db.add(copia)
        db.flush()
        mapa[it.id] = copia.id
    for it in items:
        if it.padre_id and it.padre_id in mapa:
            db.get(Item, mapa[it.id]).padre_id = mapa[it.padre_id]
    for it in items:
        for m in it.mediciones:
            db.add(Medicion(
                item_id=mapa[it.id], proyecto_id=proyecto_id,
                ubicacion_id=m.ubicacion_id, elemento_id=m.elemento_id,
                plano_id=m.plano_id, orden=m.orden, descripcion=m.descripcion,
                eje=m.eje, lamina=m.lamina, n=m.n, veces=m.veces, largo=m.largo,
                ancho=m.ancho, alto=m.alto, formula=m.formula,
                plantilla_formula=m.plantilla_formula, variables=dict(m.variables or {}),
                unidad=m.unidad, signo=m.signo, origen=m.origen, supuesto=m.supuesto,
                estado="borrador", responsable=m.responsable, fecha=m.fecha,
                observacion=m.observacion,
            ))


@router.get("/proyectos/{proyecto_id}/versiones/comparar")
def comparar_versiones(proyecto_id: str, a: str, b: str,
                       db: Session = Depends(obtener_sesion),
                       usuario: Usuario = Depends(security.usuario_actual)):
    """Compara dos versiones partida por partida."""
    p = obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "ver")
    from ..motor.redondeo import dec

    def snapshot(version_id: str) -> dict[str, dict]:
        v = db.get(Version, version_id)
        if not v or v.proyecto_id != proyecto_id:
            raise HTTPException(404, "Versión no encontrada.")
        datos = v.instantanea or servicios.arbol(db, p, version_id=version_id, con_filas=True)
        return {n["item"] + "|" + (n.get("codigo") or "") + "|" + n["descripcion"]: n
                for n in servicios.aplanar(datos["items"]) if n["tipo"] == "partida"}

    sa, sb = snapshot(a), snapshot(b)
    filas = []
    for clave in sorted(set(sa) | set(sb)):
        na, nb = sa.get(clave), sb.get(clave)
        ma = dec(na.get("metrado") or 0) if na else None
        mb = dec(nb.get("metrado") or 0) if nb else None
        if na and nb:
            estado = "igual" if ma == mb else "modificada"
        else:
            estado = "eliminada" if na else "agregada"
        if estado == "igual":
            continue
        base = nb or na
        filas.append({
            "item": base["item"], "codigo": base.get("codigo"),
            "descripcion": base["descripcion"], "unidad": base.get("unidad"),
            "especialidad": base.get("especialidad"),
            "metrado_a": None if ma is None else str(ma),
            "metrado_b": None if mb is None else str(mb),
            "diferencia": None if (ma is None or mb is None) else str(mb - ma),
            "estado": estado,
        })
    return {"comparacion": filas, "resumen": {
        "agregadas": sum(1 for f in filas if f["estado"] == "agregada"),
        "eliminadas": sum(1 for f in filas if f["estado"] == "eliminada"),
        "modificadas": sum(1 for f in filas if f["estado"] == "modificada"),
    }}
