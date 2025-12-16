from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.core import QgsWkbTypes, QgsPoint, QgsVectorLayer, QgsProject
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
        self._init_facility()
        self.refresh_layers()

    def defaultArea(self):
        return Qt.RightDockWidgetArea

    def _wire(self):
        self._widget.btnClose.clicked.connect(lambda: self.closedRequested.emit())
        self._widget.btnCalculate.clicked.connect(lambda: self.calculateRequested.emit())
        self._widget.btnDirection.clicked.connect(self._toggle_direction)
        # Default direction: start to end
        self._widget.btnDirection.setProperty("direction", "forward")
        self._widget.btnDirection.setText("Direction: Start to End")

    def _init_facility(self):
        self._facility_defs = {
            # key: (label, a_depends_threshold, defaults)
            "LOC": ("ILS LLZ – single frequency", True, {"b": 500, "h": 70, "D": 500, "H": 10, "L": 2300, "phi": 30, "r_expr": "a+6000"}),
            "LOCII": ("ILS LLZ – dual frequency", True, {"b": 500, "h": 70, "D": 500, "H": 20, "L": 1500, "phi": 20, "r_expr": "a+6000"}),
            "GP": ("ILS GP M-Type (dual)", False, {"a": 800, "b": 50, "h": 70, "D": 250, "H": 5, "L": 325, "phi": 10, "r": 6000}),
            "DME": ("DME (directional)", True, {"b": 20, "h": 70, "D": 600, "H": 20, "L": 1500, "phi": 40, "r_expr": "a+6000"}),
        }
        cb = self._widget.cboFacility
        cb.clear()
        for key, (label, _dep, _defs) in self._facility_defs.items():
            cb.addItem(label, key)
        cb.currentIndexChanged.connect(self._apply_facility_defaults)
        # Update r when A changes for types where r depends on a
        self._widget.spnA.valueChanged.connect(self._maybe_update_r)
        # Set initial
        cb.setCurrentIndex(0)
        self._apply_facility_defaults()

    def _maybe_update_r(self):
        key = self._widget.cboFacility.currentData()
        defs = self._facility_defs.get(key, (None, False, {}))[2]
        r_expr = defs.get("r_expr")
        if r_expr == "a+6000":
            a = float(self._widget.spnA.value())
            self._widget.spnr.setValue(a + 6000.0)

    def _apply_facility_defaults(self):
        key = self._widget.cboFacility.currentData()
        label, a_dep, defs = self._facility_defs.get(key, ("", False, {}))
        # A: if explicitly present in defaults, set; if depends on threshold, try to estimate from routing start
        if "a" in defs:
            self._widget.spnA.setValue(float(defs["a"]))
        else:
            # try estimate: distance from navaid to routing start/end depending on direction
            try:
                nlayer = self._widget.cboNavaidLayer.currentData()
                rlayer = self._widget.cboRoutingLayer.currentData()
                nfeat = nlayer.selectedFeatures()[0]
                rfeat = rlayer.selectedFeatures()[0]
                geom = rfeat.geometry()
                pts = geom.asMultiPolyline()[0] if geom.isMultipart() else geom.asPolyline()
                if not pts or len(pts) < 2:
                    raise Exception()
                direction = self._widget.btnDirection.property("direction") or "forward"
                pick = pts[0] if direction == "forward" else pts[-1]
                a_val = QgsPoint(pick).distance(QgsPoint(nfeat.geometry().asPoint()))
                self._widget.spnA.setValue(a_val)
            except Exception:
                self._widget.spnA.setValue(0.0)
        # Other parameters
        self._widget.spnB.setValue(float(defs.get("b", self._widget.spnB.value())))
        self._widget.spnh.setValue(float(defs.get("h", self._widget.spnh.value())))
        self._widget.spnD.setValue(float(defs.get("D", self._widget.spnD.value())))
        self._widget.spnH.setValue(float(defs.get("H", self._widget.spnH.value())))
        self._widget.spnL.setValue(float(defs.get("L", self._widget.spnL.value())))
        self._widget.spnPhi.setValue(float(defs.get("phi", self._widget.spnPhi.value())))
        if "r" in defs:
            self._widget.spnr.setValue(float(defs["r"]))
        else:
            self._maybe_update_r()

    def _toggle_direction(self):
        current = self._widget.btnDirection.property("direction") or "forward"
        new = "backward" if current == "forward" else "forward"
        self._widget.btnDirection.setProperty("direction", new)
        label = "Direction: End to Start" if new == "backward" else "Direction: Start to End"
        self._widget.btnDirection.setText(label)

    def refresh_layers(self):
        """Fill navaid (point) and routing (line) combos from layers in the canvas.

        Logic follows the original script: routing layer is any layer whose
        name contains 'routing'; navaid layer defaults to the current active
        layer (point).
        """
        self._widget.cboNavaidLayer.clear()
        self._widget.cboRoutingLayer.clear()
        # Collect layers via the layer tree to include layers inside groups
        root = QgsProject.instance().layerTreeRoot()
        def visit(node):
            for child in node.children():
                if child.nodeType() == child.NodeLayer:
                    layer = child.layer()
                    if not isinstance(layer, QgsVectorLayer):
                        continue
                    name = layer.name()
                    gtype = QgsWkbTypes.geometryType(layer.wkbType())
                    if gtype == QgsWkbTypes.LineGeometry:
                        self._widget.cboRoutingLayer.addItem(name, layer)
                    if gtype == QgsWkbTypes.PointGeometry:
                        self._widget.cboNavaidLayer.addItem(name, layer)
                elif child.nodeType() == child.NodeGroup:
                    visit(child)
        visit(root)

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

        # Apply direction setting to routing points
        direction = self._widget.btnDirection.property("direction") or "forward"
        ordered_pts = pts if direction == "forward" else list(reversed(pts))
        start_point = QgsPoint(ordered_pts[0])
        end_point = QgsPoint(ordered_pts[-1])
        azimuth = start_point.azimuth(end_point)
        print(f"QBRA ILS/LLZ: direction={direction}, azimuth={azimuth}, d0={geom.length()}")

        # Parameters come from UI (facility defaults applied on selection)
        a = float(self._widget.spnA.value())
        b = float(self._widget.spnB.value())
        h = float(self._widget.spnh.value())
        r = float(self._widget.spnr.value())
        D = float(self._widget.spnD.value())
        H = float(self._widget.spnH.value())
        L = float(self._widget.spnL.value())
        phi = float(self._widget.spnPhi.value())
        # Facility type (key) and label
        facility_key = self._widget.cboFacility.currentData()
        facility_label = self._widget.cboFacility.currentText()

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
            "direction": direction,
            "site_elev": site_elev,
            "facility_key": facility_key,
            "facility_label": facility_label,
        }
