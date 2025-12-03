from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtWidgets import QAction
from qgis.core import Qgis, QgsProject
from qgis.utils import iface

from .dockwidgets.ils.ils_llz_dockwidget import IlsLlzDockWidget
from .modules.ils_llz_logic import build_layers

class QbraPlugin(QObject):
    def __init__(self, iface_):
        super().__init__()
        self.iface = iface_
        self._action = None
        self._dock = None

    def initGui(self):
        self._action = QAction("QBRA ILS/LLZ", self.iface.mainWindow())
        self._action.setObjectName("qbra_ils_llz_action")
        self._action.triggered.connect(self._toggle_dock)
        self.iface.addToolBarIcon(self._action)
        self.iface.addPluginToMenu("QBRA", self._action)

    def unload(self):
        if self._action:
            self.iface.removePluginMenu("QBRA", self._action)
            self.iface.removeToolBarIcon(self._action)
            self._action = None
        if self._dock:
            self.iface.removeDockWidget(self._dock)
            self._dock = None

    def _toggle_dock(self):
        if self._dock and not self._dock.isHidden():
            self._dock.hide()
            return
        if not self._dock:
            self._dock = IlsLlzDockWidget(self.iface)
            self._dock.calculateRequested.connect(self._on_calculate)
            self._dock.closedRequested.connect(lambda: self._dock.hide())
            self.iface.addDockWidget(self._dock.defaultArea(), self._dock)
        self._dock.show()
        self._dock.raise_()

    def _on_calculate(self):
        params = self._dock.get_parameters()
        if not params:
            self.iface.messageBar().pushMessage("QBRA", "Invalid inputs", level=Qgis.Warning)
            return
        try:
            result_layer = build_layers(self.iface, params)
        except Exception as exc:
            self.iface.messageBar().pushMessage("QBRA", f"Error: {exc}", level=Qgis.Critical)
            return
        if result_layer:
            QgsProject.instance().addMapLayer(result_layer)
            self.iface.messageBar().pushMessage("QBRA", "BRA areas created", level=Qgis.Success)
