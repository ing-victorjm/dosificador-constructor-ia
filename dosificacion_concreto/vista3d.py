"""
Vista 3D isometrica parametrica de elementos estructurales.

Motor de extrusion general: cada elemento se compone de una o mas "piezas",
donde una pieza es una seccion 2D (poligono) extruida en el espacio mediante una
funcion de mapeo. Se renderiza con algoritmo del pintor (orden por profundidad),
por lo que cualquier seccion (rectangular, circular, T, L, muro, cartela) se ve
con todas sus caras visibles y sombreado coherente. Concreto gris con textura y
acero de refuerzo (fierros de espera y longitudinal). Solo usa QPainter.
"""

import math

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF, QFont, QLinearGradient, QBrush
from PySide6.QtWidgets import QWidget

_COS30 = math.cos(math.radians(30))
_SIN30 = math.sin(math.radians(30))
_VIEW = (1.0, -1.0, 1.0)
_LUZ = (-0.32, -0.60, 0.73)

_ACERO = QColor("#A8672E")
_ACERO_LUZ = QColor("#DDA06A")
_ACERO_TIP = QColor("#E6AF7E")
_LINEA = QColor("#63636D")

# Colores de ladrillo y mortero
_LAD_TOP = QColor("#CE7A54")
_LAD_MID = QColor("#B5502F")
_LAD_SIDE = QColor("#9C3F22")
_LAD_DARK = QColor("#84351B")
_MORTERO = QColor("#D6D4CC")


# --------------------------------------------------------------------------- #
#  Utilidades vectoriales                                                       #
# --------------------------------------------------------------------------- #
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a):
    m = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]) or 1.0
    return (a[0] / m, a[1] / m, a[2] / m)


def _gris(t):
    t = max(0.0, min(1.0, t))
    d = (0x66, 0x66, 0x70)
    l = (0xE2, 0xE2, 0xE8)
    return QColor(int(d[0] + (l[0] - d[0]) * t),
                  int(d[1] + (l[1] - d[1]) * t),
                  int(d[2] + (l[2] - d[2]) * t))


def _tono(nrm):
    n = _norm(nrm)
    if _dot(n, _VIEW) < 0:
        n = (-n[0], -n[1], -n[2])
    return 0.34 + 0.60 * max(0.0, _dot(n, _norm(_LUZ)))


def _dentro(poly, x, y):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def _inset(poly, d):
    cx = sum(x for x, _ in poly) / len(poly)
    cy = sum(y for _, y in poly) / len(poly)
    res = []
    for x, y in poly:
        dx, dy = cx - x, cy - y
        m = math.hypot(dx, dy) or 1.0
        k = min(d, m * 0.5)
        res.append((x + dx / m * k, y + dy / m * k))
    return res


# --------------------------------------------------------------------------- #
#  Secciones (poligonos 2D) y mapeos                                            #
# --------------------------------------------------------------------------- #
def _rect(w, d, ox=0.0, oy=0.0):
    return [(ox, oy), (ox + w, oy), (ox + w, oy + d), (ox, oy + d)]


def _circ(D, seg=30, ox=0.0, oy=0.0):
    r = D / 2.0
    cx, cy = ox + r, oy + r
    return [(cx + r * math.cos(2 * math.pi * k / seg),
             cy + r * math.sin(2 * math.pi * k / seg)) for k in range(seg)]


def _tee(ba, ea, bw, h):
    x0 = (ba - bw) / 2.0
    hw = max(1e-3, h - ea)
    return [(x0, 0), (x0 + bw, 0), (x0 + bw, hw), (ba, hw), (ba, h), (0, h), (0, hw), (x0, hw)]


def _ele(a, b, e):
    return [(0, 0), (a, 0), (a, e), (e, e), (e, b), (0, b)]


def _muro_l(v):
    bf, tf = v["ancho_zapata"], v["esp_zapata"]
    ts, hs = v["esp_muro"], v["altura_muro"]
    return [(0, 0), (bf, 0), (bf, tf), (ts, tf), (ts, tf + hs), (0, tf + hs)]


def _vmap(H):
    return lambda u, v, t: (u, v, t * H)


