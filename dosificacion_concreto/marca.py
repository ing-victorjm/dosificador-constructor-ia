"""Identidad visual (marca Constructor IA): paleta de color y hoja de estilos QSS."""

from string import Template

# ---------------------------------------------------------------------------
# Paleta de marca Constructor IA
# ---------------------------------------------------------------------------
INDIGO = "#231E42"
INDIGO_2 = "#322A63"
INDIGO_OSC = "#191430"
VIOLETA = "#6C3CE0"
VIOLETA_HOVER = "#7A4BE6"
VIOLETA_CLARO = "#A98BFF"
LAVANDA = "#EDE9FB"
LAVANDA_2 = "#F4F1FE"

FONDO = "#F3F4F9"
TARJETA = "#FFFFFF"
TEXTO = "#1C1B2E"
GRIS = "#6B7280"
GRIS_TENUE = "#9AA1B2"
BORDE = "#E7E9F2"
BORDE_SUAVE = "#EEF0F7"
BLANCO = "#FFFFFF"
LAVANDA_TXT = "#C9C2E8"
VERDE = "#2E7D32"

# Acentos por material (para las tarjetas de resultado)
ACENTO_CEMENTO = "#6C3CE0"
ACENTO_ARENA = "#E0952F"
ACENTO_PIEDRA = "#3E7CE0"
ACENTO_AGUA = "#12B5C9"

GRADIENTE = (
    f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {INDIGO}, stop:1 {INDIGO_2})"
)
GRADIENTE_VIOLETA = (
    f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {VIOLETA_HOVER}, stop:1 {VIOLETA})"
)

