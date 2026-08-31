"""Ventana principal del Dosificador de Concreto (PySide6)."""

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
    QFrame,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy,
    QScrollArea,
    QTabWidget,
    QSpinBox,
    QTextEdit,
    QFormLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon, QColor, QPainter
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QComboBox
from PySide6.QtSvg import QSvgRenderer

from . import modelo
from . import marca
from . import elementos
from . import baldes
from . import mortero
from . import estribos
from .vista3d import VistaMuro
from .visor_web import Vista3DWeb
from .exportar_excel import exportar, exportar_metrado

ASSETS = Path(__file__).resolve().parent / "assets"
MATERIALES = ASSETS / "materiales"


def elementos_acento(clave):
    """Color de acento para la vista 3D segun el tipo de elemento."""
    mapa = {
        "zapata": "#3E7CE0",
        "columna": marca.VIOLETA,
        "viga": "#3E7CE0",
        "viga_cimentacion": "#2E6BD0",
        "cimiento_corrido": marca.INDIGO_2,
        "sobrecimiento": marca.INDIGO_2,
        "placa": marca.VIOLETA,
        "losa_maciza": marca.ACENTO_AGUA,
        "losa_aligerada_1d": "#12B5C9",
        "losa_aligerada_2d": "#0FA0B8",
        "escalera": "#E0952F",
        "losa_piso": "#7A8AA8",
        "personalizado": marca.VIOLETA,
    }
    return mapa.get(clave, marca.VIOLETA)


def _sombra(widget, blur=28, dy=8, alpha=32):
    """Aplica una sombra suave a una tarjeta (elevacion visual)."""
    efecto = QGraphicsDropShadowEffect(widget)
    efecto.setBlurRadius(blur)
    efecto.setOffset(0, dy)
    efecto.setColor(QColor(35, 30, 66, alpha))
    widget.setGraphicsEffect(efecto)


def _icono_material(nombre, lado=40):
    """Renderiza un icono SVG de material (fondo transparente) a un QLabel."""
    lbl = QLabel()
    lbl.setFixedSize(lado, lado)
    lbl.setAlignment(Qt.AlignCenter)
    ruta = MATERIALES / f"{nombre}.svg"
    if ruta.exists():
        renderer = QSvgRenderer(str(ruta))
        dpr = 3
        pix = QPixmap(lado * dpr, lado * dpr)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing, True)
        renderer.render(painter)
        painter.end()
        pix.setDevicePixelRatio(dpr)
        lbl.setPixmap(pix)
    return lbl


def _tarjeta_valor(titulo, valor_texto, unidad, acento=marca.VIOLETA, icono=None):
    marco = QFrame()
    marco.setObjectName("TarjetaResultado")
    marco.setStyleSheet(
        f"QFrame#TarjetaResultado {{ background: {marca.TARJETA};"
        f" border: 1px solid {marca.BORDE}; border-left: 4px solid {acento};"
        f" border-radius: 12px; }}"
    )
    _sombra(marco, blur=20, dy=4, alpha=22)

    fila_ext = QHBoxLayout(marco)
    fila_ext.setContentsMargins(14, 12, 16, 12)
    fila_ext.setSpacing(12)

    if icono:
        fila_ext.addWidget(_icono_material(icono), 0, Qt.AlignVCenter)

    lay = QVBoxLayout()
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(3)
    fila_ext.addLayout(lay, 1)

    et = QLabel(titulo)
    et.setObjectName("Etiqueta")
    lay.addWidget(et)

    fila = QHBoxLayout()
    fila.setSpacing(6)

    val = QLabel(valor_texto)
    val.setObjectName("ValorGrande")
    fila.addWidget(val)

    uni = QLabel(unidad)
    uni.setObjectName("Unidad")
    uni.setAlignment(Qt.AlignBottom)
    fila.addWidget(uni)
    fila.addStretch(1)
    lay.addLayout(fila)

    return marco, val


