"""Presupuesto, análisis de precios unitarios, insumos y curva S."""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import audit, security, servicios
from ..db import obtener_sesion
from ..models import ApuDetalle, Insumo, Item, Proyecto, Usuario
from ..motor import costos, paises
from ..motor.redondeo import dec, redondear
from .proyectos import obtener

router = APIRouter(tags=["presupuesto"])


@router.get("/proyectos/{proyecto_id}/presupuesto")
def presupuesto(proyecto_id: str, version_id: str | None = None,
                db: Session = Depends(obtener_sesion),
                usuario: Usuario = Depends(security.usuario_actual)):
    p = obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "ver")
    reglas_proyecto = p.reglas or {}
    reglas = servicios.reglas_de(p)
    datos = servicios.arbol(db, p, version_id=version_id or p.version_actual_id)
    db.commit()

    impuesto = reglas_proyecto.get("impuesto") or {"nombre": "IGV", "tasa": "18"}
    pie = costos.resumen(
        datos["costo_directo"],
        gg_pct=reglas_proyecto.get("gastos_generales_pct", 0),
        utilidad_pct=reglas_proyecto.get("utilidad_pct", 0),
        impuesto_pct=impuesto.get("tasa", 0),
        nombre_impuesto=impuesto.get("nombre", "IGV"),
        reglas=reglas,
    )

    planas = servicios.aplanar(datos["items"])
    sin_precio = [{"id": n["id"], "item": n["item"], "descripcion": n["descripcion"]}
                  for n in planas
                  if n["tipo"] == "partida" and not (n.get("precio_unitario") or "").strip()]

    return {
        "proyecto": {"id": p.id, "nombre": p.nombre, "moneda": p.moneda,
                     "moneda_formato": paises.moneda(p.pais)},
        "items": datos["items"],
        "por_especialidad": datos["por_especialidad"],
        "resumen": pie,
        "sin_precio": sin_precio[:100],
        "total_sin_precio": len(sin_precio),
    }


@router.get("/proyectos/{proyecto_id}/insumos")
def lista_insumos(proyecto_id: str, db: Session = Depends(obtener_sesion),
                  usuario: Usuario = Depends(security.usuario_actual)):
    """Consolidado de insumos: cuánto se consume de cada cosa en toda la obra."""
    p = obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "ver")
    reglas = servicios.reglas_de(p)
    datos = servicios.arbol(db, p)
    db.commit()

    metrados = {n["id"]: dec(n.get("metrado") or 0)
                for n in servicios.aplanar(datos["items"]) if n["tipo"] == "partida"}
    if not metrados:
        return {"insumos": [], "por_tipo": {}, "total": "0"}

    filas = list(db.scalars(select(ApuDetalle).where(ApuDetalle.item_id.in_(metrados.keys()))))
    consumo: dict[tuple, dict] = {}
    for f in filas:
        metrado = metrados.get(f.item_id, Decimal(0))
        cantidad = dec(f.cantidad or 0) * metrado
        clave = (f.insumo_id or f.descripcion, f.unidad)
        actual = consumo.setdefault(clave, {
            "descripcion": f.descripcion, "unidad": f.unidad, "tipo": f.tipo,
            "cantidad": Decimal(0), "precio": dec(f.precio or 0),
        })
        actual["cantidad"] += cantidad

    salida, por_tipo, total = [], defaultdict(Decimal), Decimal(0)
    for datos_insumo in consumo.values():
        parcial = reglas.parcial(datos_insumo["cantidad"] * datos_insumo["precio"])
        total += parcial
        por_tipo[datos_insumo["tipo"]] += parcial
        salida.append({**datos_insumo,
                       "cantidad": str(redondear(datos_insumo["cantidad"], 4)),
                       "precio": str(datos_insumo["precio"]),
                       "parcial": str(parcial)})
    salida.sort(key=lambda x: (x["tipo"], -float(x["parcial"])))
    return {"insumos": salida,
            "por_tipo": {k: str(v) for k, v in por_tipo.items()},
            "total": str(reglas.parcial(total)),
            "nombres_tipo": costos.TIPOS}