def _vmap_off(z0, z1):
    return lambda u, v, t: (u, v, z0 + t * (z1 - z0))


def _bmap(L, z0=0.0):
    return lambda u, v, t: (t * L, u, v + z0)


def _ymap(y0, y1):
    return lambda u, v, t: (u, y0 + t * (y1 - y0), v)


def geometria(tipo, v):
    """Devuelve una lista de piezas: (seccion2d, mapear, acero_kind)."""
    def area(clave="area"):
        return max(0.1, math.sqrt(max(0.01, v.get(clave, 1.0))))

    if tipo == "zapata":
        return [(_rect(v["largo"], v["ancho"]), _vmap(v["peralte"]), "dowels")]
    if tipo == "zapata_combinada":
        L, B, H = v["largo"], v["ancho"], v["peralte"]
        sep, c = v["sep_columnas"], v["lado_col"]
        hc = 1.0
        cy = B / 2 - c / 2
        piezas = [(_rect(L, B), _vmap(H), None)]
        for cx in (L / 2 - sep / 2 - c / 2, L / 2 + sep / 2 - c / 2):
            piezas.append((_rect(c, c, cx, cy), _vmap_off(H, H + hc), "dowels"))
        return piezas
    if tipo == "columna":
        return [(_rect(v["lado_a"], v["lado_b"]), _vmap(v["altura"]), "dowels")]
    if tipo == "columna_circular":
        return [(_circ(v["diametro"]), _vmap(v["altura"]), "dowels")]
    if tipo == "columna_t":
        return [(_tee(v["ancho_ala"], v["esp_ala"], v["ancho_alma"], v["peralte"]),
                 _vmap(v["altura"]), "dowels")]
    if tipo == "columna_l":
        return [(_ele(v["lado1"], v["lado2"], v["espesor"]), _vmap(v["altura"]), "dowels")]
    if tipo in ("viga", "viga_cimentacion"):
        return [(_rect(v["base"], v["peralte"]), _bmap(v["longitud"]), "long")]
    if tipo == "viga_t":
        return [(_tee(v["ancho_ala"], v["esp_ala"], v["ancho_alma"], v["peralte"]),
                 _bmap(v["longitud"]), "long")]
    if tipo == "viga_acartelada":
        base, h = v["base"], v["peralte"]
        ha, lc, L = v["peralte_apoyo"], v["long_cartela"], v["longitud"]
        extra = max(0.0, ha - h)
        piezas = [(_rect(base, h), _bmap(L, z0=extra), "long")]
        if extra > 1e-3:
            piezas.append(([(0, 0), (lc, extra), (0, extra)], _ymap(0, base), None))
            piezas.append(([(L, 0), (L - lc, extra), (L, extra)], _ymap(0, base), None))
        return piezas
    if tipo in ("cimiento_corrido", "sobrecimiento"):
        return [(_rect(v["longitud"], v["ancho"]), _vmap(v["altura"]), "dowels")]
    if tipo == "placa":
        return [(_rect(v["longitud"], v["espesor"]), _vmap(v["altura"]), "dowels")]
    if tipo == "muro_estructural":
        L, H, e, lc = v["longitud"], v["altura"], v["espesor"], v["lado_col"]
        oy = e / 2 - lc / 2
        wl = max(0.05, L - 2 * lc)
        return [
            (_rect(wl, e, lc, 0), _vmap(H), "amarre"),
            (_rect(lc, lc, 0, oy), _vmap(H), "dowels"),
            (_rect(lc, lc, L - lc, oy), _vmap(H), "dowels"),
        ]
    if tipo == "viga_voladizo":
        b, h, L, Ha = v["base"], v["peralte"], v["longitud"], v["altura_apoyo"]
        col = max(b, 0.30)
        return [
            (_rect(col, b, 0, 0), _vmap(Ha), "dowels"),
            (_rect(b, h), _bmap(L, z0=Ha), "long"),
        ]
    if tipo in ("falso_piso", "vereda"):
        s = area()
        return [(_rect(s, s), _vmap(v["espesor"]), None)]
    if tipo == "muro_contencion":
        return [(_muro_l(v), _bmap(v["longitud"]), "long")]
    if tipo == "losa_maciza":
        s = area()
        return [(_rect(s, s), _vmap(v["espesor"]), None)]
    if tipo == "losa_piso":
        s = area()
        return [(_rect(s, s), _vmap(v["espesor"]), None)]
    if tipo in ("losa_aligerada_1d", "losa_aligerada_2d"):
        s = area()
        kind = "alig2" if tipo == "losa_aligerada_2d" else "alig1"
        return [(_rect(s, s), _vmap(v["peralte"] / 100.0), kind)]
    if tipo == "escalera":
        s = area("area_planta")
        return [(_rect(s, s), _vmap(v["esp_equivalente"]), None)]
    if tipo in ("platea", "solado", "rampa"):
        s = area()
        return [(_rect(s, s), _vmap(v["espesor"]), None)]
    if tipo == "dado":
        return [(_rect(v["lado_a"], v["lado_b"]), _vmap(v["altura"]), "dowels")]
    if tipo == "pilote":
        return [(_circ(v["diametro"]), _vmap(v["longitud"]), "dowels")]
    if tipo == "dintel" or tipo == "viga_amarre":
        return [(_rect(v["base"], v["peralte"]), _bmap(v["longitud"]), "long")]
    if tipo == "sardinel":
        return [(_rect(v["ancho"], v["altura"]), _bmap(v["longitud"]), None)]
    if tipo == "cisterna":
        e = v["espesor"]
        Lo = v["largo"] + 2 * e
        Wo = v["ancho"] + 2 * e
        hz = v["altura"]
        return [
            (_rect(Lo, Wo), _vmap(e), None),                                  # losa de fondo
            (_rect(Lo, e, 0, 0), _vmap_off(e, e + hz), None),                 # muro frontal
            (_rect(Lo, e, 0, Wo - e), _vmap_off(e, e + hz), None),            # muro posterior
            (_rect(e, max(0.02, Wo - 2 * e), 0, e), _vmap_off(e, e + hz), None),        # muro izq
            (_rect(e, max(0.02, Wo - 2 * e), Lo - e, e), _vmap_off(e, e + hz), None),   # muro der
        ]
    lado = max(0.1, v.get("volumen", 1.0) ** (1 / 3))
    return [(_rect(lado, lado), _vmap(lado), None)]


