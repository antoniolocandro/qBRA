"""QGIS Plugin main class for qBRA."""

from typing import Any, Optional
import os

from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import Qgis, QgsProject, QgsVectorLayer

from .dockwidgets.ils.ils_llz_dockwidget import IlsLlzDockWidget
from .modules.ils_llz_logic import build_layers, build_layers_omni
import os

class QbraPlugin(QObject):
    """Main plugin class for qBRA - Building Restriction Areas."""
    
    def __init__(self, iface: Any) -> None:
        """Initialize the plugin.
        
        Args:
            iface: QGIS interface object.
        """
        super().__init__()
        self.iface: Any = iface
        self._action: Optional[QAction] = None
        self._dock: Optional[IlsLlzDockWidget] = None
        self._worker: Optional[BRAWorker] = None
        self.plugin_dir: str = os.path.dirname(__file__)
        self._icon: QIcon = QIcon(os.path.join(self.plugin_dir, "icons", "qbra.svg"))

    def initGui(self) -> None:
        """Initialize the graphical user interface."""
        self._action = QAction("QBRA ILS/LLZ", self.iface.mainWindow())
        self._action.setObjectName("qbra_ils_llz_action")
        # Apply plugin icon to toolbar/menu action
        try:
            self._action.setIcon(self._icon)
        except (RuntimeError, AttributeError) as e:
            # Icon loading can fail if file doesn't exist or Qt binding issue
            logger.debug("Failed to set action icon: %s", e)
        self._action.triggered.connect(self._toggle_dock)
        self.iface.addToolBarIcon(self._action)
        self.iface.addPluginToMenu("QBRA", self._action)

    def unload(self) -> None:
        """Clean up and remove plugin resources."""
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait()
        self._worker = None
        if self._action:
            self.iface.removePluginMenu("QBRA", self._action)
            self.iface.removeToolBarIcon(self._action)
            self._action = None
        if self._dock:
            self.iface.removeDockWidget(self._dock)
            self._dock = None

    def _toggle_dock(self) -> None:
        """Toggle the dock widget visibility."""
        if self._dock and not self._dock.isHidden():
            self._dock.hide()
            return
        if not self._dock:
            self._dock = IlsLlzDockWidget(self.iface)
            # Apply icon to dock window as well
            try:
                self._dock.setWindowIcon(self._icon)
            except (RuntimeError, AttributeError) as e:
                # Icon setting can fail, but it's cosmetic
                logger.debug("Failed to set dock window icon: %s", e)
            self._dock.calculateRequested.connect(self._on_calculate)
            self._dock.closedRequested.connect(lambda: self._dock.hide())
            self.iface.addDockWidget(self._dock.defaultArea(), self._dock)
        # refresh layers each time we open to reflect current project state
        try:
            self._dock.refresh_layers()
        except LayerNotFoundError as e:
            # No layers available is not critical - user will see empty combos
            logger.warning("No layers found when refreshing: %s", e)
        except Exception as e:
            # Unexpected errors during refresh should be logged but not fatal
            logger.error("Unexpected error during layer refresh: %s", e, exc_info=True)
        self._dock.show()
        self._dock.raise_()

    def _on_calculate(self) -> None:
        """Handle calculate button click — starts calculation on a background thread."""
        if self._worker and self._worker.isRunning():
            return  # BUG-02: ignore re-entrant calls while a calculation is in flight

        params: Optional[BRAParameters] = self._dock.get_parameters() if self._dock else None
        if not params:
            self.iface.messageBar().pushMessage("QBRA", "Invalid inputs", level=Qgis.Warning)
            return
        try:
            mode = params.get("mode", "directional")
            if mode == "omni":
                result_layer = build_layers_omni(self.iface, params)
            else:
                result_layer = build_layers(self.iface, params)
        except Exception as exc:
            self.iface.messageBar().pushMessage("QBRA", f"Error: {exc}", level=Qgis.Critical)
            return

        self._dock.set_calculating(True)
        self._worker = BRAWorker(self.iface, params, parent=self)
        self._worker.finished.connect(self._on_calculation_finished)
        self._worker.error.connect(self._on_calculation_error)
        self._worker.finished.connect(lambda _: self._dock.set_calculating(False) if self._dock else None)
        self._worker.error.connect(lambda _: self._dock.set_calculating(False) if self._dock else None)
        self._worker.start()

    def _on_calculation_finished(self, result_layer: Optional[QgsVectorLayer]) -> None:
        """Receive the completed layer from BRAWorker and add it to the project."""
        if result_layer:
            QgsProject.instance().addMapLayer(result_layer)
            self.iface.messageBar().pushMessage(
                "QBRA",
                "BRA areas created successfully",
                level=Qgis.Success
            )

    def _on_calculation_error(self, message: str) -> None:
        """Receive an error message from BRAWorker and surface it to the user."""
        logger.error("BRA calculation failed: %s", message)
        self.iface.messageBar().pushMessage(
            "QBRA",
            f"Calculation error: {message}",
            level=Qgis.Critical
        )
