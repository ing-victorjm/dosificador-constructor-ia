# -*- coding: utf-8 -*-
"""
Lectura de un modelo IFC para METRADO (no para dibujar bonito).

Que hace, en orden:
  1. Lee las UNIDADES declaradas en IfcUnitAssignment y arma el factor real
     a m / m2 / m3. OJO: ifcopenshell.util.unit.calculate_unit_scale() devuelve
     el multiplicador LINEAL tambien para AREAUNIT y VOLUMEUNIT (verificado en
     0.8.5: devuelve 0.001 para un proyecto en mm), asi que hay que elevarlo
     al cuadrado / al cubo a mano o el metrado sale x1000 o x1'000,000.
  2. Lee las cantidades declaradas por el autor del modelo (IfcElementQuantity,
     Qto_*BaseQuantities)  ->  FUENTE Q.
  3. Calcula el volumen y las areas de la malla real del solido  ->  FUENTE G.
  4. Devuelve las dos y su desviacion, agrupadas por (clase IFC, tipo).
     No decide por el usuario: el usuario elige la partida y confirma.

Nada de esto emite partidas por su cuenta: la Norma Tecnica de Metrados
(R.D. 073-2010-VIVIENDA/VMCS-DNC) tiene reglas que un modelo BIM no cumple
solo (viga medida entre caras de columnas, endentado de columnas en muros,
interseccion medida una sola vez), y esas reglas las aplica el ingeniero.
Aca solo se le entregan los numeros con su procedencia.
"""
from __future__ import annotations

import base64
import os
from collections import defaultdict

import numpy as np

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element as ue
import ifcopenshell.util.shape as us

# Clases IFC que interesan para un metrado de edificacion peruana.
CLASES = [
    "IfcFooting", "IfcPile", "IfcColumn", "IfcBeam", "IfcSlab",
    "IfcWall", "IfcWallStandardCase", "IfcMember", "IfcPlate",
    "IfcStairFlight", "IfcRampFlight", "IfcCovering", "IfcRoof",
    "IfcDoor", "IfcWindow", "IfcCurtainWall", "IfcRailing",
    "IfcBuildingElementProxy", "IfcReinforcingBar",
]

# Nombres de cantidad del esquema IFC.
#
# Solo cuentan las NETAS. La norma pide neto en todos los casos que este modulo
# emite: "El volumen de concreto se obtiene calculando el volumen real por
# ejecutar" (OE.2.2.4), "Se descontaran los vanos de puertas y ventanas"
# (OE.2.3.6.2) y "Las areas son netas, por lo tanto, se descontaran en la
# medicion las areas de los vanos de puertas, ventanas, mamparas" (OE.3.1).
# GrossVolume / GrossSideArea son SIN descontar vanos: meterlos a una planilla
# seria dar un metrado inflado. Se leen aparte, solo para avisar.
Q_VOL = ("NetVolume",)
Q_AREA = ("NetSideArea", "NetArea", "NetFootprintArea")
Q_BRUTO = ("GrossVolume", "GrossSideArea", "GrossArea", "GrossFootprintArea")
Q_LONG = ("Length",)

PREFIJOS = {
    "EXA": 1e18, "PETA": 1e15, "TERA": 1e12, "GIGA": 1e9, "MEGA": 1e6,
    "KILO": 1e3, "HECTO": 1e2, "DECA": 1e1, "DECI": 1e-1, "CENTI": 1e-2,
    "MILLI": 1e-3, "MICRO": 1e-6, "NANO": 1e-9, "PICO": 1e-12,
    "FEMTO": 1e-15, "ATTO": 1e-18,
}
EXPONENTE = {"METRE": 1, "SQUARE_METRE": 2, "CUBIC_METRE": 3}
SIMBOLO = {"METRE": "m", "SQUARE_METRE": "m2", "CUBIC_METRE": "m3"}
SIM_PREF = {"KILO": "k", "HECTO": "h", "DECA": "da", "DECI": "d",
            "CENTI": "c", "MILLI": "m", "MICRO": "u"}


def _escala(f, tipo_unidad):
    """Factor para pasar el valor declarado en el IFC a unidad SI (m, m2, m3).

    Devuelve (factor, nombre_legible). Si el proyecto no declara la unidad,
    devuelve (None, "no declarada") y el llamador debe marcarlo, no adivinar.
    """
    ua = f.by_type("IfcUnitAssignment")
    if not ua:
        return None, "no declarada"
    for u in ua[0].Units:
        if getattr(u, "UnitType", None) != tipo_unidad:
            continue
        if u.is_a("IfcSIUnit"):
            exp = EXPONENTE.get(u.Name, 1)
            pref = PREFIJOS.get(u.Prefix, 1.0) if u.Prefix else 1.0
            base = SIMBOLO.get(u.Name, str(u.Name).lower())
            sp = SIM_PREF.get(u.Prefix, "") if u.Prefix else ""
            return pref ** exp, sp + base   # p.ej. MILLI + m3 -> "mm3"
        if u.is_a("IfcConversionBasedUnit"):
            try:
                return float(u.ConversionFactor.ValueComponent.wrappedValue), str(u.Name)
            except Exception:
                return None, str(getattr(u, "Name", "conversion"))
    return None, "no declarada"


