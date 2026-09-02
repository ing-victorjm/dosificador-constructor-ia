"""Servicios: puente entre la base de datos y el motor de cálculo.

Los routers no calculan y el motor no toca la base de datos. Aquí se cargan las
filas, se llama al motor y se arma el árbol con los códigos de ítem calculados.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Item, Medicion, Proyecto, Ubicacion
from .motor import especialidades, medicion as mot
from .motor.redondeo import ReglasRedondeo, dec, redondear


def reglas_de(proyecto: Proyecto) -> ReglasRedondeo:
    return ReglasRedondeo.desde_dict((proyecto.reglas or {}).get("redondeo"))


def _fila_dict(m: Medicion) -> dict:
    return {
        "id": m.id, "n": m.n, "veces": m.veces, "largo": m.largo, "ancho": m.ancho,
        "alto": m.alto, "formula": m.formula, "variables": m.variables or {},
        "signo": m.signo, "origen": m.origen,
    }


def calcular_item(db: Session, item: Item, reglas: ReglasRedondeo,
                  refrescar: bool = False) -> dict:
    """Calcula una partida y guarda los parciales en la base (caché consultable).

    `refrescar=True` obliga a releer las filas desde la base. Es obligatorio
    después de insertar, repetir o borrar filas: la colección cargada en memoria
    no incluye lo recién escrito y el total saldría de datos viejos.
    """
    if refrescar:
        db.expire(item, ["mediciones"])
    mediciones = sorted(item.mediciones, key=lambda x: (x.orden, x.creado_en))
    filas = []
    for m in mediciones:
        f = mot.calcular_fila(_fila_dict(m), item.unidad, reglas)
        nuevo = None if f.parcial is None else str(f.parcial)
        if m.parcial != nuevo or m.error != (f.error or None):
            m.parcial = nuevo
            m.error = (f.error or None)
        filas.append((m, f))

    total = mot.total_partida(
        [f for _, f in filas], item.unidad,
        desperdicio_pct=item.desperdicio_pct,
        cantidad_manual=item.cantidad_manual,
        reglas=reglas,
    )
    return {
        "total": total,
        "filas": [
            dict(
                f.a_dict(),
                id=m.id, orden=m.orden, descripcion=m.descripcion, eje=m.eje,
                lamina=m.lamina, plano_id=m.plano_id, ubicacion_id=m.ubicacion_id,
                elemento_id=m.elemento_id, n=m.n, veces=m.veces, largo=m.largo,
                ancho=m.ancho, alto=m.alto, formula=m.formula, variables=m.variables or {},
                estado=m.estado, observacion=m.observacion, supuesto=m.supuesto,
                confianza=m.confianza, responsable=m.responsable, fecha=m.fecha,
            )
            for m, f in filas
        ],
    }


def _codigo_item(prefijo: str, indice: int) -> str:
    parte = f"{indice:02d}"
    return f"{prefijo}.{parte}" if prefijo else parte


def arbol(db: Session, proyecto: Proyecto, version_id: str | None = None,
          con_filas: bool = False) -> dict:
    """Árbol completo de la hoja de metrados, con totales y códigos calculados.

    El código de ítem (01.02.03) se CALCULA a partir de la posición, no se
    guarda: mover una partida no obliga a renumerar a mano. El código normativo
    (OE.3.1.1) viaja aparte, porque es el que exige el expediente.
    """
    reglas = reglas_de(proyecto)
    q = select(Item).where(Item.proyecto_id == proyecto.id)
    if version_id:
        q = q.where(Item.version_id == version_id)
    items = list(db.scalars(q.order_by(Item.orden)))

    por_padre: dict[str | None, list[Item]] = {}
    for it in items:
        por_padre.setdefault(it.padre_id, []).append(it)
    for lista in por_padre.values():
        lista.sort(key=lambda x: (x.orden, x.creado_en))

    moneda_total = Decimal(0)
    por_especialidad: dict[str, dict] = {}
    conteo = {"partidas": 0, "con_metrado": 0, "incompletas": 0, "con_error": 0,
              "sin_lamina": 0, "aprobadas": 0, "observadas": 0}

    def construir(padre_id: str | None, prefijo: str, nivel: int) -> list[dict]:
        nonlocal moneda_total
        salida = []
        for i, it in enumerate(por_padre.get(padre_id, []), start=1):
            codigo_item = _codigo_item(prefijo, i)
            nodo = {
                "id": it.id, "item": codigo_item, "nivel": nivel, "tipo": it.tipo,
                "codigo": it.codigo, "descripcion": it.descripcion, "unidad": it.unidad,
                "especialidad": it.especialidad,
                "color": especialidades.color(it.especialidad),
                "estado": it.estado, "bloqueado": it.bloqueado,
                "desperdicio_pct": it.desperdicio_pct,
                "precio_unitario": it.precio_unitario,
                "cantidad_contratada": it.cantidad_contratada,
                "cantidad_ejecutada": it.cantidad_ejecutada,
                "familia_descuento": it.familia_descuento,
                "regla_medicion": it.regla_medicion,
                "etiqueta_fuente": it.etiqueta_fuente,
                "observaciones": it.observaciones,
                "orden": it.orden, "padre_id": it.padre_id,
            }
            if it.tipo == "titulo":
                nodo["hijos"] = construir(it.id, codigo_item, nivel + 1)
                nodo["parcial"] = str(redondear(
                    sum(dec(h.get("parcial") or 0) for h in nodo["hijos"]),
                    reglas.decimales_parcial))
                nodo["n_partidas"] = sum(h.get("n_partidas", 1) if h["tipo"] == "titulo" else 1
                                         for h in nodo["hijos"])
            else:
                calculo = calcular_item(db, it, reglas)
                t = calculo["total"]
                pu = dec(it.precio_unitario or 0)
                parcial = redondear(t.total * pu, reglas.decimales_parcial)
                moneda_total += parcial
                nodo.update({
                    "hijos": [],
                    "metrado": str(t.total),
                    "resumen": t.a_dict(),
                    "parcial": str(parcial),
                    "n_mediciones": len(calculo["filas"]),
                })
                if con_filas:
                    nodo["filas"] = calculo["filas"]

                conteo["partidas"] += 1
                if t.origen != "vacio":
                    conteo["con_metrado"] += 1
                if t.filas_incompletas:
                    conteo["incompletas"] += 1
                if t.filas_con_error:
                    conteo["con_error"] += 1
                if it.estado == "aprobado":
                    conteo["aprobadas"] += 1
                if it.estado == "observado":
                    conteo["observadas"] += 1
                if calculo["filas"] and not any(
                        f.get("lamina") or f.get("plano_id") for f in calculo["filas"]):
                    conteo["sin_lamina"] += 1

                e = por_especialidad.setdefault(it.especialidad, {
                    "clave": it.especialidad,
                    "nombre": especialidades.nombre(it.especialidad),
                    "color": especialidades.color(it.especialidad),
                    "partidas": 0, "con_metrado": 0, "costo": Decimal(0),
                })
                e["partidas"] += 1
                if t.origen != "vacio":
                    e["con_metrado"] += 1
                e["costo"] += parcial
            salida.append(nodo)
        return salida

    raiz = construir(None, "", 1)
    resumen_esp = []
    for e in sorted(por_especialidad.values(),
                    key=lambda x: especialidades.POR_CLAVE.get(x["clave"], {}).get("orden", 99)):
        resumen_esp.append({**e, "costo": str(redondear(e["costo"], reglas.decimales_parcial)),
                            "avance_pct": round(100 * e["con_metrado"] / e["partidas"], 1)
                            if e["partidas"] else 0.0})

    return {
        "items": raiz,
        "conteo": conteo,
        "por_especialidad": resumen_esp,
        "costo_directo": str(redondear(moneda_total, reglas.decimales_parcial)),
        "avance_pct": round(100 * conteo["con_metrado"] / conteo["partidas"], 1)
        if conteo["partidas"] else 0.0,
    }


def aplanar(nodos: list[dict]) -> list[dict]:
    """Recorre el árbol en orden de impresión."""
    salida = []
    for n in nodos:
        salida.append(n)
        salida.extend(aplanar(n.get("hijos") or []))
    return salida


def arbol_ubicaciones(db: Session, proyecto_id: str) -> list[dict]:
    filas = list(db.scalars(select(Ubicacion).where(Ubicacion.proyecto_id == proyecto_id)
                            .order_by(Ubicacion.orden)))
    por_padre: dict[str | None, list[Ubicacion]] = {}
    for f in filas:
        por_padre.setdefault(f.padre_id, []).append(f)

    def construir(padre_id):
        return [{
            "id": x.id, "tipo": x.tipo, "codigo": x.codigo, "nombre": x.nombre,
            "orden": x.orden, "cota": x.cota, "altura_piso": x.altura_piso,
            "area": x.area, "perimetro": x.perimetro, "atributos": x.atributos or {},
            "padre_id": x.padre_id,
            "hijos": construir(x.id),
        } for x in sorted(por_padre.get(padre_id, []), key=lambda y: (y.orden, y.nombre))]

    return construir(None)


def resumen_proyecto(db: Session, proyecto: Proyecto) -> dict:
    a = arbol(db, proyecto)
    n_ubicaciones = db.scalar(select(func.count(Ubicacion.id))
                              .where(Ubicacion.proyecto_id == proyecto.id)) or 0
    n_mediciones = db.scalar(select(func.count(Medicion.id))
                             .where(Medicion.proyecto_id == proyecto.id)) or 0
    return {
        "costo_directo": a["costo_directo"],
        "avance_pct": a["avance_pct"],
        "conteo": a["conteo"],
        "por_especialidad": a["por_especialidad"],
        "ubicaciones": n_ubicaciones,
        "mediciones": n_mediciones,
    }


def aplicar_plantilla(db: Session, proyecto: Proyecto, clave: str,
                      usuario_id: str | None = None) -> dict:
    """Vuelca una plantilla de metrados en el proyecto.

    Cada partida se enlaza al catálogo normativo por su código. Si el código no
    existe en el catálogo cargado, la partida se crea SIN código y se marca:
    nunca se inventa un código de norma.
    """
    from .models import PartidaCatalogo
    from .motor import normas, plantillas

    plantilla = plantillas.PLANTILLAS.get(clave)
    if not plantilla:
        raise ValueError(f"Plantilla desconocida: {clave}. "
                         f"Disponibles: {', '.join(plantillas.PLANTILLAS)}")

    catalogo = {c.codigo: c for c in db.scalars(
        select(PartidaCatalogo).where(PartidaCatalogo.empresa_id.is_(None)))}

    creadas = {"titulos": 0, "partidas": 0, "sin_codigo": []}

    def volcar(nodos: list[dict], padre_id: str | None) -> None:
        for i, n in enumerate(nodos, start=1):
            if n["tipo"] == "titulo":
                titulo = Item(proyecto_id=proyecto.id, version_id=proyecto.version_actual_id,
                              padre_id=padre_id, tipo="titulo",
                              descripcion=n["descripcion"], especialidad=n["especialidad"],
                              orden=i * 10, responsable=usuario_id)
                db.add(titulo)
                db.flush()
                creadas["titulos"] += 1
                volcar(n.get("hijos") or [], titulo.id)
                continue

            referencia = catalogo.get(n.get("codigo"))
            if not referencia:
                creadas["sin_codigo"].append(n["descripcion"])
            db.add(Item(
                proyecto_id=proyecto.id, version_id=proyecto.version_actual_id,
                padre_id=padre_id, tipo="partida",
                catalogo_id=referencia.id if referencia else None,
                codigo=referencia.codigo if referencia else None,
                descripcion=n["descripcion"], unidad=n["unidad"],
                especialidad=n["especialidad"], orden=i * 10,
                familia_descuento=n.get("familia_descuento") or normas.familia_por_defecto(
                    n["especialidad"], n["descripcion"]),
                regla_medicion=referencia.regla_medicion if referencia else None,
                etiqueta_fuente=normas.NORMA if (referencia and referencia.verificado)
                else normas.USUARIO,
                responsable=usuario_id,
            ))
            creadas["partidas"] += 1

    base = (db.scalar(select(func.max(Item.orden)).where(
        Item.proyecto_id == proyecto.id, Item.padre_id.is_(None))) or 0)
    arbol_plantilla = plantilla["arbol"]
    volcar(arbol_plantilla, None)

    # Respeta lo que ya existía: los nodos nuevos van después.
    if base:
        for it in db.scalars(select(Item).where(Item.proyecto_id == proyecto.id,
                                                Item.padre_id.is_(None))):
            if it.orden <= base:
                continue
            it.orden += base

    db.commit()
    return {"plantilla": plantilla["nombre"], **creadas}
