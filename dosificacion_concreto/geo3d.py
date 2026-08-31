"""
Genera una malla 3D (vertices + triangulos) y segmentos de acero a partir de la
geometria parametrica de un elemento, para renderizar en el visor WebGL (Three.js).
Reutiliza las secciones/mapeos de `vista3d.geometria`.
"""

from .vista3d import geometria, _dentro, _inset


def _area2(poly):
    a = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def _in_tri(pt, a, b, c):
    (px, py), (ax, ay), (bx, by), (cx, cy) = pt, a, b, c
    d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(d) < 1e-12:
        return False
    l1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / d
    l2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / d
    l3 = 1 - l1 - l2
    return l1 >= -1e-9 and l2 >= -1e-9 and l3 >= -1e-9


def _earclip(poly):
    n = len(poly)
    if n < 3:
        return []
    idx = list(range(n))
    if _area2(poly) < 0:
        idx.reverse()
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 2000:
        guard += 1
        m = len(idx)
        ear = False
        for k in range(m):
            i0, i1, i2 = idx[(k - 1) % m], idx[k], idx[(k + 1) % m]
            ax, ay = poly[i0]
            bx, by = poly[i1]
            cx, cy = poly[i2]
            if (bx - ax) * (cy - ay) - (by - ay) * (cx - ax) <= 0:
                continue
            if any(j not in (i0, i1, i2) and _in_tri(poly[j], (ax, ay), (bx, by), (cx, cy))
                   for j in idx):
                continue
            tris.append((i0, i1, i2))
            del idx[k]
            ear = True
            break
        if not ear:
            break
    if len(idx) == 3:
        tris.append((idx[0], idx[1], idx[2]))
    return tris


def _add_extrusion(sec, mapfn, verts, idx):
    n = len(sec)
    v0 = len(verts) // 3
    for u, v in sec:
        x, y, z = mapfn(u, v, 0.0)
        verts += [x, y, z]
    for u, v in sec:
        x, y, z = mapfn(u, v, 1.0)
        verts += [x, y, z]
    for i in range(n):
        j = (i + 1) % n
        a, b, c, d = v0 + i, v0 + j, v0 + n + j, v0 + n + i
        idx += [a, b, c, a, c, d]
    for (a, b, c) in _earclip(sec):
        idx += [v0 + a, v0 + b, v0 + c]                # cara inferior
        idx += [v0 + n + a, v0 + n + b, v0 + n + c]    # cara superior


def _seg(a, b):
    return [a[0], a[1], a[2], b[0], b[1], b[2]]


def _dowels(sec, mapfn):
    xs = [u for u, _ in sec]
    ys = [v for _, v in sec]
    umin, umax, vmin, vmax = min(xs), max(xs), min(ys), max(ys)
    du, dv = umax - umin, vmax - vmin
    r = min(du, dv) * 0.16
    nu = max(2, min(4, int(du / 0.16) + 1))
    nv = max(2, min(4, int(dv / 0.16) + 1))
    hp = 0.35
    out = []
    for i in range(nu):
        for j in range(nv):
            u = umin + r + (du - 2 * r) * (i / (nu - 1) if nu > 1 else 0.5)
            v = vmin + r + (dv - 2 * r) * (j / (nv - 1) if nv > 1 else 0.5)
            if _dentro(sec, u, v):
                b = mapfn(u, v, 1.0)
                out.append(_seg(b, (b[0], b[1], b[2] + hp)))
    return out[:12]


def _long(sec, mapfn):
    du = max(u for u, _ in sec) - min(u for u, _ in sec)
    dv = max(v for _, v in sec) - min(v for _, v in sec)
    sin = _inset(sec, min(0.06, 0.2 * min(du, dv)))
    out = [_seg(mapfn(u, v, 0.02), mapfn(u, v, 0.98)) for u, v in sin]
    for t in (0.08, 0.34, 0.62, 0.9):
        pts = [mapfn(u, v, t) for u, v in sin]
        for k in range(len(pts)):
            out.append(_seg(pts[k], pts[(k + 1) % len(pts)]))
    return out


def _amarre(sec, mapfn):
    xs = [u for u, _ in sec]
    ys = [v for _, v in sec]
    x0, x1 = min(xs), max(xs)
    ym = (min(ys) + max(ys)) / 2
    out = []
    for fr in (0.12, 0.34, 0.56, 0.78, 0.95):
        out.append(_seg(mapfn(x0, ym, fr), mapfn(x1, ym, fr)))
    for i in range(1, 6):
        xx = x0 + (x1 - x0) * i / 6
        out.append(_seg(mapfn(xx, ym, 0.02), mapfn(xx, ym, 0.98)))
    return out


def construir_malla(tipo, valores):
    """Devuelve dict {vertices, indices, rebar, groove} para el visor WebGL."""
    verts = []
    idx = []
    rebar = []
    grooves = []
    for sec, mapfn, kind in geometria(tipo, valores):
        _add_extrusion(sec, mapfn, verts, idx)
        if kind == "dowels":
            rebar += _dowels(sec, mapfn)
        elif kind == "long":
            rebar += _long(sec, mapfn)
        elif kind == "amarre":
            rebar += _amarre(sec, mapfn)
        elif kind in ("alig1", "alig2"):
            r1 = [mapfn(u, v, 1.0) for u, v in sec]
            bx0 = min(v[0] for v in r1); bx1 = max(v[0] for v in r1)
            by0 = min(v[1] for v in r1); by1 = max(v[1] for v in r1)
            zt = r1[0][2]
            for i in range(1, 5):
                t = i / 5
                grooves.append(_seg((bx0 + (bx1 - bx0) * t, by0, zt), (bx0 + (bx1 - bx0) * t, by1, zt)))
                if kind == "alig2":
                    grooves.append(_seg((bx0, by0 + (by1 - by0) * t, zt), (bx1, by0 + (by1 - by0) * t, zt)))
    return {"vertices": verts, "indices": idx, "rebar": rebar, "grooves": grooves}