def _qtos(el):
    """Cantidades declaradas por el autor del modelo, aplanadas por nombre."""
    out = {}
    try:
        for nombre_set, campos in (ue.get_psets(el, qtos_only=True) or {}).items():
            for k, v in campos.items():
                if k == "id" or not isinstance(v, (int, float)) or isinstance(v, bool):
                    continue
                out.setdefault(k, (float(v), nombre_set))
    except Exception:
        pass
    return out


def _primero(qd, nombres):
    for n in nombres:
        if n in qd:
            return qd[n]
    return None


def _tipo(el):
    """Nombre del tipo. Prioridad: objeto tipo IFC > ObjectType > Name sin id."""
    try:
        t = ue.get_type(el)
        if t is not None and getattr(t, "Name", None):
            return str(t.Name)
    except Exception:
        pass
    if getattr(el, "ObjectType", None):
        return str(el.ObjectType)
    n = str(getattr(el, "Name", "") or "")
    return n.rsplit(":", 1)[0] if n.count(":") >= 2 else (n or "sin tipo")


def _piso(el):
    try:
        c = ue.get_container(el)
        while c is not None and not c.is_a("IfcBuildingStorey"):
            c = ue.get_container(c)
        if c is not None:
            return str(c.Name or "sin nombre")
    except Exception:
        pass
    return "sin piso"


def _b64(arr, dtype):
    return base64.b64encode(np.asarray(arr, dtype=dtype).tobytes()).decode("ascii")