class Ventana(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dosificador de Concreto · Constructor IA")
        icono = ASSETS / "icono.ico"
        if icono.exists():
            self.setWindowIcon(QIcon(str(icono)))
        self.setMinimumSize(1040, 720)
        self.resize(1280, 860)
        self.requerimiento_actual = None
        self.presupuesto_actual = None
        self.elementos_metrados = []

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 20, 24, 16)
        raiz.setSpacing(14)

        raiz.addWidget(self._encabezado())

        self.tabs = QTabWidget()
        self.tabs.setObjectName("Tabs")
        raiz.addWidget(self.tabs, 1)
        self.tabs.addTab(self._tab_dosificacion(), "  Dosificacion  ")
        self.tabs.addTab(self._tab_metrado(), "  Metrado 3D  ")
        self.tabs.addTab(self._tab_obra(), "  Vaciado en obra  ")
        self.tabs.addTab(self._tab_mortero(), "  Mortero  ")
        self.tabs.addTab(self._tab_estribos(), "  Estribos  ")

        self.barra = QStatusBar()
        raiz.addWidget(self.barra)

        self.spin_fc.valueChanged.connect(self.calcular)
        self.spin_volumen.valueChanged.connect(self.calcular)
        self.spin_desperdicio.valueChanged.connect(self.calcular)
        self.combo_bolsa.currentIndexChanged.connect(self.calcular)
        for s in (self.spin_precio_cemento, self.spin_precio_arena,
                  self.spin_precio_piedra, self.spin_precio_agua):
            s.valueChanged.connect(self.calcular)
        self.calcular()

    def _tab_dosificacion(self):
        cont = QWidget()
        cuerpo = QHBoxLayout(cont)
        cuerpo.setContentsMargins(0, 10, 0, 0)
        cuerpo.setSpacing(16)
        cuerpo.addWidget(self._panel_entrada(), 0)
        cuerpo.addWidget(self._panel_resultado(), 1)
        return cont

    def _encabezado(self):
        cont = QFrame()
        cont.setObjectName("BarraMarca")
        cont.setMinimumHeight(84)
        _sombra(cont, blur=30, dy=10, alpha=46)
        fila = QHBoxLayout(cont)
        fila.setContentsMargins(20, 14, 22, 14)
        fila.setSpacing(16)

        # Monograma / logotipo de marca
        insignia = QLabel()
        ruta_logo = ASSETS / "constructor_ia_logo.png"
        if ruta_logo.exists():
            pix = QPixmap(str(ruta_logo)).scaledToHeight(48, Qt.SmoothTransformation)
            insignia.setPixmap(pix)
        else:
            insignia.setText("CI")
            insignia.setAlignment(Qt.AlignCenter)
            insignia.setFixedSize(52, 52)
            insignia.setStyleSheet(
                "background: rgba(255,255,255,0.12); border: 1px solid"
                " rgba(255,255,255,0.28); border-radius: 14px; color: #FFFFFF;"
                " font-size: 19px; font-weight: 800; letter-spacing: 1px;"
            )
        fila.addWidget(insignia, 0, Qt.AlignVCenter)

        izq = QVBoxLayout()
        izq.setSpacing(3)
        titulo = QLabel("Dosificador de Concreto")
        titulo.setObjectName("Titulo")
        subtitulo = QLabel(
            "Cemento, arena, piedra, agua y costo por f'c y volumen a vaciar, para expediente"
        )
        subtitulo.setObjectName("SubtituloMarca")
        izq.addWidget(titulo)
        izq.addWidget(subtitulo)

        fila.addLayout(izq)
        fila.addStretch(1)

        marca_txt = QLabel("CONSTRUCTOR IA")
        marca_txt.setObjectName("Marca")
        marca_txt.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        fila.addWidget(marca_txt, 0, Qt.AlignVCenter)

        return cont

    def _panel_entrada(self):
        marco = QFrame()
        marco.setObjectName("Tarjeta")
        marco.setFixedWidth(330)
        _sombra(marco, blur=30, dy=8, alpha=26)
        lay = QVBoxLayout(marco)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(11)

        seccion = QLabel("DATOS DEL PROYECTO")
        seccion.setObjectName("Seccion")
        lay.addWidget(seccion)

        lay.addWidget(self._etiqueta("Resistencia f'c (kg/cm2)"))
        self.spin_fc = QDoubleSpinBox()
        self.spin_fc.setRange(100, 400)
        self.spin_fc.setDecimals(0)
        self.spin_fc.setSingleStep(5)
        self.spin_fc.setValue(210)
        self.spin_fc.setSuffix(" kg/cm2")
        lay.addWidget(self.spin_fc)

        lay.addWidget(self._etiqueta("Volumen de concreto a producir"))
        self.spin_volumen = QDoubleSpinBox()
        self.spin_volumen.setRange(0.01, 100000)
        self.spin_volumen.setDecimals(2)
        self.spin_volumen.setSingleStep(1)
        self.spin_volumen.setValue(10.0)
        self.spin_volumen.setSuffix(" m3")
        lay.addWidget(self.spin_volumen)

        lay.addWidget(self._etiqueta("Desperdicio / merma adicional"))
        self.spin_desperdicio = QDoubleSpinBox()
        self.spin_desperdicio.setRange(0, 50)
        self.spin_desperdicio.setDecimals(1)
        self.spin_desperdicio.setValue(5.0)
        self.spin_desperdicio.setSuffix(" %")
        lay.addWidget(self.spin_desperdicio)

        lay.addWidget(self._etiqueta("Peso de bolsa de cemento (segun pais)"))
        self.combo_bolsa = QComboBox()
        for kg, etiqueta in [
            (42.5, "42.5 kg  ·  Peru"),
            (50.0, "50 kg  ·  Internacional / Mexico / Colombia"),
            (40.0, "40 kg"),
            (25.0, "25 kg"),
        ]:
            self.combo_bolsa.addItem(etiqueta, kg)
        self.combo_bolsa.setCurrentIndex(0)
        lay.addWidget(self.combo_bolsa)

        lay.addSpacing(4)

        seccion_precios = QLabel("PRECIOS UNITARIOS (S/)")
        seccion_precios.setObjectName("Seccion")
        lay.addWidget(seccion_precios)

        self.spin_precio_cemento = self._spin_precio(" /bolsa", 30.0)
        self.spin_precio_arena = self._spin_precio(" /m3", 60.0)
        self.spin_precio_piedra = self._spin_precio(" /m3", 70.0)
        self.spin_precio_agua = self._spin_precio(" /m3", 10.0)

        self.lbl_precio_cemento = self._etiqueta("Cemento (por bolsa de 42.5 kg)")
        lay.addWidget(self.lbl_precio_cemento)
        lay.addWidget(self.spin_precio_cemento)
        lay.addWidget(self._etiqueta("Arena (por m3)"))
        lay.addWidget(self.spin_precio_arena)
        lay.addWidget(self._etiqueta("Piedra / agregado (por m3)"))
        lay.addWidget(self.spin_precio_piedra)
        lay.addWidget(self._etiqueta("Agua (por m3)"))
        lay.addWidget(self.spin_precio_agua)

        lay.addSpacing(6)

        lay.addWidget(self._etiqueta("Responsable (para el Excel)"))
        self.texto_responsable = QLineEdit()
        self.texto_responsable.setPlaceholderText("Ing. ...")
        lay.addWidget(self.texto_responsable)

        lay.addSpacing(6)

        boton_excel = QPushButton("Exportar a Excel")
        boton_excel.setObjectName("Principal")
        boton_excel.clicked.connect(self.exportar_excel)
        lay.addWidget(boton_excel)

        lay.addStretch(1)

        nota = QLabel(
            "Tabla referencial de dosificacion por volumenes. Verificar siempre con diseno de mezcla de laboratorio antes de vaciar en obra."
        )
        nota.setWordWrap(True)
        nota.setObjectName("Subtitulo")
        lay.addWidget(nota)

        return marco

    def _etiqueta(self, texto):
        et = QLabel(texto)
        et.setObjectName("Etiqueta")
        return et

    def _spin_precio(self, sufijo, valor):
        s = QDoubleSpinBox()
        s.setRange(0, 1000000)
        s.setDecimals(2)
        s.setSingleStep(1)
        s.setValue(valor)
        s.setPrefix("S/ ")
        s.setSuffix(sufijo)
        return s

    def _panel_resultado(self):
        marco = QFrame()
        marco.setObjectName("Tarjeta")
        lay = QVBoxLayout(marco)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(14)

        seccion = QLabel("MATERIAL REQUERIDO")
        seccion.setObjectName("Seccion")
        lay.addWidget(seccion)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        lay.addLayout(grid)

        marco_cem, self.val_cemento = _tarjeta_valor("Cemento", "0", "bolsas", marca.ACENTO_CEMENTO, "cemento")
        marco_kg, self.val_cemento_kg = _tarjeta_valor("Cemento", "0", "kg", marca.ACENTO_CEMENTO, "cemento")
        marco_are, self.val_arena = _tarjeta_valor("Arena", "0", "m3", marca.ACENTO_ARENA, "arena")
        marco_pie, self.val_piedra = _tarjeta_valor("Piedra / agregado grueso", "0", "m3", marca.ACENTO_PIEDRA, "piedra")
        marco_agu, self.val_agua = _tarjeta_valor("Agua", "0", "m3", marca.ACENTO_AGUA, "agua")
        marco_lit, self.val_agua_lit = _tarjeta_valor("Agua", "0", "litros", marca.ACENTO_AGUA, "agua")

        grid.addWidget(marco_cem, 0, 0)
        grid.addWidget(marco_kg, 0, 1)
        grid.addWidget(marco_are, 1, 0)
        grid.addWidget(marco_pie, 1, 1)
        grid.addWidget(marco_agu, 2, 0)
        grid.addWidget(marco_lit, 2, 1)

        seccion2 = QLabel("PARAMETROS DE DOSIFICACION (POR M3)")
        seccion2.setObjectName("Seccion")
        lay.addWidget(seccion2)

        self.tabla = QTableWidget(5, 2)
        self.tabla.setHorizontalHeaderLabels(["Parametro", "Valor"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(34)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionMode(QTableWidget.NoSelection)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setShowGrid(False)
        self.tabla.setFixedHeight(5 * 34 + 44)
        self.tabla.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lay.addWidget(self.tabla)

        seccion3 = QLabel("PRESUPUESTO ESTIMADO")
        seccion3.setObjectName("Seccion")
        lay.addWidget(seccion3)

        self.tabla_costos = QTableWidget(4, 4)
        self.tabla_costos.setHorizontalHeaderLabels(
            ["Material", "Cantidad", "P.U. (S/)", "Parcial (S/)"]
        )
        self.tabla_costos.verticalHeader().setVisible(False)
        self.tabla_costos.verticalHeader().setDefaultSectionSize(34)
        cab = self.tabla_costos.horizontalHeader()
        cab.setSectionResizeMode(0, QHeaderView.Stretch)
        cab.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        cab.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        cab.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla_costos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_costos.setSelectionMode(QTableWidget.NoSelection)
        self.tabla_costos.setAlternatingRowColors(True)
        self.tabla_costos.setShowGrid(False)
        self.tabla_costos.setFixedHeight(4 * 34 + 44)
        self.tabla_costos.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lay.addWidget(self.tabla_costos)

        marco_total = QFrame()
        marco_total.setObjectName("TarjetaTotal")
        _sombra(marco_total, blur=28, dy=8, alpha=60)
        lt = QVBoxLayout(marco_total)
        lt.setContentsMargins(20, 16, 20, 16)
        lt.setSpacing(3)

        et_total = QLabel("Costo total de materiales del vaciado")
        et_total.setObjectName("TotalEtiqueta")
        self.val_total = QLabel("S/ 0.00")
        self.val_total.setObjectName("TotalValor")
        self.val_costo_m3 = QLabel("Costo por m3: S/ 0.00")
        self.val_costo_m3.setObjectName("TotalSub")
        lt.addWidget(et_total)
        lt.addWidget(self.val_total)
        lt.addWidget(self.val_costo_m3)
        lay.addWidget(marco_total)

        lay.addStretch(1)

        scroll = QScrollArea()
        scroll.setObjectName("ScrollResultado")
        scroll.setWidget(marco)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.viewport().setStyleSheet("background: transparent;")
        return scroll

    def calcular(self):
        peso_bolsa = self.combo_bolsa.currentData()
        self.lbl_precio_cemento.setText(
            f"Cemento (por bolsa de {peso_bolsa:g} kg)"
        )
        try:
            req = modelo.calcular(
                fc=self.spin_fc.value(),
                volumen_m3=self.spin_volumen.value(),
                desperdicio_pct=self.spin_desperdicio.value(),
                peso_bolsa=peso_bolsa,
            )
        except ValueError as e:
            self.barra.showMessage(str(e))
            return

        self.requerimiento_actual = req

        self.val_cemento.setText(f"{req.cemento_bolsas:,.2f}")
        self.val_cemento_kg.setText(f"{req.cemento_kg:,.1f}")
        self.val_arena.setText(f"{req.arena_m3:,.3f}")
        self.val_piedra.setText(f"{req.piedra_m3:,.3f}")
        self.val_agua.setText(f"{req.agua_m3:,.3f}")
        self.val_agua_lit.setText(f"{req.agua_litros:,.1f}")

        dos = req.dosificacion
        filas = [
            ("Relacion a/c", f"{dos.a_c}"),
            ("Slump", f"{dos.slump_pulg} pulg"),
            ("Tamano max. agregado", f"{dos.tmax_pulg} pulg"),
            ("Dosificacion en volumen", dos.dosificacion_volumen),
            ("Interpolado", "Si" if dos.interpolado else "No (valor de tabla)"),
        ]
        for i, (a, b) in enumerate(filas):
            self.tabla.setItem(i, 0, QTableWidgetItem(a))
            self.tabla.setItem(i, 1, QTableWidgetItem(b))

        precios = modelo.Precios(
            cemento_bolsa=self.spin_precio_cemento.value(),
            arena_m3=self.spin_precio_arena.value(),
            piedra_m3=self.spin_precio_piedra.value(),
            agua_m3=self.spin_precio_agua.value(),
        )
        pres = modelo.calcular_presupuesto(req, precios)
        self.presupuesto_actual = pres

        for i, ln in enumerate(pres.lineas):
            it_mat = QTableWidgetItem(ln.material)
            it_cant = QTableWidgetItem(f"{ln.cantidad:,.2f} {ln.unidad}")
            it_pu = QTableWidgetItem(f"{ln.precio_unit:,.2f}")
            it_par = QTableWidgetItem(f"{ln.parcial:,.2f}")
            it_cant.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it_pu.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it_par.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_costos.setItem(i, 0, it_mat)
            self.tabla_costos.setItem(i, 1, it_cant)
            self.tabla_costos.setItem(i, 2, it_pu)
            self.tabla_costos.setItem(i, 3, it_par)

        self.val_total.setText(f"S/ {pres.total:,.2f}")
        self.val_costo_m3.setText(f"Costo por m3: S/ {pres.costo_m3:,.2f}")

        self._refrescar_obra(req, peso_bolsa)

        self.barra.showMessage(
            f"f'c = {req.fc:.0f} kg/cm2 · Volumen = {req.volumen_m3:.2f} m3 · "
            f"Desperdicio = {self.spin_desperdicio.value():.1f}% · "
            f"Bolsa = {peso_bolsa:g} kg · Total: S/ {pres.total:,.2f}"
        )

    def exportar_excel(self):
        if not self.requerimiento_actual:
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar dosificacion",
            f"Dosificacion_fc{int(self.spin_fc.value())}.xlsx",
            "Excel (*.xlsx)",
        )
        if not ruta:
            return
        try:
            exportar(
                ruta,
                self.requerimiento_actual,
                self.texto_responsable.text(),
                self.presupuesto_actual,
            )
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))
            return
        QMessageBox.information(self, "Listo", f"Excel guardado en:\n{ruta}")

    # ------------------------------------------------------------------ #
    #  Utilidades de UI                                                    #
    # ------------------------------------------------------------------ #
    def _seccion(self, texto):
        lbl = QLabel(texto)
        lbl.setObjectName("Seccion")
        return lbl

    # ------------------------------------------------------------------ #
    #  Pestana: Metrado 3D                                                 #
    # ------------------------------------------------------------------ #
    def _tab_metrado(self):
        cont = QWidget()
        lay = QHBoxLayout(cont)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(16)

        # --- Panel izquierdo: elemento + 3D + dimensiones ---
        panel = QFrame()
        panel.setObjectName("Tarjeta")
        panel.setFixedWidth(400)
        _sombra(panel, 30, 8, 26)
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(20, 20, 20, 20)
        pl.setSpacing(10)

        pl.addWidget(self._seccion("ELEMENTO ESTRUCTURAL"))
        self.combo_elemento = QComboBox()
        for t in elementos.TIPOS:
            self.combo_elemento.addItem(t.nombre, t.clave)
        pl.addWidget(self.combo_elemento)

        lienzo = QFrame()
        lienzo.setObjectName("Lienzo3D")
        lienzo.setStyleSheet(
            f"QFrame#Lienzo3D {{ background: {marca.LAVANDA_2};"
            f" border: 1px solid {marca.BORDE}; border-radius: 12px; }}"
        )
        cl = QVBoxLayout(lienzo)
        cl.setContentsMargins(6, 6, 6, 6)
        self.vista3d = Vista3DWeb()
        self.vista3d.setMinimumHeight(300)
        cl.addWidget(self.vista3d)
        pl.addWidget(lienzo)

        self.lbl_ayuda_elem = QLabel("")
        self.lbl_ayuda_elem.setObjectName("Subtitulo")
        self.lbl_ayuda_elem.setWordWrap(True)
        pl.addWidget(self.lbl_ayuda_elem)

        self.cont_dims = QWidget()
        self.form_dims = QFormLayout(self.cont_dims)
        self.form_dims.setContentsMargins(0, 0, 0, 0)
        self.form_dims.setSpacing(8)
        pl.addWidget(self.cont_dims)

        fila_cant = QHBoxLayout()
        et_cant = self._etiqueta("Cantidad de elementos iguales")
        fila_cant.addWidget(et_cant, 1)
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setRange(1, 100000)
        self.spin_cantidad.setValue(1)
        self.spin_cantidad.setFixedWidth(90)
        fila_cant.addWidget(self.spin_cantidad, 0)
        pl.addLayout(fila_cant)

        self.lbl_vol_unit = QLabel("Volumen unitario: 0.000 m3")
        self.lbl_vol_unit.setObjectName("Subtitulo")
        pl.addWidget(self.lbl_vol_unit)

        btn_add = QPushButton("Agregar al metrado")
        btn_add.setObjectName("Principal")
        btn_add.clicked.connect(self._agregar_elemento)
        pl.addWidget(btn_add)
        pl.addStretch(1)
        lay.addWidget(panel, 0)

        # --- Panel derecho: lista + total ---
        der = QFrame()
        der.setObjectName("Tarjeta")
        _sombra(der, 30, 8, 26)
        dl = QVBoxLayout(der)
        dl.setContentsMargins(22, 22, 22, 22)
        dl.setSpacing(12)
        dl.addWidget(self._seccion("METRADO DE CONCRETO"))

        self.tabla_metrado = QTableWidget(0, 4)
        self.tabla_metrado.setHorizontalHeaderLabels(
            ["Elemento", "Dimensiones", "Cant.", "Vol. (m3)"]
        )
        self.tabla_metrado.verticalHeader().setVisible(False)
        self.tabla_metrado.verticalHeader().setDefaultSectionSize(32)
        cabm = self.tabla_metrado.horizontalHeader()
        cabm.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        cabm.setSectionResizeMode(1, QHeaderView.Stretch)
        cabm.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        cabm.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla_metrado.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_metrado.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_metrado.setAlternatingRowColors(True)
        self.tabla_metrado.setShowGrid(False)
        dl.addWidget(self.tabla_metrado, 1)

        fila_btns = QHBoxLayout()
        btn_quitar = QPushButton("Quitar seleccionado")
        btn_quitar.setObjectName("Secundario")
        btn_quitar.clicked.connect(self._quitar_elemento)
        btn_limpiar = QPushButton("Limpiar todo")
        btn_limpiar.setObjectName("Secundario")
        btn_limpiar.clicked.connect(self._limpiar_metrado)
        fila_btns.addWidget(btn_quitar)
        fila_btns.addWidget(btn_limpiar)
        fila_btns.addStretch(1)
        dl.addLayout(fila_btns)

        tot = QFrame()
        tot.setObjectName("TarjetaTotal")
        _sombra(tot, 28, 8, 60)
        tl = QVBoxLayout(tot)
        tl.setContentsMargins(20, 16, 20, 16)
        tl.setSpacing(3)
        et = QLabel("VOLUMEN TOTAL DE CONCRETO")
        et.setObjectName("TotalEtiqueta")
        self.lbl_metrado_total = QLabel("0.000 m3")
        self.lbl_metrado_total.setObjectName("TotalValor")
        tl.addWidget(et)
        tl.addWidget(self.lbl_metrado_total)
        dl.addWidget(tot)

        fila_usar = QHBoxLayout()
        btn_usar = QPushButton("Usar este volumen en la dosificacion")
        btn_usar.setObjectName("Principal")
        btn_usar.clicked.connect(self._usar_volumen_metrado)
        fila_usar.addWidget(btn_usar)
        btn_exportar_metrado = QPushButton("Exportar a Excel")
        btn_exportar_metrado.setObjectName("Secundario")
        btn_exportar_metrado.clicked.connect(self._exportar_metrado_excel)
        fila_usar.addWidget(btn_exportar_metrado)
        dl.addLayout(fila_usar)
        lay.addWidget(der, 1)

        self.combo_elemento.currentIndexChanged.connect(self._cambiar_tipo_elemento)
        self._cambiar_tipo_elemento()
        return cont

    def _limpiar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _cambiar_tipo_elemento(self):
        clave = self.combo_elemento.currentData()
        tipo = elementos.TIPOS_POR_CLAVE[clave]
        self._limpiar_layout(self.form_dims)
        self.spins_dims = {}
        for campo in tipo.campos:
            spin = QDoubleSpinBox()
            spin.setRange(campo.minimo, campo.maximo)
            spin.setDecimals(campo.decimales)
            spin.setSingleStep(campo.paso)
            spin.setValue(campo.valor)
            spin.setSuffix(campo.sufijo)
            spin.valueChanged.connect(self._actualizar_3d)
            self.spins_dims[campo.clave] = spin
            self.form_dims.addRow(self._etiqueta(campo.etiqueta), spin)
        self.lbl_ayuda_elem.setText(tipo.ayuda)
        self._actualizar_3d()

    def _valores_dims(self):
        return {c: s.value() for c, s in self.spins_dims.items()}

    def _actualizar_3d(self):
        clave = self.combo_elemento.currentData()
        valores = self._valores_dims()
        acento = elementos_acento(clave)
        label = self.combo_elemento.currentText().strip()
        self.vista3d.set_elemento(clave, valores, acento, label=label)
        try:
            elem = elementos.calcular_elemento(clave, valores, self.spin_cantidad.value())
            self.lbl_vol_unit.setText(
                f"Volumen unitario: {elem.volumen_unitario:.3f} m3"
            )
        except Exception:
            self.lbl_vol_unit.setText("Volumen unitario: -")

    def _agregar_elemento(self):
        clave = self.combo_elemento.currentData()
        valores = self._valores_dims()
        elem = elementos.calcular_elemento(clave, valores, self.spin_cantidad.value())
        self.elementos_metrados.append(elem)
        self._refrescar_metrado()

    def _quitar_elemento(self):
        fila = self.tabla_metrado.currentRow()
        if 0 <= fila < len(self.elementos_metrados):
            del self.elementos_metrados[fila]
            self._refrescar_metrado()

    def _limpiar_metrado(self):
        self.elementos_metrados.clear()
        self._refrescar_metrado()

    def _refrescar_metrado(self):
        self.tabla_metrado.setRowCount(len(self.elementos_metrados))
        total = 0.0
        for i, e in enumerate(self.elementos_metrados):
            total += e.volumen_total
            it_nom = QTableWidgetItem(e.nombre)
            it_dim = QTableWidgetItem(e.descripcion)
            it_can = QTableWidgetItem(str(e.cantidad))
            it_vol = QTableWidgetItem(f"{e.volumen_total:.3f}")
            it_can.setTextAlignment(Qt.AlignCenter)
            it_vol.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_metrado.setItem(i, 0, it_nom)
            self.tabla_metrado.setItem(i, 1, it_dim)
            self.tabla_metrado.setItem(i, 2, it_can)
            self.tabla_metrado.setItem(i, 3, it_vol)
        self.metrado_total = round(total, 3)
        self.lbl_metrado_total.setText(f"{self.metrado_total:,.3f} m3")

    def _usar_volumen_metrado(self):
        total = getattr(self, "metrado_total", 0.0)
        if total <= 0:
            QMessageBox.information(
                self, "Metrado vacio",
                "Agregue al menos un elemento para calcular el volumen.",
            )
            return
        self.spin_volumen.setValue(total)
        self.tabs.setCurrentIndex(0)

    def _exportar_metrado_excel(self):
        if not self.elementos_metrados:
            QMessageBox.information(
                self, "Metrado vacio",
                "Agregue al menos un elemento para exportar.",
            )
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar metrado",
            "Metrado_concreto.xlsx",
            "Excel (*.xlsx)",
        )
        if not ruta:
            return
        try:
            exportar_metrado(
                ruta,
                self.elementos_metrados,
                getattr(self, "metrado_total", 0.0),
                self.texto_responsable.text(),
            )
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))
            return
        QMessageBox.information(self, "Listo", f"Metrado guardado en:\n{ruta}")

    # ------------------------------------------------------------------ #
    #  Pestana: Vaciado en obra (trompo / baldes)                          #
    # ------------------------------------------------------------------ #
    def _tab_obra(self):
        cont = QWidget()
        lay = QHBoxLayout(cont)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(16)

        # --- Izquierda: balde + dosificacion en baldes + palabras ---
        izq = QFrame()
        izq.setObjectName("Tarjeta")
        izq.setFixedWidth(440)
        _sombra(izq, 30, 8, 26)
        il = QVBoxLayout(izq)
        il.setContentsMargins(22, 22, 22, 22)
        il.setSpacing(10)

        il.addWidget(self._seccion("BALDE / TROMPO"))
        il.addWidget(self._etiqueta("Volumen del balde (medida en obra)"))
        self.combo_balde = QComboBox()
        self.combo_balde.addItem("Balde estandar 18 L", 0.018)
        self.combo_balde.addItem("Balde 20 L", 0.020)
        self.combo_balde.addItem("Balde 15 L", 0.015)
        self.combo_balde.addItem("Balde 12 L", 0.012)
        self.combo_balde.addItem("Personalizado (medir cono)", None)
        self.combo_balde.currentIndexChanged.connect(self._toggle_cono)
        il.addWidget(self.combo_balde)

        self.cono_widget = QWidget()
        cono = QFormLayout(self.cono_widget)
        cono.setContentsMargins(0, 0, 0, 0)
        cono.setSpacing(8)
        self.spin_diam_inf = self._spin_cm(26.0)
        self.spin_diam_sup = self._spin_cm(28.5)
        self.spin_alt_balde = self._spin_cm(39.0)
        for s in (self.spin_diam_inf, self.spin_diam_sup, self.spin_alt_balde):
            s.valueChanged.connect(lambda *_: self._refrescar_obra())
        cono.addRow(self._etiqueta("Diametro inferior"), self.spin_diam_inf)
        cono.addRow(self._etiqueta("Diametro superior"), self.spin_diam_sup)
        cono.addRow(self._etiqueta("Altura"), self.spin_alt_balde)
        il.addWidget(self.cono_widget)
        self.cono_widget.setVisible(False)

        grid_b = QGridLayout()
        grid_b.setHorizontalSpacing(12)
        grid_b.setVerticalSpacing(12)
        m_are, self.val_baldes_arena = _tarjeta_valor("Arena", "0", "baldes", marca.ACENTO_ARENA, "arena")
        m_pie, self.val_baldes_piedra = _tarjeta_valor("Piedra", "0", "baldes", marca.ACENTO_PIEDRA, "piedra")
        m_agu, self.val_agua_bolsa = _tarjeta_valor("Agua", "0", "litros", marca.ACENTO_AGUA, "agua")
        grid_b.addWidget(m_are, 0, 0)
        grid_b.addWidget(m_pie, 0, 1)
        grid_b.addWidget(m_agu, 1, 0, 1, 2)
        il.addWidget(self._seccion("POR CADA BOLSA DE CEMENTO"))
        il.addLayout(grid_b)

        il.addWidget(self._seccion("PALABRAS PARA EL MAESTRO DE OBRA"))
        self.txt_maestro = QTextEdit()
        self.txt_maestro.setReadOnly(True)
        self.txt_maestro.setObjectName("Instruccion")
        il.addWidget(self.txt_maestro, 1)
        lay.addWidget(izq, 0)

        # --- Derecha: material a pedir + recomendaciones + aditivos ---
        der = QFrame()
        der.setObjectName("Tarjeta")
        _sombra(der, 30, 8, 26)
        dr = QVBoxLayout(der)
        dr.setContentsMargins(22, 22, 22, 22)
        dr.setSpacing(12)

        dr.addWidget(self._seccion("MATERIAL A PEDIR (con margen)"))
        grid_p = QGridLayout()
        grid_p.setHorizontalSpacing(12)
        grid_p.setVerticalSpacing(12)
        p_cem, self.val_pedir_cemento = _tarjeta_valor("Cemento", "0", "bolsas", marca.ACENTO_CEMENTO, "cemento")
        p_are, self.val_pedir_arena = _tarjeta_valor("Arena", "0", "m3", marca.ACENTO_ARENA, "arena")
        p_pie, self.val_pedir_piedra = _tarjeta_valor("Piedra", "0", "m3", marca.ACENTO_PIEDRA, "piedra")
        p_agu, self.val_pedir_agua = _tarjeta_valor("Agua", "0", "litros", marca.ACENTO_AGUA, "agua")
        grid_p.addWidget(p_cem, 0, 0)
        grid_p.addWidget(p_are, 0, 1)
        grid_p.addWidget(p_pie, 1, 0)
        grid_p.addWidget(p_agu, 1, 1)
        dr.addLayout(grid_p)

        dr.addWidget(self._seccion("RECOMENDACIONES TECNICAS"))
        self.txt_recom = QTextEdit()
        self.txt_recom.setReadOnly(True)
        self.txt_recom.setObjectName("Instruccion")
        self.txt_recom.setMaximumHeight(170)
        dr.addWidget(self.txt_recom)

        dr.addWidget(self._seccion("ADITIVOS (cuando conviene)"))
        self.txt_aditivos = QTextEdit()
        self.txt_aditivos.setReadOnly(True)
        self.txt_aditivos.setObjectName("Instruccion")
        aditivos = "\n".join(f"• {n}: {d}" for n, d in baldes.ADITIVOS)
        self.txt_aditivos.setPlainText(aditivos)
        dr.addWidget(self.txt_aditivos, 1)
        lay.addWidget(der, 1)
        return cont

    def _spin_cm(self, valor):
        s = QDoubleSpinBox()
        s.setRange(1, 200)
        s.setDecimals(1)
        s.setSingleStep(0.5)
        s.setValue(valor)
        s.setSuffix(" cm")
        return s

    def _toggle_cono(self):
        es_cono = self.combo_balde.currentData() is None
        self.cono_widget.setVisible(es_cono)
        self._refrescar_obra()

    def _volumen_balde_actual(self):
        data = self.combo_balde.currentData()
        if data is None:
            return baldes.volumen_balde_m3(
                self.spin_diam_inf.value(),
                self.spin_diam_sup.value(),
                self.spin_alt_balde.value(),
            )
        return data

    def _refrescar_obra(self, req=None, peso_bolsa=None):
        if req is None:
            req = self.requerimiento_actual
        if req is None or not hasattr(self, "val_baldes_arena"):
            return
        if peso_bolsa is None:
            peso_bolsa = self.combo_bolsa.currentData()

        vol_balde = self._volumen_balde_actual()
        bal = baldes.dosificar_por_baldes(req.dosificacion, req, vol_balde, peso_bolsa)

        self.val_baldes_arena.setText(f"{bal.baldes_arena:g}")
        self.val_baldes_piedra.setText(f"{bal.baldes_piedra:g}")
        self.val_agua_bolsa.setText(f"{bal.agua_litros_bolsa:g}")

        self.txt_maestro.setPlainText(baldes.palabras_maestro(req, bal, peso_bolsa))

        pedir = baldes.material_a_pedir(req)
        self.val_pedir_cemento.setText(f"{pedir['cemento_bolsas']:,}")
        self.val_pedir_arena.setText(f"{pedir['arena_m3']:,.2f}")
        self.val_pedir_piedra.setText(f"{pedir['piedra_m3']:,.2f}")
        self.val_pedir_agua.setText(f"{pedir['agua_litros']:,.0f}")

        recom = "\n".join(f"• {r}" for r in baldes.recomendaciones_obra(req))
        self.txt_recom.setPlainText(recom)

    # ------------------------------------------------------------------ #
    #  Pestana: Mortero (albanileria)                                      #
    # ------------------------------------------------------------------ #
    def _tab_mortero(self):
        cont = QWidget()
        lay = QHBoxLayout(cont)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(16)

        # --- Asentado de muro ---
        izq = QFrame()
        izq.setObjectName("Tarjeta")
        _sombra(izq, 30, 8, 26)
        il = QVBoxLayout(izq)
        il.setContentsMargins(22, 22, 22, 22)
        il.setSpacing(10)
        il.addWidget(self._seccion("ASENTADO DE MURO (LADRILLOS)"))

        form = QFormLayout()
        form.setSpacing(9)
        self.spin_area_muro = self._spin_generico(0.1, 100000, 2, 1.0, 12.0, " m2")
        self.combo_ladrillo = QComboBox()
        for i, l in enumerate(mortero.LADRILLOS):
            self.combo_ladrillo.addItem(f"{l[0]}  ({l[1]:g}x{l[2]:g}x{l[3]:g})", i)
        self.combo_aparejo = QComboBox()
        self.combo_aparejo.addItems(list(mortero.APAREJOS.keys()))
        self.spin_junta = self._spin_generico(0.5, 4.0, 1, 0.5, 1.5, " cm")
        self.combo_prop_asentado = QComboBox()
        self.combo_prop_asentado.addItems(list(mortero.PROPORCIONES.keys()))
        self.combo_prop_asentado.setCurrentText("1:4")
        form.addRow(self._etiqueta("Area de muro"), self.spin_area_muro)
        form.addRow(self._etiqueta("Ladrillo"), self.combo_ladrillo)
        form.addRow(self._etiqueta("Aparejo"), self.combo_aparejo)
        form.addRow(self._etiqueta("Espesor de junta"), self.spin_junta)
        form.addRow(self._etiqueta("Proporcion mortero"), self.combo_prop_asentado)
        il.addLayout(form)

        lienzo = QFrame()
        lienzo.setObjectName("Lienzo3D")
        lienzo.setStyleSheet(
            f"QFrame#Lienzo3D {{ background: {marca.LAVANDA_2};"
            f" border: 1px solid {marca.BORDE}; border-radius: 12px; }}"
        )
        cl = QVBoxLayout(lienzo)
        cl.setContentsMargins(6, 6, 6, 6)
        self.vista_muro = VistaMuro()
        cl.addWidget(self.vista_muro)
        il.addWidget(lienzo)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        m_lad, self.val_ladrillos = _tarjeta_valor("Ladrillos", "0", "und", marca.ACENTO_ARENA)
        m_cem, self.val_asen_cemento = _tarjeta_valor("Cemento", "0", "bolsas", marca.ACENTO_CEMENTO, "cemento")
        m_are, self.val_asen_arena = _tarjeta_valor("Arena fina", "0", "m3", marca.ACENTO_ARENA, "arena")
        grid.addWidget(m_lad, 0, 0)
        grid.addWidget(m_cem, 0, 1)
        grid.addWidget(m_are, 1, 0, 1, 2)
        il.addLayout(grid)
        self.lbl_asen_det = QLabel("")
        self.lbl_asen_det.setObjectName("Subtitulo")
        self.lbl_asen_det.setWordWrap(True)
        il.addWidget(self.lbl_asen_det)
        il.addStretch(1)
        lay.addWidget(izq, 1)

        # --- Tarrajeo ---
        der = QFrame()
        der.setObjectName("Tarjeta")
        _sombra(der, 30, 8, 26)
        dl = QVBoxLayout(der)
        dl.setContentsMargins(22, 22, 22, 22)
        dl.setSpacing(10)
        dl.addWidget(self._seccion("TARRAJEO / REVOQUE"))

        form2 = QFormLayout()
        form2.setSpacing(9)
        self.spin_area_tarr = self._spin_generico(0.1, 100000, 2, 1.0, 20.0, " m2")
        self.spin_esp_tarr = self._spin_generico(0.5, 5.0, 1, 0.5, 1.5, " cm")
        self.combo_caras = QComboBox()
        self.combo_caras.addItem("1 cara", 1)
        self.combo_caras.addItem("2 caras", 2)
        self.combo_prop_tarr = QComboBox()
        self.combo_prop_tarr.addItems(list(mortero.PROPORCIONES.keys()))
        self.combo_prop_tarr.setCurrentText("1:5")
        form2.addRow(self._etiqueta("Area a tarrajear"), self.spin_area_tarr)
        form2.addRow(self._etiqueta("Espesor"), self.spin_esp_tarr)
        form2.addRow(self._etiqueta("Caras"), self.combo_caras)
        form2.addRow(self._etiqueta("Proporcion mortero"), self.combo_prop_tarr)
        dl.addLayout(form2)

        grid2 = QGridLayout()
        grid2.setHorizontalSpacing(12)
        grid2.setVerticalSpacing(12)
        t_cem, self.val_tarr_cemento = _tarjeta_valor("Cemento", "0", "bolsas", marca.ACENTO_CEMENTO, "cemento")
        t_are, self.val_tarr_arena = _tarjeta_valor("Arena fina", "0", "m3", marca.ACENTO_ARENA, "arena")
        t_vol, self.val_tarr_vol = _tarjeta_valor("Mortero", "0", "m3", marca.ACENTO_AGUA)
        grid2.addWidget(t_cem, 0, 0)
        grid2.addWidget(t_are, 0, 1)
        grid2.addWidget(t_vol, 1, 0, 1, 2)
        dl.addLayout(grid2)
        self.lbl_tarr_det = QLabel("")
        self.lbl_tarr_det.setObjectName("Subtitulo")
        self.lbl_tarr_det.setWordWrap(True)
        dl.addWidget(self.lbl_tarr_det)

        nota = QLabel(
            "El mortero es cemento + arena fina (sin piedra). El agua se agrega hasta "
            "lograr una mezcla trabajable; no la vuelva muy aguada."
        )
        nota.setObjectName("Subtitulo")
        nota.setWordWrap(True)
        dl.addWidget(nota)
        dl.addStretch(1)
        lay.addWidget(der, 1)

        for wsig in (self.spin_area_muro, self.spin_junta):
            wsig.valueChanged.connect(self._refrescar_mortero)
        for csig in (self.combo_ladrillo, self.combo_aparejo, self.combo_prop_asentado):
            csig.currentIndexChanged.connect(self._refrescar_mortero)
        for wsig in (self.spin_area_tarr, self.spin_esp_tarr):
            wsig.valueChanged.connect(self._refrescar_mortero)
        for csig in (self.combo_caras, self.combo_prop_tarr):
            csig.currentIndexChanged.connect(self._refrescar_mortero)
        self._refrescar_mortero()
        return cont

    def _spin_generico(self, mn, mx, dec, paso, val, sufijo):
        s = QDoubleSpinBox()
        s.setRange(mn, mx)
        s.setDecimals(dec)
        s.setSingleStep(paso)
        s.setValue(val)
        s.setSuffix(sufijo)
        return s

    def _refrescar_mortero(self):
        if not hasattr(self, "val_ladrillos"):
            return
        lad = mortero.LADRILLOS[self.combo_ladrillo.currentData()]
        aparejo = self.combo_aparejo.currentText()
        self.vista_muro.set_muro(lad[1], lad[2], lad[3], aparejo, self.spin_junta.value())
        r = mortero.asentado(
            self.spin_area_muro.value(),
            lad,
            aparejo,
            self.spin_junta.value(),
            self.combo_prop_asentado.currentText(),
        )
        self.val_ladrillos.setText(f"{r.ladrillos:,.0f}")
        self.val_asen_cemento.setText(f"{r.cemento_bolsas:,.1f}")
        self.val_asen_arena.setText(f"{r.arena_m3:,.2f}")
        self.lbl_asen_det.setText(
            f"{r.detalle} · {r.ladrillos_por_m2:g} ladrillos/m2 · "
            f"mortero {r.volumen_mortero_m3:g} m3 (incluye 10% desperdicio)"
        )

        t = mortero.tarrajeo(
            self.spin_area_tarr.value(),
            self.spin_esp_tarr.value(),
            self.combo_prop_tarr.currentText(),
            caras=self.combo_caras.currentData(),
        )
        self.val_tarr_cemento.setText(f"{t.cemento_bolsas:,.1f}")
        self.val_tarr_arena.setText(f"{t.arena_m3:,.2f}")
        self.val_tarr_vol.setText(f"{t.volumen_mortero_m3:,.3f}")
        self.lbl_tarr_det.setText(f"{t.detalle} (incluye 10% desperdicio)")

    # ------------------------------------------------------------------ #
    #  Pestana: Estribos de columna                                        #
    # ------------------------------------------------------------------ #
    def _tab_estribos(self):
        cont = QWidget()
        lay = QHBoxLayout(cont)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(16)

        # --- Izquierda: entradas ---
        izq = QFrame()
        izq.setObjectName("Tarjeta")
        izq.setFixedWidth(360)
        _sombra(izq, 30, 8, 26)
        il = QVBoxLayout(izq)
        il.setContentsMargins(22, 22, 22, 22)
        il.setSpacing(10)

        il.addWidget(self._seccion("DATOS DE LA COLUMNA"))
        form = QFormLayout()
        form.setSpacing(9)

        self.est_spin_a = self._spin_generico(5, 500, 0, 5, 30, " cm")
        self.est_spin_b = self._spin_generico(5, 500, 0, 5, 30, " cm")
        self.est_spin_h = self._spin_generico(50, 2000, 0, 10, 280, " cm")
        self.est_spin_rec = self._spin_generico(1, 10, 1, 0.5, 4.0, " cm")
        form.addRow(self._etiqueta("Lado a de columna"), self.est_spin_a)
        form.addRow(self._etiqueta("Lado b de columna"), self.est_spin_b)
        form.addRow(self._etiqueta("Altura libre H"), self.est_spin_h)
        form.addRow(self._etiqueta("Recubrimiento"), self.est_spin_rec)
        il.addLayout(form)

        il.addWidget(self._seccion("DIAMETROS DE ACERO"))
        form2 = QFormLayout()
        form2.setSpacing(9)
        self.est_combo_de = QComboBox()
        for n, v in estribos.DIAMS_ESTRIBO.items():
            self.est_combo_de.addItem(n, v)
        self.est_combo_de.setCurrentIndex(1)  # 8mm por defecto
        self.est_combo_db = QComboBox()
        for n, v in estribos.DIAMS_LONG.items():
            self.est_combo_db.addItem(n, v)
        self.est_combo_db.setCurrentIndex(1)  # 1/2" por defecto
        form2.addRow(self._etiqueta("Diametro de estribo"), self.est_combo_de)
        form2.addRow(self._etiqueta("Barra longitudinal"), self.est_combo_db)
        il.addLayout(form2)

        il.addWidget(self._seccion("SEPARACIONES (dejar en 0 = automatico NTE E.060)"))
        form3 = QFormLayout()
        form3.setSpacing(9)
        self.est_spin_s1 = self._spin_generico(0, 50, 1, 1, 0, " cm")
        self.est_spin_s2 = self._spin_generico(0, 50, 1, 1, 0, " cm")
        self.est_spin_lo = self._spin_generico(0, 500, 0, 5, 0, " cm")
        form3.addRow(self._etiqueta("s1 zona confinada"), self.est_spin_s1)
        form3.addRow(self._etiqueta("s2 zona central"), self.est_spin_s2)
        form3.addRow(self._etiqueta("Lo zona confinada"), self.est_spin_lo)
        il.addLayout(form3)
        il.addStretch(1)

        nota = QLabel("Calculo segun NTE E.060-2009 / ACI 318-19. Verificar con el diseno estructural del proyecto.")
        nota.setObjectName("Subtitulo")
        nota.setWordWrap(True)
        il.addWidget(nota)
        lay.addWidget(izq, 0)

        # --- Derecha: resultados + diagrama ---
        der = QFrame()
        der.setObjectName("Tarjeta")
        _sombra(der, 30, 8, 26)
        dl = QVBoxLayout(der)
        dl.setContentsMargins(22, 22, 22, 22)
        dl.setSpacing(12)
        dl.addWidget(self._seccion("RESULTADO DE ESTRIBOS"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        mc_lo, self.est_val_lo = _tarjeta_valor("Zona confinada Lo", "—", "cm", marca.VIOLETA)
        mc_s1, self.est_val_s1 = _tarjeta_valor("s1 (zona conf.)", "—", "cm", marca.VIOLETA)
        mc_s2, self.est_val_s2 = _tarjeta_valor("s2 (zona central)", "—", "cm", marca.INDIGO_2)
        mc_le, self.est_val_le = _tarjeta_valor("Long. estribo", "—", "cm", marca.ACENTO_ARENA)
        grid.addWidget(mc_lo, 0, 0)
        grid.addWidget(mc_s1, 0, 1)
        grid.addWidget(mc_s2, 1, 0)
        grid.addWidget(mc_le, 1, 1)
        dl.addLayout(grid)

        dl.addWidget(self._seccion("CONTEO DE ESTRIBOS"))
        self.est_tabla = QTableWidget(4, 2)
        self.est_tabla.setHorizontalHeaderLabels(["Zona", "Cantidad"])
        self.est_tabla.verticalHeader().setVisible(False)
        self.est_tabla.verticalHeader().setDefaultSectionSize(34)
        self.est_tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.est_tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.est_tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.est_tabla.setSelectionMode(QTableWidget.NoSelection)
        self.est_tabla.setAlternatingRowColors(True)
        self.est_tabla.setShowGrid(False)
        self.est_tabla.setFixedHeight(4 * 34 + 44)
        self.est_tabla.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        dl.addWidget(self.est_tabla)

        tot_est = QFrame()
        tot_est.setObjectName("TarjetaTotal")
        _sombra(tot_est, 28, 8, 60)
        tl = QVBoxLayout(tot_est)
        tl.setContentsMargins(20, 16, 20, 16)
        tl.setSpacing(3)
        et_tot = QLabel("Total de estribos en la columna")
        et_tot.setObjectName("TotalEtiqueta")
        self.est_val_total = QLabel("—")
        self.est_val_total.setObjectName("TotalValor")
        self.est_val_peso = QLabel("Peso acero estribos: — kg")
        self.est_val_peso.setObjectName("TotalSub")
        tl.addWidget(et_tot)
        tl.addWidget(self.est_val_total)
        tl.addWidget(self.est_val_peso)
        dl.addWidget(tot_est)

        self.est_lbl_det = QLabel("")
        self.est_lbl_det.setObjectName("Subtitulo")
        self.est_lbl_det.setWordWrap(True)
        dl.addWidget(self.est_lbl_det)
        dl.addStretch(1)
        lay.addWidget(der, 1)

        for wsig in (self.est_spin_a, self.est_spin_b, self.est_spin_h,
                     self.est_spin_rec, self.est_spin_s1, self.est_spin_s2, self.est_spin_lo):
            wsig.valueChanged.connect(self._refrescar_estribos)
        for csig in (self.est_combo_de, self.est_combo_db):
            csig.currentIndexChanged.connect(self._refrescar_estribos)
        self._refrescar_estribos()
        return cont

    def _refrescar_estribos(self):
        if not hasattr(self, "est_val_lo"):
            return
        try:
            r = estribos.calcular(
                h_cm=self.est_spin_h.value(),
                a_cm=self.est_spin_a.value(),
                b_cm=self.est_spin_b.value(),
                de_mm=self.est_combo_de.currentData(),
                db_mm=self.est_combo_db.currentData(),
                rec_cm=self.est_spin_rec.value(),
                s1_manual=self.est_spin_s1.value() or None,
                s2_manual=self.est_spin_s2.value() or None,
                lo_manual=self.est_spin_lo.value() or None,
            )
        except Exception as e:
            self.barra.showMessage(f"Estribos error: {e}")
            return

        self.est_val_lo.setText(f"{r.lo_cm:.0f}")
        self.est_val_s1.setText(f"{r.s1_cm:.1f}")
        self.est_val_s2.setText(f"{r.s2_cm:.1f}")
        self.est_val_le.setText(f"{r.long_estribo_cm:.1f}")

        filas = [
            (f"Zona confinada inferior  (s = {r.s1_cm:.1f} cm)", str(r.n_conf_inf)),
            (f"Zona central  (s = {r.s2_cm:.1f} cm)", str(r.n_central)),
            (f"Zona confinada superior  (s = {r.s1_cm:.1f} cm)", str(r.n_conf_sup)),
            ("TOTAL", str(r.n_total)),
        ]
        for i, (zona, cant) in enumerate(filas):
            it_z = QTableWidgetItem(zona)
            it_c = QTableWidgetItem(cant)
            it_c.setTextAlignment(Qt.AlignCenter)
            if i == 3:
                it_z.setFont(it_z.font())
                it_c.setFont(it_c.font())
            self.est_tabla.setItem(i, 0, it_z)
            self.est_tabla.setItem(i, 1, it_c)

        self.est_val_total.setText(str(r.n_total))
        self.est_val_peso.setText(
            f"Peso acero estribos: {r.peso_total_kg:.2f} kg  ·  {r.kg_por_ml:.3f} kg/ml"
        )
        self.est_lbl_det.setText(r.detalle)
