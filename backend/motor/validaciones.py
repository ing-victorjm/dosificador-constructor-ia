"""Control de calidad: detecta lo que un metrado suele esconder.

Cada alerta lleva gravedad, una explicación en lenguaje llano, la cita normativa
cuando existe y —lo más importante— **cómo se arregla**. Una alerta que dice
«error» sin decir qué hacer no sirve de nada en obra.

El motor es puro: recibe un contexto ya cargado y devuelve alertas. No consulta
la base de datos ni sabe de HTTP.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from . import normas
from .redondeo import dec
from .unidades import ErrorUnidad, dimension as dim_de_unidad

ALTA, MEDIA, BAJA = "alta", "media", "baja"

# Rangos de dimensión razonables en edificación (m). Fuera de esto no es error
# automático: es una pregunta. Fuente: práctica de obra, no norma.
RANGOS = {
    "largo": (dec("0.05"), dec("200")),
    "ancho": (dec("0.02"), dec("100")),
    "alto": (dec("0.02"), dec("60")),
}

ESPESORES_TIPICOS = {
    "losa_maciza": (dec("0.10"), dec("0.40")),
    "muro": (dec("0.06"), dec("0.60")),
    "zapata": (dec("0.30"), dec("2.00")),
}


@dataclass
class Alerta:
    clave: str
    tipo: str
    gravedad: str
    titulo: str
    detalle: str
    solucion: str
    item_id: str | None = None
    medicion_id: str | None = None
    plano_id: str | None = None
    referencia: str | None = None      # código de partida o de norma
    cita: str | None = None
    datos: dict = field(default_factory=dict)

    def a_dict(self) -> dict:
        return {
            "clave": self.clave, "tipo": self.tipo, "gravedad": self.gravedad,
            "titulo": self.titulo, "detalle": self.detalle, "solucion": self.solucion,
            "item_id": self.item_id, "medicion_id": self.medicion_id,
            "plano_id": self.plano_id, "referencia": self.referencia,
            "cita": self.cita, "datos": self.datos,
        }


def _normalizar_texto(t: str | None) -> str:
    if not t:
        return ""
    import re
    import unicodedata
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def evaluar(contexto: dict) -> list[Alerta]:
    """Ejecuta todas las validaciones sobre el proyecto ya cargado.

    `contexto` espera: partidas (planas, con `filas`), planos, elementos,
    ubicaciones, reglas del proyecto y (opcional) comparacion de versiones.
    """
    partidas: list[dict] = contexto.get("partidas") or []
    planos: list[dict] = contexto.get("planos") or []
    elementos: list[dict] = contexto.get("elementos") or []
    reglas: dict = contexto.get("reglas") or {}

    alertas: list[Alerta] = []
    for revision in (
        _duplicadas, _sin_metrado, _unidades, _negativas, _formulas_incompletas,
        _dimensiones_atipicas, _sin_evidencia, _vanos, _cantidad_manual,
        _desperdicio_en_metrado, _acero_por_ratio,
    ):
        alertas.extend(revision(partidas, reglas))

    alertas.extend(_planos_sin_calibrar(planos))
    alertas.extend(_elementos_sin_metrar(elementos, partidas))
    alertas.extend(_incompatibilidad_especialidades(partidas))
    alertas.extend(_posibles_duplicidades_origen(partidas))

    comparacion = contexto.get("comparacion")
    if comparacion:
        alertas.extend(_cambios_version(comparacion))

    orden = {ALTA: 0, MEDIA: 1, BAJA: 2}
    alertas.sort(key=lambda a: (orden.get(a.gravedad, 3), a.tipo, a.titulo))
    return alertas


# --------------------------------------------------------------------------- #
# Revisiones
# --------------------------------------------------------------------------- #

def _duplicadas(partidas, _reglas) -> list[Alerta]:
    vistos: dict[tuple, list[dict]] = defaultdict(list)
    for p in partidas:
        clave = (_normalizar_texto(p.get("descripcion")), p.get("unidad"))
        vistos[clave].append(p)
    salida = []
    for (descripcion, unidad), grupo in vistos.items():
        if len(grupo) < 2 or not descripcion:
            continue
        salida.append(Alerta(
            clave=f"duplicada:{descripcion}:{unidad}",
            tipo="partidas_duplicadas", gravedad=MEDIA,
            titulo="Partida repetida",
            detalle=f"«{grupo[0]['descripcion']}» ({unidad}) aparece {len(grupo)} veces: "
                    + ", ".join(g["item"] for g in grupo[:6]),
            solucion="Si son zonas distintas, diferéncielas en la descripción o use una "
                     "sola partida con varias filas de sustento por ubicación. Si es un "
                     "duplicado real, elimine una: se está cobrando dos veces.",
            item_id=grupo[0]["id"],
            datos={"items": [g["item"] for g in grupo]},
        ))
    return salida


def _sin_metrado(partidas, _reglas) -> list[Alerta]:
    return [Alerta(
        clave=f"sin_metrado:{p['id']}", tipo="sin_metrado", gravedad=ALTA,
        titulo="Partida sin metrar",
        detalle=f"{p['item']} «{p['descripcion']}» no tiene ninguna fila de sustento.",
        solucion="Agregue al menos una fila con sus dimensiones, o elimine la partida "
                 "si no corresponde al proyecto.",
        item_id=p["id"], referencia=p.get("codigo"),
    ) for p in partidas if (p.get("resumen") or {}).get("origen") == "vacio"]


def _unidades(partidas, _reglas) -> list[Alerta]:
    salida = []
    for p in partidas:
        unidad = p.get("unidad")
        if not unidad:
            salida.append(Alerta(
                clave=f"sin_unidad:{p['id']}", tipo="unidad", gravedad=ALTA,
                titulo="Partida sin unidad de medida",
                detalle=f"{p['item']} «{p['descripcion']}» no declara unidad.",
                solucion="Asigne la unidad que manda la norma para esa partida.",
                item_id=p["id"],
            ))
            continue
        try:
            dim_de_unidad(unidad)
        except ErrorUnidad as exc:
            salida.append(Alerta(
                clave=f"unidad_rara:{p['id']}", tipo="unidad", gravedad=ALTA,
                titulo="Unidad no reconocida", detalle=str(exc),
                solucion="Use una unidad del catálogo o regístrela en Configuración.",
                item_id=p["id"],
            ))
            continue
        for f in p.get("filas") or []:
            if f.get("error") and "dimensional" in (f["error"] or ""):
                salida.append(Alerta(
                    clave=f"dimension:{f['id']}", tipo="unidad", gravedad=ALTA,
                    titulo="Incompatibilidad dimensional",
                    detalle=f"{p['item']}: {f['error']}",
                    solucion="Corrija la unidad de la partida o quite la dimensión sobrante. "
                             "Una partida en m² no puede alimentarse de largo × ancho × alto.",
                    item_id=p["id"], medicion_id=f.get("id"),
                ))
    return salida


def _negativas(partidas, _reglas) -> list[Alerta]:
    salida = []
    for p in partidas:
        total = dec(p.get("metrado") or 0)
        if total < 0:
            salida.append(Alerta(
                clave=f"negativa:{p['id']}", tipo="cantidad_negativa", gravedad=ALTA,
                titulo="Metrado negativo",
                detalle=f"{p['item']} «{p['descripcion']}» suma {total} {p.get('unidad') or ''}.",
                solucion="Las deducciones superan al área bruta. Revise las filas con signo "
                         "negativo: probablemente falta la fila del área total.",
                item_id=p["id"],
            ))
        for f in p.get("filas") or []:
            if f.get("parcial") and dec(f["parcial"]) < 0 and int(f.get("signo") or 1) > 0:
                salida.append(Alerta(
                    clave=f"parcial_negativo:{f['id']}", tipo="cantidad_negativa", gravedad=MEDIA,
                    titulo="Parcial negativo sin marcar como deducción",
                    detalle=f"{p['item']}: la fila «{f.get('descripcion') or f.get('sustento')}» "
                            f"da {f['parcial']} pero no está marcada como deducción.",
                    solucion="Márquela como deducción (signo negativo) o revise las dimensiones.",
                    item_id=p["id"], medicion_id=f.get("id"),
                ))
    return salida


def _formulas_incompletas(partidas, _reglas) -> list[Alerta]:
    salida = []
    for p in partidas:
        for f in p.get("filas") or []:
            if f.get("faltantes"):
                salida.append(Alerta(
                    clave=f"faltan:{f['id']}", tipo="formula_incompleta", gravedad=ALTA,
                    titulo="Faltan datos para calcular",
                    detalle=f"{p['item']}: la fórmula «{f.get('sustento')}» necesita "
                            + ", ".join(f["faltantes"]),
                    solucion="Complete esos valores. METRA AI no asume ceros: una cantidad "
                             "faltante quedaría fuera del metrado sin avisar.",
                    item_id=p["id"], medicion_id=f.get("id"),
                    datos={"faltantes": f["faltantes"]},
                ))
            elif f.get("error"):
                salida.append(Alerta(
                    clave=f"error_fila:{f['id']}", tipo="formula_incompleta", gravedad=ALTA,
                    titulo="Fila con error de cálculo",
                    detalle=f"{p['item']}: {f['error']}",
                    solucion="Revise la fórmula o las dimensiones de esa fila.",
                    item_id=p["id"], medicion_id=f.get("id"),
                ))
    return salida


def _dimensiones_atipicas(partidas, _reglas) -> list[Alerta]:
    salida = []
    for p in partidas:
        for f in p.get("filas") or []:
            for campo, (minimo, maximo) in RANGOS.items():
                valor = f.get(campo)
                if valor in (None, ""):
                    continue
                try:
                    v = abs(dec(valor))
                except ValueError:
                    continue
                if v == 0 or minimo <= v <= maximo:
                    continue
                salida.append(Alerta(
                    clave=f"atipica:{f['id']}:{campo}", tipo="dimension_atipica", gravedad=BAJA,
                    titulo="Dimensión fuera de lo habitual",
                    detalle=f"{p['item']}: {campo} = {valor} m "
                            f"(lo habitual está entre {minimo} y {maximo} m).",
                    solucion="Confirme la unidad del plano. El error más común es escribir "
                             "centímetros donde van metros.",
                    item_id=p["id"], medicion_id=f.get("id"),
                    datos={"campo": campo, "valor": str(valor)},
                ))
    return salida


def _sin_evidencia(partidas, reglas) -> list[Alerta]:
    if not reglas.get("exigir_lamina", True):
        return []
    salida = []
    for p in partidas:
        filas = p.get("filas") or []
        if not filas:
            continue
        sin = [f for f in filas if not (f.get("lamina") or f.get("plano_id"))]
        if len(sin) == len(filas):
            salida.append(Alerta(
                clave=f"sin_lamina:{p['id']}", tipo="sin_evidencia", gravedad=MEDIA,
                titulo="Metrado sin lámina de referencia",
                detalle=f"{p['item']} «{p['descripcion']}»: ninguna de sus {len(filas)} "
                        "filas indica de qué plano sale.",
                solucion="Escriba el código de lámina (por ejemplo E-03) o vincule la fila a "
                         "un plano. La supervisión exige poder rastrear cada cantidad hasta "
                         "un plano concreto.",
                item_id=p["id"],
            ))
    return salida


def _vanos(partidas, _reglas) -> list[Alerta]:
    salida = []
    for p in partidas:
        familia = p.get("familia_descuento")
        if not familia or familia == "sin_descuento":
            continue
        f = normas.FAMILIAS.get(familia)
        if not f or not f.descuenta:
            continue
        deducciones = [x for x in (p.get("filas") or [])
                       if x.get("parcial") and dec(x["parcial"]) < 0]
        if deducciones:
            # Verificar que ningún vano bajo el umbral se haya descontado.
            for d in deducciones:
                ancho, alto = d.get("ancho"), d.get("alto")
                if not ancho or not alto:
                    continue
                area = dec(ancho) * dec(alto)
                aplica, motivo, _ = normas.descontar_vano(area, familia)
                if not aplica:
                    salida.append(Alerta(
                        clave=f"vano_indebido:{d['id']}", tipo="descuento_vanos", gravedad=MEDIA,
                        titulo="Vano descontado que la norma no permite descontar",
                        detalle=f"{p['item']}: se descontó un vano de {area} m². {motivo}",
                        solucion="Quite esa deducción. Sub-metrar por descontar de más también "
                                 "es un error de expediente.",
                        item_id=p["id"], medicion_id=d.get("id"),
                        referencia=f.codigo, cita=f.cita,
                    ))
            continue
        if (p.get("resumen") or {}).get("origen") == "vacio":
            continue
        salida.append(Alerta(
            clave=f"sin_vanos:{p['id']}", tipo="descuento_vanos", gravedad=MEDIA,
            titulo="Sin descuento de vanos",
            detalle=f"{p['item']} «{p['descripcion']}» es de la familia «{f.nombre}», "
                    "que descuenta vanos, y no tiene ninguna deducción registrada.",
            solucion="Si el paño no tiene puertas ni ventanas, ignore esta alerta. Si las "
                     "tiene, use «Descontar vanos» para generar las deducciones con el "
                     "umbral correcto.",
            item_id=p["id"], referencia=f.codigo, cita=f.cita,
        ))
    return salida


def _cantidad_manual(partidas, _reglas) -> list[Alerta]:
    return [Alerta(
        clave=f"manual:{p['id']}", tipo="sin_evidencia", gravedad=MEDIA,
        titulo="Cantidad escrita a mano, sin sustento",
        detalle=f"{p['item']} «{p['descripcion']}» tiene {p.get('metrado')} "
                f"{p.get('unidad') or ''} ingresados directamente.",
        solucion="Reemplácela por filas con dimensiones. Un expediente técnico no admite "
                 "una cantidad sin memoria de cálculo.",
        item_id=p["id"],
    ) for p in partidas if (p.get("resumen") or {}).get("origen") == "manual"]


def _desperdicio_en_metrado(partidas, _reglas) -> list[Alerta]:
    salida = []
    for p in partidas:
        pct = p.get("desperdicio_pct")
        if not pct or dec(pct) == 0:
            continue
        salida.append(Alerta(
            clave=f"desperdicio:{p['id']}", tipo="desperdicio", gravedad=BAJA,
            titulo="Partida con desperdicio declarado",
            detalle=f"{p['item']} lleva {pct}% de desperdicio. El metrado de la partida "
                    f"sigue siendo {p.get('metrado')} {p.get('unidad') or ''}; "
                    "el desperdicio solo afecta la cantidad a comprar.",
            solucion="Verifique que el análisis de precios unitarios no vuelva a aplicar "
                     "el mismo porcentaje: sería cobrarlo dos veces.",
            item_id=p["id"], referencia=normas.REGLA_DESPERDICIO["codigo"],
            cita=normas.REGLA_DESPERDICIO["cita"],
        ))
    return salida


def _acero_por_ratio(partidas, _reglas) -> list[Alerta]:
    salida = []
    for p in partidas:
        if p.get("unidad") != "kg":
            continue
        texto = _normalizar_texto(p.get("descripcion"))
        if "acero" not in texto and "refuerzo" not in texto:
            continue
        filas = p.get("filas") or []
        if not filas:
            continue
        con_peso = any("peso" in (f.get("formula") or "").lower() or f.get("alto")
                       for f in filas)
        if not con_peso and len(filas) <= 2:
            salida.append(Alerta(
                clave=f"acero_estimado:{p['id']}", tipo="acero", gravedad=MEDIA,
                titulo="Acero sin despiece",
                detalle=f"{p['item']} «{p['descripcion']}» se resuelve con "
                        f"{len(filas)} fila(s), sin cuadro de acero.",
                solucion="Use el módulo de acero: diámetro, longitud, ganchos, traslapes y "
                         "cantidad. " + normas.REGLA_KG_M3["aviso"],
                item_id=p["id"], cita=normas.REGLA_ARRANQUES["explicacion"],
            ))
    return salida


def _planos_sin_calibrar(planos) -> list[Alerta]:
    return [Alerta(
        clave=f"sin_calibrar:{pl['id']}", tipo="escala", gravedad=ALTA,
        titulo="Plano sin calibrar",
        detalle=f"{pl.get('codigo') or pl.get('titulo') or 'Plano'} "
                f"(página {pl.get('pagina')}) no tiene escala definida.",
        solucion="Abra el plano, use la herramienta de calibración y marque una distancia "
                 "conocida del plano. Sin calibrar, cualquier medición sobre él es falsa.",
        plano_id=pl["id"],
    ) for pl in planos if not pl.get("metros_por_px")]


def _elementos_sin_metrar(elementos, partidas) -> list[Alerta]:
    if not elementos:
        return []
    usados = {f.get("elemento_id") for p in partidas for f in (p.get("filas") or [])}
    sin = [e for e in elementos if e["id"] not in usados]
    if not sin:
        return []
    por_tipo: dict[str, list] = defaultdict(list)
    for e in sin:
        por_tipo[e.get("tipo") or "elemento"].append(e)
    return [Alerta(
        clave=f"elemento_sin_metrar:{tipo}", tipo="sin_metrado", gravedad=MEDIA,
        titulo=f"{len(grupo)} {tipo}(s) registrados y no metrados",
        detalle="Sin partida asociada: " + ", ".join(
            (e.get("marca") or e.get("nombre") or e["id"])[:20] for e in grupo[:8]),
        solucion="Genere las partidas de esos elementos o márquelos como no metrables.",
        datos={"tipo": tipo, "ids": [e["id"] for e in grupo]},
    ) for tipo, grupo in por_tipo.items()]


def _incompatibilidad_especialidades(partidas) -> list[Alerta]:
    """Cruces clásicos entre disciplinas que descuadran el metrado."""
    salida = []
    tiene = {e: any(p.get("especialidad") == e for p in partidas)
             for e in ("estructuras", "arquitectura", "sanitarias", "electricas")}

    if tiene["arquitectura"] and not tiene["estructuras"]:
        salida.append(Alerta(
            clave="falta_estructuras", tipo="incompatibilidad", gravedad=BAJA,
            titulo="Hay arquitectura pero no estructuras",
            detalle="El proyecto tiene partidas de arquitectura y ninguna de estructuras.",
            solucion="Si es un proyecto solo de acabados, ignore esta alerta.",
        ))

    area_piso = sum(dec(p.get("metrado") or 0) for p in partidas
                    if p.get("unidad") == "m2"
                    and "piso" in _normalizar_texto(p.get("descripcion")))
    area_cielo = sum(dec(p.get("metrado") or 0) for p in partidas
                     if p.get("unidad") == "m2"
                     and "cielorraso" in _normalizar_texto(p.get("descripcion")))
    if area_piso > 0 and area_cielo > 0:
        mayor = max(area_piso, area_cielo)
        if abs(area_piso - area_cielo) / mayor > Decimal("0.25"):
            salida.append(Alerta(
                clave="piso_vs_cielorraso", tipo="incompatibilidad", gravedad=MEDIA,
                titulo="Piso y cielorraso no cuadran",
                detalle=f"Pisos suman {area_piso} m² y cielorrasos {area_cielo} m² "
                        "(más de 25% de diferencia).",
                solucion="Normalmente ambas áreas son parecidas. Revise si falta metrar "
                         "ambientes en una de las dos.",
                datos={"pisos": str(area_piso), "cielorrasos": str(area_cielo)},
            ))
    return salida


def _posibles_duplicidades_origen(partidas) -> list[Alerta]:
    """La misma cantidad medida a mano y además importada de CAD/BIM."""
    salida = []
    for p in partidas:
        filas = p.get("filas") or []
        origenes = {f.get("origen") for f in filas}
        sospechosos = {"medido_plano", "importado", "detectado_ia"} & origenes
        if len(sospechosos) >= 1 and "ingresado" in origenes and len(filas) > 1:
            por_valor: dict[str, list] = defaultdict(list)
            for f in filas:
                if f.get("parcial"):
                    por_valor[str(dec(f["parcial"]))].append(f)
            repetidos = {v: fs for v, fs in por_valor.items()
                         if len(fs) > 1 and len({f.get("origen") for f in fs}) > 1}
            for valor, fs in repetidos.items():
                salida.append(Alerta(
                    clave=f"duplicidad_origen:{p['id']}:{valor}", tipo="duplicidad_origen",
                    gravedad=MEDIA,
                    titulo="Posible doble conteo entre medición manual y automática",
                    detalle=f"{p['item']}: {len(fs)} filas con el mismo parcial ({valor}) "
                            "pero distinto origen ("
                            + ", ".join(sorted({f.get('origen') or '' for f in fs})) + ").",
                    solucion="Confirme si es coincidencia o si la misma cantidad se cargó "
                             "dos veces: una a mano y otra desde el plano o el modelo.",
                    item_id=p["id"],
                ))
    return salida


def _cambios_version(comparacion: list[dict]) -> list[Alerta]:
    salida = []
    for c in comparacion:
        if c["estado"] == "modificada" and c.get("diferencia"):
            dif = dec(c["diferencia"])
            base = dec(c.get("metrado_a") or 0)
            pct = (abs(dif) / base * 100) if base else Decimal(100)
            if pct >= 10:
                salida.append(Alerta(
                    clave=f"cambio_version:{c['item']}", tipo="cambio_version",
                    gravedad=ALTA if pct >= 30 else MEDIA,
                    titulo="Cambio importante entre versiones",
                    detalle=f"{c['item']} «{c['descripcion']}»: {c['metrado_a']} → "
                            f"{c['metrado_b']} {c.get('unidad') or ''} "
                            f"({pct.quantize(Decimal('0.1'))}%).",
                    solucion="Verifique que el cambio responde a una modificación real del "
                             "proyecto y déjelo justificado en las observaciones.",
                    datos=c,
                ))
        elif c["estado"] in ("agregada", "eliminada"):
            salida.append(Alerta(
                clave=f"version_{c['estado']}:{c['item']}", tipo="cambio_version", gravedad=MEDIA,
                titulo=f"Partida {c['estado']} respecto de la versión anterior",
                detalle=f"{c['item']} «{c['descripcion']}».",
                solucion="Confirme que corresponde a un adicional o a un deductivo y regístrelo.",
                datos=c,
            ))
    return salida


def resumen(alertas: list[Alerta]) -> dict:
    por_gravedad = {ALTA: 0, MEDIA: 0, BAJA: 0}
    por_tipo: dict[str, int] = defaultdict(int)
    for a in alertas:
        por_gravedad[a.gravedad] = por_gravedad.get(a.gravedad, 0) + 1
        por_tipo[a.tipo] += 1
    return {"total": len(alertas), "por_gravedad": por_gravedad, "por_tipo": dict(por_tipo)}