def leer(ruta, con_malla=True, max_triangulos=1200000):
    f = ifcopenshell.open(ruta)

    e_len, n_len = _escala(f, "LENGTHUNIT")
    e_are, n_are = _escala(f, "AREAUNIT")
    e_vol, n_vol = _escala(f, "VOLUMEUNIT")

    avisos = []
    if e_vol is None:
        avisos.append("El modelo no declara unidad de VOLUMEN: las cantidades "
                      "declaradas (fuente Q) no se pueden convertir y se omiten.")
    if e_are is None:
        avisos.append("El modelo no declara unidad de AREA: las areas declaradas "
                      "(fuente Q) no se pueden convertir y se omiten.")

    # --- elementos de interes -------------------------------------------------
    elems = {}
    for c in CLASES:
        try:
            for el in f.by_type(c):
                elems[el.id()] = el
        except Exception:
            pass  # la clase no existe en este esquema (IFC2X3 vs IFC4)

    # --- geometria (fuente G) -------------------------------------------------
    # ifcopenshell.geom entrega la malla YA EN METROS aunque el proyecto este en
    # milimetros (verificado: muro de 4000x150x2500 mm -> bbox 4.00 x 0.15 x 2.50).
    geo, mallas, tri_total = {}, {}, 0
    if elems:
        s = ifcopenshell.geom.settings()
        # Sin use-world-coords todos los solidos salen apilados en el origen
        # (verificado: una columna colocada en x=6.00 m se devolvia en x=0).
        # El volumen NO cambia con esta opcion; la posicion si.
        for opcion, valor in (("use-world-coords", True), ("weld-vertices", True)):
            try:
                s.set(opcion, valor)
            except Exception:
                pass
        # num_threads=0 ("auto") se cuelga en Windows con ifcopenshell 0.8.5
        # (verificado: el proceso nunca retorna). Se fija un numero explicito.
        hilos = max(1, min(4, os.cpu_count() or 1))
        it = ifcopenshell.geom.iterator(s, f, num_threads=hilos,
                                        include=list(elems.values()))
        if it.initialize():
            while True:
                sh = it.get()
                eid = sh.id
                try:
                    v = us.get_vertices(sh.geometry)
                    fa = us.get_faces(sh.geometry)
                    vol = float(us.get_volume(sh.geometry))
                    bb = us.get_bbox(v)
                    dim = bb[1] - bb[0]
                    caja = float(dim[0] * dim[1] * dim[2])
                    cerrado = vol > 0 and (caja <= 0 or vol <= caja * 1.02)
                    geo[eid] = {
                        "vol": vol if cerrado else None,
                        "lateral": float(us.get_max_side_area(sh.geometry) or 0),
                        "dim": [float(x) for x in dim],
                    }
                    if con_malla and tri_total + len(fa) <= max_triangulos:
                        mallas[eid] = (v.astype(np.float32).ravel(),
                                       fa.astype(np.uint32).ravel())
                        tri_total += len(fa)
                except Exception:
                    geo[eid] = {"vol": None, "lateral": 0.0, "dim": [0, 0, 0]}
                if not it.next():
                    break

    # --- agrupado -------------------------------------------------------------
    grupos = defaultdict(lambda: {
        "n": 0, "vol_q": 0.0, "vol_q_n": 0, "vol_g": 0.0, "vol_g_n": 0,
        "area_q": 0.0, "area_q_n": 0, "area_g": 0.0, "long_q": 0.0,
        "pisos": set(), "ids": [], "qsets": set(), "abiertos": 0, "solo_bruto": 0,
    })
    con_qto = 0
    solo_bruto = 0
    for eid, el in elems.items():
        g = grupos[(el.is_a(), _tipo(el))]
        g["n"] += 1
        g["ids"].append(eid)
        g["pisos"].add(_piso(el))

        qd = _qtos(el)
        if qd:
            con_qto += 1
        vq = _primero(qd, Q_VOL)
        if vq and e_vol:
            g["vol_q"] += vq[0] * e_vol
            g["vol_q_n"] += 1
            g["qsets"].add(vq[1])
        aq = _primero(qd, Q_AREA)
        if aq and e_are:
            g["area_q"] += aq[0] * e_are
            g["area_q_n"] += 1
            g["qsets"].add(aq[1])
        # Declara cantidades, pero ninguna NETA: no sirven para metrar.
        if qd and not vq and not aq and _primero(qd, Q_BRUTO):
            g["solo_bruto"] += 1
            solo_bruto += 1
        lq = _primero(qd, Q_LONG)
        if lq and e_len:
            g["long_q"] += lq[0] * e_len

        gg = geo.get(eid)
        if gg:
            if gg["vol"] is not None:
                g["vol_g"] += gg["vol"]
                g["vol_g_n"] += 1
            else:
                g["abiertos"] += 1
            g["area_g"] += gg["lateral"]

    salida = []
    for (clase, tipo), g in sorted(grupos.items(), key=lambda x: (x[0][0], x[0][1])):
        vq = g["vol_q"] if g["vol_q_n"] else None
        vg = g["vol_g"] if g["vol_g_n"] else None
        desv = ((vg - vq) / vq * 100.0) if (vq and vg and vq > 0) else None
        item = {
            "id": clase + "|" + tipo,
            "clase": clase,
            "tipo": tipo,
            "n": g["n"],
            "pisos": sorted(g["pisos"]),
            "vol_q_m3": round(vq, 4) if vq is not None else None,
            "vol_g_m3": round(vg, 4) if vg is not None else None,
            "n_con_vol_q": g["vol_q_n"],
            "n_con_vol_g": g["vol_g_n"],
            "area_q_m2": round(g["area_q"], 3) if g["area_q_n"] else None,
            "area_g_m2": round(g["area_g"], 3) if g["area_g"] else None,
            "long_q_m": round(g["long_q"], 3) if g["long_q"] else None,
            "desvio_pct": round(desv, 2) if desv is not None else None,
            "qsets": sorted(g["qsets"]),
            "solidos_abiertos": g["abiertos"],
            "solo_bruto": g["solo_bruto"],
        }
        if con_malla:
            vs, fs, off = [], [], 0
            for eid in g["ids"]:
                m = mallas.get(eid)
                if not m:
                    continue
                vs.append(m[0])
                fs.append(m[1] + off)
                off += len(m[0]) // 3
            if vs:
                item["malla"] = {"v": _b64(np.concatenate(vs), np.float32),
                                 "f": _b64(np.concatenate(fs), np.uint32)}
        salida.append(item)

    if tri_total >= max_triangulos:
        avisos.append("Modelo grande: la vista 3D se corto en " +
                      format(max_triangulos, ",") + " triangulos. "
                      "Los numeros del metrado NO se cortaron.")
    if solo_bruto:
        avisos.append(str(solo_bruto) + " elemento(s) declaran solo cantidades BRUTAS "
                      "(GrossVolume / GrossSideArea), que no descuentan vanos. La norma "
                      "pide neto (OE.2.3.6.2 y OE.3.1), asi que esas cantidades no se "
                      "usan como fuente Q: para esos elementos manda la geometria (G).")
    if con_qto == 0 and elems:
        avisos.append("Este modelo NO trae cantidades declaradas (Qto_*BaseQuantities). "
                      "Vuelve a exportarlo con 'Base Quantities' activado si quieres "
                      "contrastar. Mientras tanto solo hay fuente G (geometria).")

    return {
        "esquema": f.schema,
        "unidades": {"longitud": n_len, "area": n_are, "volumen": n_vol},
        "elementos": len(elems),
        "con_qto": con_qto,
        "grupos": salida,
        "avisos": avisos,
    }
