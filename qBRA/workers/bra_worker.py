"""Background worker for BRA layer calculation.

Runs ``build_layers`` on a dedicated QThread so the QGIS UI stays responsive
during the geometry computation.

Usage
-----
    worker = BRAWorker(iface, params)
    worker.finished.connect(on_finished)   # receives QgsVectorLayer
    worker.error.connect(on_error)         # receives error message str
    worker.start()
"""

from typing import Any

from qgis.PyQt.QtCore import QThread, pyqtSignal
from qgis.core import QgsVectorLayer

from ..models.bra_parameters import BRAParameters
from ..modules.ils_llz_logic import build_layers
from ..exceptions import BRACalculationError


class BRAWorker(QThread):
    """QThread that executes BRA geometry calculation off the main thread.

    Signals
    -------
    finished(QgsVectorLayer)
        Emitted when calculation completes successfully.
    error(str)
        Emitted when calculation fails; carries a user-readable message.
    """

    finished: pyqtSignal = pyqtSignal(object)   # QgsVectorLayer
    error: pyqtSignal = pyqtSignal(str)

    def __init__(self, iface: Any, params: BRAParameters, parent: Any = None) -> None:
        """Initialise the worker.

        Args:
            iface: QGIS interface object (passed through to build_layers).
            params: Validated BRAParameters for the calculation.
            parent: Optional Qt parent object.
        """
        super().__init__(parent)
        self._iface = iface
        self._params = params

    def run(self) -> None:
        """Execute build_layers and emit finished or error signal."""
        try:
            layer: QgsVectorLayer = build_layers(self._iface, self._params)
            self.finished.emit(layer)
        except BRACalculationError as e:
            self.error.emit(e.message)
        except Exception as e:
            self.error.emit(f"{type(e).__name__}: {e}")