_QSS = Template(
    """
    QWidget {
        background: $FONDO;
        color: $TEXTO;
        font-family: "Segoe UI", "Inter", sans-serif;
        font-size: 13px;
    }
    QLabel, QCheckBox { background: transparent; }

    /* --- Barra de marca (encabezado indigo) --- */
    QFrame#BarraMarca {
        background: $GRADIENTE;
        border: none;
        border-radius: 16px;
    }
    QLabel#Titulo {
        font-size: 22px;
        font-weight: 800;
        color: $BLANCO;
        letter-spacing: 0.3px;
    }
    QLabel#SubtituloMarca { color: $LAVANDA_TXT; font-size: 12px; }
    QLabel#Marca {
        color: $BLANCO;
        font-size: 15px;
        font-weight: 800;
        letter-spacing: 1px;
    }

    /* --- Textos de seccion --- */
    QLabel#Subtitulo { color: $GRIS; font-size: 12px; }
    QLabel#Seccion {
        font-size: 11px;
        font-weight: 800;
        color: $VIOLETA;
        letter-spacing: 1.2px;
    }
    QLabel#Etiqueta { color: $GRIS; font-size: 11px; font-weight: 600; }
    QLabel#ValorGrande { font-size: 23px; font-weight: 800; color: $TEXTO; min-height: 30px; }
    QLabel#Unidad { color: $GRIS_TENUE; font-size: 12px; font-weight: 600; }

    /* --- Tarjetas --- */
    QFrame#Tarjeta {
        background: $TARJETA;
        border: 1px solid $BORDE;
        border-radius: 16px;
    }
    QFrame#TarjetaResultado {
        background: $TARJETA;
        border: 1px solid $BORDE;
        border-left: 4px solid $VIOLETA;
        border-radius: 12px;
    }
    /* Tarjeta destacada del total (indigo premium) */
    QFrame#TarjetaTotal {
        background: $GRADIENTE;
        border: none;
        border-radius: 14px;
    }
    QLabel#TotalEtiqueta {
        color: $LAVANDA_TXT;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.8px;
    }
    QLabel#TotalValor { color: $BLANCO; font-size: 30px; font-weight: 800; min-height: 38px; }
    QLabel#TotalSub { color: $LAVANDA_TXT; font-size: 12px; }

    /* --- Campos de entrada --- */
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {
        background: #FFFFFF;
        border: 1px solid $BORDE;
        border-radius: 10px;
        padding: 8px 12px;
        selection-background-color: $VIOLETA;
        selection-color: #FFFFFF;
    }
    QLineEdit:hover, QDoubleSpinBox:hover, QSpinBox:hover, QComboBox:hover { border: 1px solid $VIOLETA_CLARO; }
    QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus { border: 1.5px solid $VIOLETA; }
    QLineEdit::placeholder { color: $GRIS_TENUE; }
    QComboBox::drop-down { border: none; width: 22px; }
    QComboBox::down-arrow {
        image: none; width: 0; height: 0;
        border-left: 5px solid transparent; border-right: 5px solid transparent;
        border-top: 7px solid $VIOLETA; margin-right: 6px;
    }
    QComboBox QAbstractItemView {
        background: #FFFFFF; border: 1px solid $BORDE; border-radius: 8px;
        selection-background-color: $LAVANDA; selection-color: $TEXTO; outline: none;
    }
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
    QSpinBox::up-button, QSpinBox::down-button {
        width: 20px;
        border: none;
        background: transparent;
        subcontrol-origin: border;
    }
    QDoubleSpinBox::up-button, QSpinBox::up-button { subcontrol-position: top right; }
    QDoubleSpinBox::down-button, QSpinBox::down-button { subcontrol-position: bottom right; }
    QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {
        image: none; width: 0; height: 0;
        border-left: 4px solid transparent; border-right: 4px solid transparent;
        border-bottom: 6px solid $VIOLETA;
    }
    QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {
        image: none; width: 0; height: 0;
        border-left: 4px solid transparent; border-right: 4px solid transparent;
        border-top: 6px solid $VIOLETA;
    }

    /* --- Botones --- */
    QPushButton#Principal {
        background: $GRADIENTE_VIOLETA;
        color: #FFFFFF;
        border: none;
        border-radius: 12px;
        padding: 12px 22px;
        font-weight: 700;
        font-size: 13px;
    }
    QPushButton#Principal:hover { background: $VIOLETA_HOVER; }
    QPushButton#Principal:pressed { background: $INDIGO_OSC; }
    QPushButton#Secundario {
        background: transparent;
        color: $VIOLETA;
        border: 1px solid $VIOLETA;
        border-radius: 12px;
        padding: 11px 20px;
        font-weight: 600;
    }
    QPushButton#Secundario:hover { background: $LAVANDA; }

    /* --- Tablas --- */
    QTableWidget {
        background: #FFFFFF;
        border: 1px solid $BORDE;
        border-radius: 12px;
        gridline-color: transparent;
        alternate-background-color: $LAVANDA_2;
        selection-background-color: $LAVANDA;
        selection-color: $TEXTO;
    }
    QTableWidget::item { padding: 7px 10px; border: none; }
    QHeaderView::section {
        background: $INDIGO;
        color: #FFFFFF;
        padding: 9px 10px;
        border: none;
        font-weight: 700;
        font-size: 11px;
    }
    QHeaderView::section:first { border-top-left-radius: 10px; }
    QHeaderView::section:last { border-top-right-radius: 10px; }
    QTableWidget QTableCornerButton::section { background: $INDIGO; border: none; }
    QStatusBar { color: $GRIS; font-size: 12px; }
    QStatusBar::item { border: none; }

    /* --- Pestanas --- */
    QTabWidget::pane { border: none; top: 4px; }
    QTabBar::tab {
        background: transparent;
        color: $GRIS;
        padding: 9px 8px;
        margin-right: 22px;
        border: none;
        border-bottom: 3px solid transparent;
        font-size: 13px;
        font-weight: 700;
    }
    QTabBar::tab:selected { color: $VIOLETA; border-bottom: 3px solid $VIOLETA; }
    QTabBar::tab:hover:!selected { color: $TEXTO; }

    /* --- Cuadros de instruccion / texto --- */
    QTextEdit#Instruccion {
        background: $LAVANDA_2;
        border: 1px solid $BORDE;
        border-radius: 12px;
        padding: 12px 14px;
        color: $TEXTO;
        font-size: 13px;
    }

    /* --- Scrollbars --- */
    QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
    QScrollBar::handle:vertical { background: $BORDE; border-radius: 5px; min-height: 28px; }
    QScrollBar::handle:vertical:hover { background: $VIOLETA_CLARO; }
    QScrollBar::add-line, QScrollBar::sub-line { height: 0; }

    QToolTip {
        background: $INDIGO;
        color: #FFFFFF;
        border: none;
        padding: 6px 9px;
        border-radius: 6px;
    }
    """
)


def hoja():
    """Devuelve la hoja de estilos completa de la aplicacion."""
    valores = {k: v for k, v in globals().items() if k.isupper()}
    return _QSS.substitute(valores)
