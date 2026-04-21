from typing import Any, Optional, Dict, Tuple

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QDockWidget
from ...utils.qt_compat import LeftDockWidgetArea, RightDockWidgetArea, MsgWarning, MsgCritical
from qgis.core import QgsWkbTypes, QgsPoint, QgsVectorLayer, QgsProject

import os
import re

from ...models.bra_parameters import BRAParameters
from ...services.validation_service import ValidationService, ValidationError
from ...services.layer_service import LayerService
from ...exceptions import BRACalculationError
from ...utils.logging_config import get_logger

# Module logger
logger = get_logger(__name__)

UI_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ui", "ils", "ils_llz_panel.ui")

class IlsLlzDockWidget(QDockWidget):
    calculateRequested = pyqtSignal()
    closedRequested = pyqtSignal()
    
    _facility_defs_dir: Dict[str, Tuple]
    _facility_defs_omni: Dict[str, Tuple]
    _validation_service: ValidationService
    _layer_service: LayerService

    def __init__(self, iface_: Any) -> None:
        """Initialize the ILS/LLZ dock widget.
        
        Args:
            iface_: QGIS interface object
        """
        super().__init__("QBRA ILS/LLZ")
        self.iface = iface_
        
        # Initialize services (dependency injection)
        self._validation_service = ValidationService()
        self._layer_service = LayerService(iface_)
        
        self.setAllowedAreas(LeftDockWidgetArea | RightDockWidgetArea)
        self.setObjectName("IlsLlzDockWidget")
        self._widget = uic.loadUi(UI_PATH)
        self.setWidget(self._widget)
        self._wire()
        self._init_mode_and_facilities()
        self.refresh_layers()

    def defaultArea(self) -> Qt.DockWidgetArea:
        """Return the default dock widget area.
        
        Returns:
            The right dock widget area
        """
        return RightDockWidgetArea

    def _wire(self) -> None:
        """Wire up UI signal connections."""
        self._widget.btnClose.clicked.connect(lambda: self.closedRequested.emit())
        self._widget.btnCalculate.clicked.connect(lambda: self.calculateRequested.emit())
        self._widget.btnDirection.clicked.connect(self._toggle_direction)
        # Default direction: start to end
        self._widget.btnDirection.setProperty("direction", "forward")
        self._widget.btnDirection.setText("Direction: Start to End")

    def _init_mode_and_facilities(self):
        # Directional facilities
        self._facility_defs_dir = {
            # key: (label, a_depends_threshold, defaults)
            "LOC": ("ILS LLZ – single frequency", True, {"b": 500, "h": 70, "D": 500, "H": 10, "L": 2300, "phi": 30, "r_expr": "a+6000"}),
            "LOCII": ("ILS LLZ – dual frequency", True, {"b": 500, "h": 70, "D": 500, "H": 20, "L": 1500, "phi": 20, "r_expr": "a+6000"}),
            "GP": ("ILS GP M-Type (dual)", False, {"a": 800, "b": 50, "h": 70, "D": 250, "H": 5, "L": 325, "phi": 10, "r": 6000}),
            "DME": ("DME (directional)", True, {"b": 20, "h": 70, "D": 600, "H": 20, "L": 1500, "phi": 40, "r_expr": "a+6000"}),
        }
        # Omnidirectional facilities presets (initial set)
        self._facility_defs_omni = {
            # key: (label, defaults for r, alpha, R, optional j/h)
            "OMNI_DME_N": ("DME N (omnidirectional)", {"r": 300, "alpha": 1.0, "R": 3000}),
            "OMNI_CVOR": ("CVOR (omnidirectional)", {"r": 600, "alpha": 1.0, "R": 3000, "j": 15000, "h": 52}),
            "OMNI_DVOR": ("DVOR (omnidirectional)", {"r": 600, "alpha": 1.0, "R": 3000, "j": 10000, "h": 52}),
            "OMNI_DF": ("Direction Finder (omnidirectional)", {"r": 500, "alpha": 1.0, "R": 3000, "j": 10000, "h": 52}),
            "OMNI_MARKERS": ("Markers (omnidirectional)", {"r": 50, "alpha": 20.0, "R": 200}),
            "OMNI_NDB": ("NDB (omnidirectional)", {"r": 200, "alpha": 5.0, "R": 1000}),
            "OMNI_GBAS_REF": ("GBAS ground Reference receiver", {"r": 400, "alpha": 3.0, "R": 3000}),
            "OMNI_GBAS_VDB": ("GBAS VDB station", {"r": 300, "alpha": 0.9, "R": 3000}),
            "OMNI_VDB_MON": ("VDB station monitoring station", {"r": 400, "alpha": 3.0, "R": 3000}),
            "OMNI_VHF_TX": ("VHF Communication Tx", {"r": 300, "alpha": 1.0, "R": 2000}),
            "OMNI_VHF_RX": ("VHF Communication Rx", {"r": 300, "alpha": 1.0, "R": 2000}),
            "OMNI_PSR": ("PSR (surveillance)", {"r": 500, "alpha": 0.25, "R": 15000}),
            "OMNI_SSR": ("SSR (surveillance)", {"r": 500, "alpha": 0.25, "R": 15000}),
        }

        # connect handlers
        self._widget.cboMode.currentIndexChanged.connect(self._on_mode_changed)
        self._widget.cboFacility.currentIndexChanged.connect(self._on_facility_changed)
        self._widget.spnA.valueChanged.connect(self._maybe_update_r)
        self._widget.chkOmniTurbine.toggled.connect(self._on_turbine_toggle)
        # initialize
        self._on_mode_changed()

    def _on_mode_changed(self):
        mode_text = self._widget.cboMode.currentText() or "Directional"
        is_omni = mode_text.lower().startswith("omni")
        # toggle parameter groups
        self._widget.grpParameters.setVisible(not is_omni)
        self._widget.grpOmniParameters.setVisible(is_omni)
        # populate facilities
        cb = self._widget.cboFacility
        cb.blockSignals(True)
        cb.clear()
        if is_omni:
            for key, (label, _defs) in self._facility_defs_omni.items():
                cb.addItem(label, key)
        else:
            for key, (label, _dep, _defs) in self._facility_defs_dir.items():
                cb.addItem(label, key)
        cb.blockSignals(False)
        # apply defaults for the initial selection
        self._on_facility_changed()

    def _on_turbine_toggle(self, checked):
        self._set_turbine_fields(enabled=checked, reset=False)

    def _on_facility_changed(self):
        mode_text = self._widget.cboMode.currentText() or "Directional"
        is_omni = mode_text.lower().startswith("omni")
        if is_omni:
            self._apply_omni_defaults()
        else:
            self._apply_facility_defaults()

    def _maybe_update_r(self) -> None:
        """Update r parameter based on facility type if it depends on a."""
        key = self._widget.cboFacility.currentData()
        defs = self._facility_defs_dir.get(key, (None, False, {}))[2]
        r_expr = defs.get("r_expr")
        if r_expr == "a+6000":
            a = float(self._widget.spnA.value())
            self._widget.spnr.setValue(a + 6000.0)

    def _estimate_a_from_layers(self) -> float:
        """Estimate the 'a' parameter (navaid-to-threshold distance) from selected layers.

        Returns:
            Estimated distance in metres, or 0.0 if layers/features are not ready.
        """
        try:
            nlayer_id = self._widget.cboNavaidLayer.currentData()
            rlayer_id = self._widget.cboRoutingLayer.currentData()
            nlayer = QgsProject.instance().mapLayer(nlayer_id) if nlayer_id else None
            rlayer = QgsProject.instance().mapLayer(rlayer_id) if rlayer_id else None

            if not nlayer or not rlayer:
                return 0.0

            if nlayer.selectedFeatureCount() == 0 or rlayer.selectedFeatureCount() == 0:
                return 0.0

            nfeat = nlayer.selectedFeatures()[0]
            rfeat = rlayer.selectedFeatures()[0]
            geom = rfeat.geometry()

            pts = geom.asMultiPolyline()[0] if geom.isMultipart() else geom.asPolyline()
            if not pts or len(pts) < 2:
                raise BRACalculationError(
                    "Routing geometry has insufficient vertices",
                    f"Need at least 2 points, got {len(pts) if pts else 0}",
                )

            direction = self._widget.btnDirection.property("direction") or "forward"
            pick = pts[0] if direction == "forward" else pts[-1]
            # Both pick and npt are QgsPointXY — use QgsPointXY.distance() directly
            npt = nfeat.geometry().asPoint()
            return pick.distance(npt)

        except BRACalculationError as e:
            logger.warning("Could not estimate parameter 'a': %s", e.message)
            return 0.0
        except (AttributeError, IndexError, TypeError) as e:
            logger.debug("Cannot estimate 'a' from geometry: %s", e)
            return 0.0
        except Exception as e:
            logger.error("Unexpected error estimating 'a': %s", e, exc_info=True)
            return 0.0

    def _apply_facility_defaults(self) -> None:
        """Apply default parameter values based on the selected facility type."""
        key = self._widget.cboFacility.currentData()
        entry = self._facility_defs_dir.get(key)
        if entry is None:
            return

        _label, _a_dep, defs = entry
        # A: if explicitly present in defaults, set it; otherwise estimate from layers.
        # The estimation may return 0.0 on initial load (no layers yet) — that is fine.
        a_default = defs.get("a")
        if a_default is not None:
            self._widget.spnA.setValue(float(a_default))
        else:
            self._widget.spnA.setValue(self._estimate_a_from_layers())

        # Always apply all other facility defaults regardless of 'a' estimation outcome.
        self._widget.spnB.setValue(float(defs["b"]))
        self._widget.spnh.setValue(float(defs["h"]))
        self._widget.spnD.setValue(float(defs["D"]))
        self._widget.spnH.setValue(float(defs["H"]))
        self._widget.spnL.setValue(float(defs["L"]))
        self._widget.spnPhi.setValue(float(defs["phi"]))
        r_default = defs.get("r")
        if r_default is not None:
            self._widget.spnr.setValue(float(r_default))
        else:
            self._maybe_update_r()

    def _apply_omni_defaults(self):
        key = self._widget.cboFacility.currentData()
        defs = self._facility_defs_omni.get(key, ("", {}))[1]
        self._widget.spnOmni_r.setValue(float(defs.get("r", 0)))
        self._widget.spnOmni_alpha.setValue(float(defs.get("alpha", 1)))
        self._widget.spnOmni_R.setValue(float(defs.get("R", 0)))
        has_turbine = ("j" in defs and "h" in defs)
        # block signal to avoid resetting user toggles when applying defaults
        self._widget.chkOmniTurbine.blockSignals(True)
        self._widget.chkOmniTurbine.setChecked(has_turbine)
        self._widget.chkOmniTurbine.blockSignals(False)
        self._set_turbine_fields(enabled=has_turbine, preset_j=defs.get("j"), preset_h=defs.get("h"), reset=True)

    def _set_turbine_fields(self, enabled, preset_j=None, preset_h=None, reset=False):
        self._widget.spnOmni_j.setEnabled(enabled)
        self._widget.spnOmni_h.setEnabled(enabled)
        if not enabled:
            # keep values but make them inert when toggle is off
            return
        if reset:
            if preset_j is not None:
                self._widget.spnOmni_j.setValue(float(preset_j))
            if preset_h is not None:
                self._widget.spnOmni_h.setValue(float(preset_h))

    def _toggle_direction(self):
        current = self._widget.btnDirection.property("direction") or "forward"
        new = "backward" if current == "forward" else "forward"
        self._widget.btnDirection.setProperty("direction", new)
        label = "Direction: End to Start" if new == "backward" else "Direction: Start to End"
        self._widget.btnDirection.setText(label)

    def refresh_layers(self) -> None:
        """Fill navaid (point) and routing (line) combos from layers in the canvas.

        Uses LayerService to discover layers from the project.
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
                        self._widget.cboRoutingLayer.addItem(name, layer.id())
                    if gtype == QgsWkbTypes.PointGeometry:
                        self._widget.cboNavaidLayer.addItem(name, layer.id())
                elif child.nodeType() == child.NodeGroup:
                    visit(child)
        visit(root)

        # Default navaid: current active layer if it is a point layer
        al = self.iface.activeLayer()
        if al and isinstance(al, QgsVectorLayer):
            gtype = QgsWkbTypes.geometryType(al.wkbType())
            if gtype == QgsWkbTypes.PointGeometry:
                idx = self._widget.cboNavaidLayer.findText(al.name())
                if idx >= 0:
                    self._widget.cboNavaidLayer.setCurrentIndex(idx)


    def set_calculating(self, calculating: bool) -> None:
        """Enable/disable the Calculate button during background calculation."""
        self._widget.btnCalculate.setEnabled(not calculating)
        self._widget.btnCalculate.setText("Calculating\u2026" if calculating else "Calculate")

    def is_omni_mode(self) -> bool:
        """Return True if the current mode is omnidirectional."""
        mode_text = self._widget.cboMode.currentText() or "Directional"
        return mode_text.lower().startswith("omni")

    def get_omni_parameters(self) -> Optional[dict]:
        """Extract omnidirectional parameters from the UI.

        Returns:
            Dict with omni params, or None if no navaid layer/feature is selected.
        """
        navaid_layer_id = self._widget.cboNavaidLayer.currentData()
        navaid_layer = QgsProject.instance().mapLayer(navaid_layer_id) if navaid_layer_id else None
        if not navaid_layer:
            self.iface.messageBar().pushMessage("QBRA", "No navaid layer selected", level=MsgWarning)
            return None
        if not navaid_layer.selectedFeatureCount():
            self.iface.messageBar().pushMessage("QBRA", "No navaid feature selected", level=MsgWarning)
            return None

        site_elev = float(self._widget.spnSiteElev.value())
        facility_key = self._widget.cboFacility.currentData()
        facility_label = self._widget.cboFacility.currentText()
        custom_name = (self._widget.txtOutputName.text() or "").strip()
        display_name = (
            f"{custom_name} - {facility_label}"
            if custom_name and facility_label
            else (custom_name or facility_label or "BRA")
        )

        return {
            "active_layer": navaid_layer,
            "site_elev": site_elev,
            "facility_key": facility_key,
            "facility_label": facility_label,
            "display_name": display_name,
            "omni_r": float(self._widget.spnOmni_r.value()),
            "omni_alpha": float(self._widget.spnOmni_alpha.value()),
            "omni_R": float(self._widget.spnOmni_R.value()),
            "omni_turbine": bool(self._widget.chkOmniTurbine.isChecked()),
            "omni_j": float(self._widget.spnOmni_j.value()),
            "omni_h": float(self._widget.spnOmni_h.value()),
        }

    def get_parameters(self) -> Optional[BRAParameters]:
        """Extract and validate all parameters from the UI.

        Returns:
            BRAParameters object with all calculation parameters, or None if validation fails.
        """
        try:
            # Resolve layer IDs to actual layer objects (combos store IDs since fix #24)
            navaid_layer_id = self._widget.cboNavaidLayer.currentData()
            routing_layer_id = self._widget.cboRoutingLayer.currentData()
            navaid_layer = QgsProject.instance().mapLayer(navaid_layer_id) if navaid_layer_id else None
            routing_layer = QgsProject.instance().mapLayer(routing_layer_id) if routing_layer_id else None

            # Validate layers using ValidationService
            self._validation_service.validate_layer_selected(navaid_layer, "navaid layer")
            self._validation_service.validate_layer_selected(routing_layer, "routing layer")
            self._validation_service.validate_feature_selected(navaid_layer, "navaid layer")
            self._validation_service.validate_feature_selected(routing_layer, "routing layer")
            self._validation_service.validate_geometry_vertices(routing_layer, min_vertices=2, layer_name="routing layer")

            # Get selected features
            feat = navaid_layer.selectedFeatures()[0]
            attrs = feat.attributes()

            # Site elevation comes directly from UI numeric parameter
            site_elev = float(self._widget.spnSiteElev.value())

            # Runway remark: find and normalize runway identifier
            def _format_runway(val):
                s = str(val).strip().upper()
                m = re.search(r"(?<!\d)(\d{1,2})([LRC])?", s)
                if m:
                    try:
                        num = int(m.group(1))
                    except Exception:
                        return "RWYXX"
                    suffix = m.group(2) or ""
                    return f"RWY{num:02d}{suffix}"
                m2 = re.search(r"RWY\s*(\d{1,2})([LRC])?", s)
                if m2:
                    try:
                        num = int(m2.group(1))
                    except Exception:
                        return "RWYXX"
                    suffix = m2.group(2) or ""
                    return f"RWY{num:02d}{suffix}"
                return "RWYXX"

            rwy_idx = self._layer_service.find_field_index(navaid_layer, ["runway", "rwy", "thr_rwy"])
            if rwy_idx < 0:
                remark = f"RWY{feat.id()}"
            else:
                remark = _format_runway(attrs[rwy_idx])

            # Compute azimuth from selected routing feature
            routing_feat = routing_layer.selectedFeatures()[0]
            geom = routing_feat.geometry()

            # Get vertices based on geometry type
            if geom.isMultipart():
                pts = geom.asMultiPolyline()[0]
            else:
                pts = geom.asPolyline()

            # Apply direction setting to routing points
            direction = self._widget.btnDirection.property("direction") or "forward"
            ordered_pts = pts if direction == "forward" else list(reversed(pts))
            # QgsPoint(x, y) is required for azimuth(); QgsPointXY does not have azimuth()
            p0 = ordered_pts[0]
            p1 = ordered_pts[-1]
            start_point = QgsPoint(p0.x(), p0.y())
            end_point = QgsPoint(p1.x(), p1.y())
            # QgsPoint.azimuth() returns [-180, 180]; normalize to [0, 360)
            azimuth = start_point.azimuth(end_point) % 360

            logger.debug(
                "Calculated azimuth from routing geometry: direction=%s, azimuth=%.2f, distance=%.2f",
                direction, azimuth, geom.length()
            )

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

            # Output naming: user-provided name concatenated with facility label
            custom_name = (self._widget.txtOutputName.text() or "").strip()
            base_name = custom_name if custom_name else remark
            display_name = f"{base_name} - {facility_label}" if facility_label else base_name

            # Create BRAParameters (with built-in validation)
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

        except (ValidationError, ValueError) as e:
            logger.warning("Parameter validation failed: %s", e)
            self.iface.messageBar().pushMessage(
                "QBRA",
                str(e),
                level=MsgWarning,
            )
            return None
        except Exception as e:
            logger.error("Unexpected error while extracting parameters: %s", e, exc_info=True)
            self.iface.messageBar().pushMessage(
                "QBRA",
                f"Unexpected error: {e}",
                level=MsgCritical,
            )
            return None