class Vista3DElemento(QWidget):
    def __init__(self, accento="#6C3CE0", parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 240)
        self._piezas = geometria("zapata", {"largo": 1.2, "ancho": 1.2, "peralte": 0.5})

    def set_elemento(self, tipo_clave, valores, accento=None):
        try:
            self._piezas = geometria(tipo_clave, valores)
        except Exception:
            self._piezas = geometria("personalizado", {"volumen": 1.0})
        self.update()

    def _iso(self, x, y, z, s, cx, cy):
        ux = (x - y) * _COS30
        uy = (x + y) * _SIN30 - z
        return QPointF(cx + ux * s, cy + uy * s)

    # -- construccion de caras --
    def _caras_pieza(self, sec, mapfn):
        n = len(sec)
        r0 = [mapfn(u, v, 0.0) for u, v in sec]
        r1 = [mapfn(u, v, 1.0) for u, v in sec]
        caras = []
        for i in range(n):
            j = (i + 1) % n
            quad = [r0[i], r0[j], r1[j], r1[i]]
            nrm = _cross(_sub(quad[1], quad[0]), _sub(quad[3], quad[0]))
            caras.append((quad, nrm))
        caras.append((r1, _cross(_sub(r1[1], r1[0]), _sub(r1[2], r1[0]))))          # tapa sup
        caras.append((list(reversed(r0)), _cross(_sub(r0[0], r0[1]), _sub(r0[0], r0[2]))))  # tapa inf
        return caras

    def _barra(self, p, a, b, ancho=3.2):
        pen = QPen(_ACERO, ancho)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawLine(a, b)
        pen = QPen(_ACERO_LUZ, max(1.0, ancho * 0.35))
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawLine(a, b)
        p.setPen(Qt.NoPen)
        p.setBrush(_ACERO_TIP)
        p.drawEllipse(b, ancho * 0.7, ancho * 0.7)

    def _acero_dowels(self, p, P, sec, mapfn):
        xs = [u for u, _ in sec]
        ys = [v for _, v in sec]
        umin, umax, vmin, vmax = min(xs), max(xs), min(ys), max(ys)
        du, dv = umax - umin, vmax - vmin
        r = min(du, dv) * 0.16
        nu = max(2, min(4, int(du / 0.16) + 1))
        nv = max(2, min(4, int(dv / 0.16) + 1))
        hp = 0.35
        pts = []
        for i in range(nu):
            for j in range(nv):
                u = umin + r + (du - 2 * r) * (i / (nu - 1) if nu > 1 else 0.5)
                v = vmin + r + (dv - 2 * r) * (j / (nv - 1) if nv > 1 else 0.5)
                if _dentro(sec, u, v):
                    pts.append((u, v))
        pts.sort(key=lambda c: c[0] + c[1])
        for u, v in pts[:12]:
            base = mapfn(u, v, 1.0)
            self._barra(p, P(*base), P(base[0], base[1], base[2] + hp))

    def _acero_long(self, p, P, sec, mapfn):
        sin = _inset(sec, min(0.06, 0.2 * min(
            max(u for u, _ in sec) - min(u for u, _ in sec),
            max(v for _, v in sec) - min(v for _, v in sec))))
        for u, v in sin:
            self._barra(p, P(*mapfn(u, v, 0.02)), P(*mapfn(u, v, 0.98)), ancho=2.4)
        p.setPen(QPen(_ACERO, 1.3))
        p.setBrush(Qt.NoBrush)
        for t in (0.08, 0.34, 0.62, 0.9):
            p.drawPolygon(QPolygonF([P(*mapfn(u, v, t)) for u, v in sin]))

    def _acero_amarre(self, p, P, sec, mapfn):
        """Malla de acero del muro (barras horizontales y verticales)."""
        xs = [u for u, _ in sec]
        ys = [v for _, v in sec]
        x0, x1 = min(xs), max(xs)
        ym = (min(ys) + max(ys)) / 2
        for fr in (0.12, 0.34, 0.56, 0.78, 0.95):
            self._barra(p, P(*mapfn(x0, ym, fr)), P(*mapfn(x1, ym, fr)), ancho=2.0)
        for i in range(1, 6):
            xx = x0 + (x1 - x0) * i / 6
            self._barra(p, P(*mapfn(xx, ym, 0.02)), P(*mapfn(xx, ym, 0.98)), ancho=1.7)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()

        # 1) recopilar caras de todas las piezas
        todas = []
        acero = []
        verts = []
        for sec, mapfn, kind in self._piezas:
            for quad, nrm in self._caras_pieza(sec, mapfn):
                todas.append((quad, nrm))
                verts.extend(quad)
            if kind == "dowels":
                acero.append(("dowels", sec, mapfn))
            elif kind == "long":
                acero.append(("long", sec, mapfn))
            elif kind == "amarre":
                acero.append(("amarre", sec, mapfn))

        if not verts:
            p.end()
            return

        # 2) escala y centrado a partir del bounding box proyectado
        raw = [self._iso(x, y, z, 1.0, 0.0, 0.0) for x, y, z in verts]
        # margen extra arriba para los fierros de espera
        top_extra = 0.45 if any(a[0] == "dowels" for a in acero) else 0.0
        if top_extra:
            for x, y, z in list(verts):
                raw.append(self._iso(x, y, z + top_extra, 1.0, 0.0, 0.0))
        xr = [q.x() for q in raw]
        yr = [q.y() for q in raw]
        rw = (max(xr) - min(xr)) or 1
        rh = (max(yr) - min(yr)) or 1
        margen = 84
        s = max(4.0, min((w - margen) / rw, (h - margen) / rh, 1600.0))
        cx = w / 2 - s * (min(xr) + max(xr)) / 2
        cy = h / 2 - s * (min(yr) + max(yr)) / 2

        def P(x, y, z):
            return self._iso(x, y, z, s, cx, cy)

        # 3) piso: grilla + sombra sobre z=0
        xs = [v[0] for v in verts]
        ys = [v[1] for v in verts]
        zs = [v[2] for v in verts]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        z0 = min(zs)
        mx = max(0.15 * (x1 - x0), 0.1)
        my = max(0.15 * (y1 - y0), 0.1)
        p.setPen(QPen(QColor(35, 30, 66, 20), 1))
        for i in range(5):
            xg = x0 - mx + (x1 - x0 + 2 * mx) * i / 4
            p.drawLine(P(xg, y0 - my, z0), P(xg, y1 + my, z0))
            yg = y0 - my + (y1 - y0 + 2 * my) * i / 4
            p.drawLine(P(x0 - mx, yg, z0), P(x1 + mx, yg, z0))
        p.setPen(Qt.NoPen)
        foot = [P(x0, y0, z0), P(x1, y0, z0), P(x1, y1, z0), P(x0, y1, z0)]
        for dx, dy, a in ((11, 14, 20), (5, 7, 28)):
            p.setBrush(QColor(35, 30, 66, a))
            p.drawPolygon(QPolygonF([QPointF(pt.x() + dx, pt.y() + dy) for pt in foot]))

        # 4) caras ordenadas por profundidad (lejos -> cerca)
        todas.sort(key=lambda f: sum(_dot(v, _VIEW) for v in f[0]) / len(f[0]))
        p.setPen(QPen(_LINEA, 1.3))
        for quad, nrm in todas:
            pts = [P(*v) for v in quad]
            tono = _tono(nrm)
            gy = [q.y() for q in pts]
            g = QLinearGradient(QPointF(0, min(gy)), QPointF(0, max(gy)))
            g.setColorAt(0.0, _gris(tono + 0.10))
            g.setColorAt(1.0, _gris(tono - 0.10))
            p.setBrush(QBrush(g))
            p.drawPolygon(QPolygonF(pts))

        # 5) detalle de aligerado (viguetas sobre la cara superior)
        for sec, mapfn, kind in self._piezas:
            if kind in ("alig1", "alig2"):
                r1 = [mapfn(u, v, 1.0) for u, v in sec]
                bx0 = min(v[0] for v in r1); bx1 = max(v[0] for v in r1)
                by0 = min(v[1] for v in r1); by1 = max(v[1] for v in r1)
                zt = r1[0][2]
                p.setPen(QPen(_LINEA, 1.0))
                for i in range(1, 5):
                    t = i / 5
                    p.drawLine(P(bx0 + (bx1 - bx0) * t, by0, zt), P(bx0 + (bx1 - bx0) * t, by1, zt))
                    if kind == "alig2":
                        p.drawLine(P(bx0, by0 + (by1 - by0) * t, zt), P(bx1, by0 + (by1 - by0) * t, zt))

        # 6) acero
        for kind, sec, mapfn in acero:
            if kind == "dowels":
                self._acero_dowels(p, P, sec, mapfn)
            elif kind == "amarre":
                self._acero_amarre(p, P, sec, mapfn)
            else:
                self._acero_long(p, P, sec, mapfn)

        # 7) cotas del envolvente
        z1 = max(zs)
        p.setPen(QPen(QColor("#1C1B2E")))
        f = QFont("Segoe UI", 8)
        f.setBold(True)
        p.setFont(f)
        fm = p.fontMetrics()

        def cota(a, b, texto, dx, dy):
            x = (a.x() + b.x()) / 2 + dx
            y = (a.y() + b.y()) / 2 + dy
            x = max(3, min(x, w - fm.horizontalAdvance(texto) - 3))
            p.drawText(QPointF(x, y), texto)

        tx = f"{x1 - x0:.2f} m"
        ty = f"{y1 - y0:.2f} m"
        tz = f"{z1 - z0:.2f} m"
        cota(P(x0, y0, z0), P(x1, y0, z0), tx, -fm.horizontalAdvance(tx) / 2, 20)
        cota(P(x1, y0, z0), P(x1, y1, z0), ty, 8, 18)
        cota(P(x1, y0, z0), P(x1, y0, z1), tz, 10, 2)
        p.end()