@router.get("/items/{item_id}/apu")
def ver_apu(item_id: str, db: Session = Depends(obtener_sesion),
            usuario: Usuario = Depends(security.usuario_actual)):
    it = db.get(Item, item_id)
    if not it:
        raise HTTPException(404, "Partida no encontrada.")
    security.exigir(db, usuario, it.proyecto_id, "ver")
    p = db.get(Proyecto, it.proyecto_id)
    filas = list(db.scalars(select(ApuDetalle).where(ApuDetalle.item_id == item_id)
                            .order_by(ApuDetalle.orden)))
    rendimiento = next((f.rendimiento for f in filas if f.rendimiento), None)
    resultado = costos.analisis(
        [{"tipo": f.tipo, "descripcion": f.descripcion, "unidad": f.unidad,
          "cuadrilla": f.cuadrilla, "cantidad": f.cantidad, "precio": f.precio,
          "rendimiento": f.rendimiento} for f in filas],
        rendimiento_partida=rendimiento, reglas=servicios.reglas_de(p))
    calculo = servicios.calcular_item(db, it, servicios.reglas_de(p))
    db.commit()
    metrado = calculo["total"].total
    return {
        "item": {"id": it.id, "codigo": it.codigo, "descripcion": it.descripcion,
                 "unidad": it.unidad, "metrado": str(metrado),
                 "precio_unitario": it.precio_unitario},
        "apu": resultado,
        "ids": [f.id for f in filas],
        "parcial": str(redondear(metrado * dec(resultado["pu"]), 2)),
        "moneda": p.moneda,
    }


class LineaApuEntrada(BaseModel):
    tipo: str = "MAT"
    descripcion: str
    unidad: str = "und"
    cuadrilla: str | None = None
    cantidad: str = "0"
    precio: str = "0"
    rendimiento: str | None = None
    insumo_id: str | None = None


class ApuEntrada(BaseModel):
    lineas: list[LineaApuEntrada]
    aplicar_pu: bool = True


@router.put("/items/{item_id}/apu")
def guardar_apu(item_id: str, datos: ApuEntrada, db: Session = Depends(obtener_sesion),
                usuario: Usuario = Depends(security.usuario_actual)):
    it = db.get(Item, item_id)
    if not it:
        raise HTTPException(404, "Partida no encontrada.")
    security.exigir(db, usuario, it.proyecto_id, "editar")
    p = db.get(Proyecto, it.proyecto_id)

    for viejo in db.scalars(select(ApuDetalle).where(ApuDetalle.item_id == item_id)):
        db.delete(viejo)
    db.flush()

    for i, l in enumerate(datos.lineas):
        db.add(ApuDetalle(item_id=item_id, orden=i * 10, **l.model_dump()))

    rendimiento = next((l.rendimiento for l in datos.lineas if l.rendimiento), None)
    resultado = costos.analisis([l.model_dump() for l in datos.lineas],
                                rendimiento_partida=rendimiento,
                                reglas=servicios.reglas_de(p))
    if datos.aplicar_pu:
        it.precio_unitario = resultado["pu"]

    audit.registrar(db, accion="editar", entidad="apu", entidad_id=item_id,
                    proyecto_id=it.proyecto_id,
                    resumen=f"APU de {it.descripcion[:80]}: PU = {resultado['pu']}",
                    usuario=usuario)
    db.commit()
    return {"apu": resultado, "precio_unitario": it.precio_unitario}


@router.get("/proyectos/{proyecto_id}/curva-s")
def curva(proyecto_id: str, meses: int = 12, db: Session = Depends(obtener_sesion),
          usuario: Usuario = Depends(security.usuario_actual)):
    p = obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "ver")
    datos = servicios.arbol(db, p)
    db.commit()
    partidas = [n for n in servicios.aplanar(datos["items"]) if n["tipo"] == "partida"]
    return costos.curva_s(partidas, meses, servicios.reglas_de(p))


@router.get("/proyectos/{proyecto_id}/adicionales")
def adicionales(proyecto_id: str, db: Session = Depends(obtener_sesion),
                usuario: Usuario = Depends(security.usuario_actual)):
    """Adicionales y deductivos: diferencia entre lo contratado y lo previsto."""
    p = obtener(db, proyecto_id)
    security.exigir(db, usuario, proyecto_id, "ver")
    reglas = servicios.reglas_de(p)
    datos = servicios.arbol(db, p)
    db.commit()

    filas, total_adicional, total_deductivo = [], Decimal(0), Decimal(0)
    for n in servicios.aplanar(datos["items"]):
        if n["tipo"] != "partida" or not n.get("cantidad_contratada"):
            continue
        prevista = dec(n.get("metrado") or 0)
        contratada = dec(n["cantidad_contratada"])
        diferencia = prevista - contratada
        if diferencia == 0:
            continue
        pu = dec(n.get("precio_unitario") or 0)
        monto = reglas.parcial(diferencia * pu)
        if monto > 0:
            total_adicional += monto
        else:
            total_deductivo += monto
        filas.append({
            "id": n["id"], "item": n["item"], "descripcion": n["descripcion"],
            "unidad": n["unidad"], "contratada": str(contratada),
            "prevista": str(prevista), "diferencia": str(diferencia),
            "precio_unitario": str(pu), "monto": str(monto),
            "clase": "adicional" if monto > 0 else "deductivo",
        })
    return {"filas": filas,
            "total_adicional": str(reglas.parcial(total_adicional)),
            "total_deductivo": str(reglas.parcial(total_deductivo)),
            "neto": str(reglas.parcial(total_adicional + total_deductivo))}
