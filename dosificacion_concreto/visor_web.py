"""Visor 3D WebGL (Three.js) embebido para el metrado de elementos."""

import json
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView

from . import geo3d

WEB = Path(__file__).resolve().parent / "web" / "index.html"


class Vista3DWeb(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 260)
        self._ready = False
        self._pending = None
        self.loadFinished.connect(self._on_load)
        self.load(QUrl.fromLocalFile(str(WEB)))

    def _on_load(self, ok):
        self._ready = bool(ok)
        if self._ready and self._pending is not None:
            self._push(self._pending)

    def set_elemento(self, tipo_clave, valores, accento=None, label=""):
        try:
            model = geo3d.construir_malla(tipo_clave, valores)
        except Exception:
            return
        if accento:
            model["acento"] = accento
        if label:
            model["label"] = label
        self._pending = model
        if self._ready:
            self._push(model)

    def reset_camara(self):
        if self._ready:
            self.page().runJavaScript(
                "document.getElementById('btn-reset').click()"
            )

    def _push(self, model):
        self.page().runJavaScript("window.setModel(" + json.dumps(model) + ")")
