import sys

from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

from .marca import hoja
from .ventana import Ventana


def main():
    # Necesario para el visor 3D WebGL (QtWebEngine) embebido.
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    paleta = QPalette()
    paleta.setColor(QPalette.Window, QColor("#F4F6F8"))
    paleta.setColor(QPalette.WindowText, QColor("#1B2733"))
    paleta.setColor(QPalette.Base, QColor("#FFFFFF"))
    paleta.setColor(QPalette.Text, QColor("#1B2733"))
    paleta.setColor(QPalette.Button, QColor("#F4F6F8"))
    paleta.setColor(QPalette.ButtonText, QColor("#1B2733"))
    paleta.setColor(QPalette.ToolTipBase, QColor("#FFFFFF"))
    paleta.setColor(QPalette.ToolTipText, QColor("#1B2733"))
    app.setPalette(paleta)
    app.setStyleSheet(hoja())

    v = Ventana()
    v.show()
    sys.exit(app.exec())
