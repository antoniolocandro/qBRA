from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.core import QgsWkbTypes, QgsPoint, QgsVectorLayer
from qgis.utils import iface

import os

UI_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ui", "ils", "ils_llz_panel.ui")

class IlsLlzDockWidget(QDockWidget):
    calculateRequested = pyqtSignal()
    closedRequested = pyqtSignal()

    def __init__(self, iface_):
        super().__init__("QBRA ILS/LLZ")
        self.iface = iface_
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setObjectName("IlsLlzDockWidget")
        self._widget = uic.loadUi(UI_PATH)
        self.setWidget(self._widget)
        self._wire()
        self.refresh_layers()

    def defaultArea(self):
        return Qt.RightDockWidgetArea

    def _wire(self):
        self._widget.btnClose.clicked.connect(lambda: self.closedRequested.emit())
        self._widget.btnCalculate.clicked.connect(lambda: self.calculateRequested.emit())
        self._widget.btnDirection.clicked.connect(self._toggle_direction)

    def _toggle_direction(self):
        current = self._widget.btnDirection.property("direction") or "forward"
        new = "backward" if current == "forward" else "forward"
        self._widget.btnDirection.setProperty("direction", new)
        self._widget.btnDirection.setText("Backward" if new == "backward" else "Forward")

    def refresh_layers(self):
        """Fill navaid (point) and routing (line) combos from layers in the canvas.

        Logic follows the original script: routing layer is any layer whose
        name contains 'routing'; navaid layer defaults to the current active
        layer (point).
        """
        self._widget.cboNavaidLayer.clear()
        self._widget.cboRoutingLayer.clear()
        for layer in self.iface.mapCanvas().layers():
            # Skip non-vector layers (e.g., rasters) to avoid calling wkbType on them
            if not isinstance(layer, QgsVectorLayer):
                continue
            name = layer.name()
            gtype = QgsWkbTypes.geometryType(layer.wkbType())

            # Any line layer can be used as routing/runway
            if gtype == QgsWkbTypes.LineGeometry:
                self._widget.cboRoutingLayer.addItem(name, layer)

            # Any point layer can be used as navaid
            if gtype == QgsWkbTypes.PointGeometry:
                self._widget.cboNavaidLayer.addItem(name, layer)

        # Default navaid: current active layer if it is a point layer
        al = iface.activeLayer()
        if al and isinstance(al, QgsVectorLayer):
            gtype = QgsWkbTypes.geometryType(al.wkbType())
            if gtype == QgsWkbTypes.PointGeometry:
                idx = self._widget.cboNavaidLayer.findText(al.name())
                if idx >= 0:
                    self._widget.cboNavaidLayer.setCurrentIndex(idx)


    def get_parameters(self):
        navaid_layer = self._widget.cboNavaidLayer.currentData()
        routing_layer = self._widget.cboRoutingLayer.currentData()
        # Basic presence validation with debug logs
        if not navaid_layer:
            print("QBRA ILS/LLZ: no navaid layer selected")
            return None
        if not routing_layer:
            print("QBRA ILS/LLZ: no routing layer selected")
            return None
        selection = navaid_layer.selectedFeatures()
        if not selection:
            print("QBRA ILS/LLZ: no navaid feature selected")
            return None
        feat = selection[0]
        attrs = feat.attributes()

        # Site elevation comes directly from UI numeric parameter
        site_elev = float(self._widget.spnSiteElev.value())

        # Runway remark: try to find a sensible field, else use FID
        fields = navaid_layer.fields()
        rwy_field_candidates = ["runway", "rwy", "thr_rwy"]
        rwy_idx = -1
        for name in rwy_field_candidates:
            idx = fields.indexFromName(name)
            if idx >= 0:
                rwy_idx = idx
                break
        if rwy_idx < 0:
            # Fallback: use feature id as runway label
            remark = f"RWY{feat.id()}"
        else:
            remark = f"RWY{attrs[rwy_idx]}"

        # Compute azimuth from selected routing feature (as in legacy script)
        routing_sel = routing_layer.selectedFeatures()
        if not routing_sel:
            print("QBRA ILS/LLZ: no routing feature selected")
            return None

        geom = routing_sel[0].geometry()
        if geom.isMultipart():
            pts = geom.asMultiPolyline()[0]
        else:
            pts = geom.asPolyline()
        if not pts or len(pts) < 2:
            print("QBRA ILS/LLZ: routing geometry has insufficient vertices")
            return None

        start_point = QgsPoint(pts[0])
        end_point = QgsPoint(pts[-1])
        azimuth = start_point.azimuth(end_point)
        print(f"QBRA ILS/LLZ: azimuth={azimuth}, d0={geom.length()}")

        # Parameters preset for DME case (from legacy script)
        a = 300
        b = 20
        h = 70
        r = 6000 + a
        D = 600
        H = 20
        L = 1500
        phi = 40

        return {
            "active_layer": navaid_layer,
            "azimuth": azimuth,
            "a": a,
            "b": b,
            "h": h,
            "r": r,
            "D": D,
            "H": H,
            "L": L,
            "phi": phi,
            "remark": remark,
            "site_elev": site_elev,
        }
