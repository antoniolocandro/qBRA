from typing import Any, Optional, Dict, Tuple

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.core import QgsWkbTypes, QgsPoint, QgsVectorLayer, QgsProject
from qgis.utils import iface

import os

from ...models.bra_parameters import BRAParameters, FacilityConfig, FacilityDefaults

UI_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ui", "ils", "ils_llz_panel.ui")

class IlsLlzDockWidget(QDockWidget):
    calculateRequested = pyqtSignal()
    closedRequested = pyqtSignal()
    
    _facility_defs: Dict[str, FacilityConfig]

    def __init__(self, iface_: Any) -> None:
        """Initialize the ILS/LLZ dock widget.
        
        Args:
            iface_: QGIS interface object
        """
        super().__init__("QBRA ILS/LLZ")
        self.iface = iface_
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setObjectName("IlsLlzDockWidget")
        self._widget = uic.loadUi(UI_PATH)
        self.setWidget(self._widget)
        self._wire()
        self._init_facility()
        self.refresh_layers()

    def defaultArea(self) -> Qt.DockWidgetArea:
        """Return the default dock widget area.
        
        Returns:
            The right dock widget area
        """
        return Qt.RightDockWidgetArea

    def _wire(self) -> None:
        """Wire up UI signal connections."""
        self._widget.btnClose.clicked.connect(lambda: self.closedRequested.emit())
        self._widget.btnCalculate.clicked.connect(lambda: self.calculateRequested.emit())
        self._widget.btnDirection.clicked.connect(self._toggle_direction)
        # Default direction: start to end
        self._widget.btnDirection.setProperty("direction", "forward")
        self._widget.btnDirection.setText("Direction: Start to End")

    def _init_facility(self) -> None:
        """Initialize facility type dropdown with predefined configurations."""
        self._facility_defs = {
            "LOC": FacilityConfig(
                key="LOC",
                label="ILS LLZ – single frequency",
                a_depends_on_threshold=True,
                defaults=FacilityDefaults(b=500, h=70, D=500, H=10, L=2300, phi=30, r_expr="a+6000")
            ),
            "LOCII": FacilityConfig(
                key="LOCII",
                label="ILS LLZ – dual frequency",
                a_depends_on_threshold=True,
                defaults=FacilityDefaults(b=500, h=70, D=500, H=20, L=1500, phi=20, r_expr="a+6000")
            ),
            "GP": FacilityConfig(
                key="GP",
                label="ILS GP M-Type (dual)",
                a_depends_on_threshold=False,
                defaults=FacilityDefaults(a=800, b=50, h=70, D=250, H=5, L=325, phi=10, r=6000)
            ),
            "DME": FacilityConfig(
                key="DME",
                label="DME (directional)",
                a_depends_on_threshold=True,
                defaults=FacilityDefaults(b=20, h=70, D=600, H=20, L=1500, phi=40, r_expr="a+6000")
            ),
        }
        cb = self._widget.cboFacility
        cb.clear()
        for key, config in self._facility_defs.items():
            cb.addItem(config.label, key)
        cb.currentIndexChanged.connect(self._apply_facility_defaults)
        # Update r when A changes for types where r depends on a
        self._widget.spnA.valueChanged.connect(self._maybe_update_r)
        # Set initial
        cb.setCurrentIndex(0)
        self._apply_facility_defaults()

    def _maybe_update_r(self) -> None:
        """Update r parameter based on facility type if it depends on a."""
        key = self._widget.cboFacility.currentData()
        config = self._facility_defs.get(key)
        if config is None:
            return
        
        r_expr = config.defaults.r_expr
        if r_expr == "a+6000":
            a = float(self._widget.spnA.value())
            self._widget.spnr.setValue(a + 6000.0)

    def _apply_facility_defaults(self) -> None:
        """Apply default parameter values based on the selected facility type."""
        key = self._widget.cboFacility.currentData()
        config = self._facility_defs.get(key)
        if config is None:
            return
        
        defs = config.defaults
        # A: if explicitly present in defaults, set; if depends on threshold, try to estimate from routing start
        if defs.a is not None:
            self._widget.spnA.setValue(float(defs.a))
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
        self._widget.spnB.setValue(float(defs.b))
        self._widget.spnh.setValue(float(defs.h))
        self._widget.spnD.setValue(float(defs.D))
        self._widget.spnH.setValue(float(defs.H))
        self._widget.spnL.setValue(float(defs.L))
        self._widget.spnPhi.setValue(float(defs.phi))
        if defs.r is not None:
            self._widget.spnr.setValue(float(defs.r))
        else:
            self._maybe_update_r()

    def _toggle_direction(self) -> None:
        """Toggle routing direction between forward and backward."""
        current = self._widget.btnDirection.property("direction") or "forward"
        new = "backward" if current == "forward" else "forward"
        self._widget.btnDirection.setProperty("direction", new)
        label = "Direction: End to Start" if new == "backward" else "Direction: Start to End"
        self._widget.btnDirection.setText(label)

    def refresh_layers(self) -> None:
        """Fill navaid (point) and routing (line) combos from layers in the canvas.

        Logic follows the original script: routing layer is any layer whose
        name contains 'routing'; navaid layer defaults to the current active
        layer (point).
        """
        self._widget.cboNavaidLayer.clear()
        self._widget.cboRoutingLayer.clear()
        # Collect layers via the layer tree to include layers inside groups
        root = QgsProject.instance().layerTreeRoot()
        def visit(node: Any) -> None:
            """Recursively visit layer tree nodes to collect layers."""
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


    def get_parameters(self) -> Optional[BRAParameters]:
        """Extract and validate all parameters from the UI.
        
        Returns:
            BRAParameters object with all calculation parameters, or None if validation fails
        """
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

        # Facility type (key) and label for naming
        facility_key = self._widget.cboFacility.currentData()
        facility_label = self._widget.cboFacility.currentText()

        # Output naming: user-provided name concatenated with facility label
        custom_name = (self._widget.txtOutputName.text() or "").strip()
        base_name = custom_name if custom_name else remark
        display_name = f"{base_name} - {facility_label}" if facility_label else base_name

        try:
            return BRAParameters(
                active_layer=navaid_layer,
                azimuth=azimuth,
                a=a,
                b=b,
                h=h,
                r=r,
                D=D,
                H=H,
                L=L,
                phi=phi,
                site_elev=site_elev,
                remark=remark,
                direction=direction,
                facility_key=facility_key,
                facility_label=facility_label,
                display_name=display_name,
            )
        except ValueError as e:
            print(f"QBRA ILS/LLZ: Invalid parameters - {e}")
            return None