class VistaMuro(QWidget):
    """Muro de ladrillo en isometrico segun el aparejo (soga/cabeza/canto)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 210)
        self._ladrillos = []
        self.set_muro(23.0, 12.5, 9.0, "Soga", 1.5)

    def set_muro(self, largo_cm, ancho_cm, alto_cm, aparejo, junta_cm):
        L, A, H = largo_cm / 100.0, ancho_cm / 100.0, alto_cm / 100.0
        j = junta_cm / 100.0
        if aparejo == "Cabeza":
            bx, by, bz = A, L, H
        elif aparejo == "Canto":
            bx, by, bz = L, H, A
        else:  # Soga
            bx, by, bz = L, A, H
        cols, filas = 4, 5
        lad = []
        for r in range(filas):
            off = (bx + j) / 2.0 if r % 2 else 0.0
            z = r * (bz + j)
            for c in range(cols):
                x = c * (bx + j) - off
                lad.append((x, 0.0, z, bx, by, bz))
        self._ladrillos = lad
        self._brick = (bx, by, bz)
        self.update()

    def _iso(self, x, y, z, s, cx, cy):
        ux = (x - y) * _COS30
        uy = (x + y) * _SIN30 - z
        return QPointF(cx + ux * s, cy + uy * s)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()
        if not self._ladrillos:
            p.end()
            return

        verts = []
        for x, y, z, bx, by, bz in self._ladrillos:
            for dx in (0, bx):
                for dy in (0, by):
                    for dz in (0, bz):
                        verts.append((x + dx, y + dy, z + dz))
        raw = [self._iso(a, b, c, 1.0, 0.0, 0.0) for a, b, c in verts]
        xr = [q.x() for q in raw]
        yr = [q.y() for q in raw]
        rw = (max(xr) - min(xr)) or 1
        rh = (max(yr) - min(yr)) or 1
        s = max(4.0, min((w - 46) / rw, (h - 46) / rh, 1600.0))
        cx = w / 2 - s * (min(xr) + max(xr)) / 2
        cy = h / 2 - s * (min(yr) + max(yr)) / 2

        def P(x, y, z):
            return self._iso(x, y, z, s, cx, cy)

        # fondo de mortero (plano frontal del muro) para que las juntas se vean
        bx0 = min(x for x, *_ in self._ladrillos)
        bx1 = max(x + b[3] for b in self._ladrillos)
        bz1 = max(b[2] + b[5] for b in self._ladrillos)
        by = self._brick[1]
        p.setPen(Qt.NoPen)
        p.setBrush(_MORTERO.darker(108))
        p.drawPolygon(QPolygonF([P(bx0, by, 0), P(bx1, by, 0), P(bx1, by, bz1), P(bx0, by, bz1)]))
        p.setBrush(_MORTERO)
        p.drawPolygon(QPolygonF([P(bx0, 0, 0), P(bx1, 0, 0), P(bx1, 0, bz1), P(bx0, 0, bz1)]))

        # ordenar ladrillos de atras hacia adelante
        piezas = sorted(self._ladrillos, key=lambda b: b[0] + b[1] + b[2])
        p.setPen(QPen(_LAD_DARK, 1.0))
        for x, y, z, bx, by, bz in piezas:
            def V(dx, dy, dz):
                return P(x + dx, y + dy, z + dz)

            # cara superior
            self._cara(p, [V(0, 0, bz), V(bx, 0, bz), V(bx, by, bz), V(0, by, bz)],
                       _LAD_TOP, _LAD_MID)
            # cara frontal izquierda (y=0)
            self._cara(p, [V(0, 0, bz), V(bx, 0, bz), V(bx, 0, 0), V(0, 0, 0)],
                       _LAD_MID, _LAD_DARK)
            # cara frontal derecha (x=bx)
            self._cara(p, [V(bx, 0, bz), V(bx, by, bz), V(bx, by, 0), V(bx, 0, 0)],
                       _LAD_SIDE, _LAD_DARK)

    def _cara(self, p, pts, c1, c2):
        gy = [q.y() for q in pts]
        g = QLinearGradient(QPointF(0, min(gy)), QPointF(0, max(gy)))
        g.setColorAt(0.0, c1)
        g.setColorAt(1.0, c2)
        p.setBrush(QBrush(g))
        p.drawPolygon(QPolygonF(pts))
