"""Tests for IlsLlzDockWidget — omni mode helpers and facility defaults."""

import sys
import types
import pytest
from unittest.mock import Mock, MagicMock, patch


# ---------------------------------------------------------------------------
# Patch QDockWidget to a plain Python class BEFORE importing the dockwidget.
# The conftest already injected qgis.PyQt.QtWidgets as a MagicMock; here we
# replace just the QDockWidget attribute with a real base class so that
# IlsLlzDockWidget is a proper Python type (not a MagicMock subclass).
# ---------------------------------------------------------------------------
class _FakeQDockWidget:
    def __init__(self, *args, **kwargs):
        pass


_widgets_mod = sys.modules.get("qgis.PyQt.QtWidgets")
if _widgets_mod is not None:
    _widgets_mod.QDockWidget = _FakeQDockWidget

# Now import the real dockwidget class
from qBRA.dockwidgets.ils.ils_llz_dockwidget import IlsLlzDockWidget  # noqa: E402
from qBRA.services.validation_service import ValidationService          # noqa: E402
from qgis.core import QgsVectorLayer                                    # noqa: E402


def _make_widget_mock(mode_text="Directional"):
    """Build a mock _widget with all UI controls needed by the dockwidget."""
    w = MagicMock()
    w.cboMode.currentText.return_value = mode_text
    w.cboFacility.currentData.return_value = "LOC"
    w.cboFacility.currentText.return_value = "ILS LLZ – single frequency"
    w.cboNavaidLayer.currentData.return_value = "layer-id-1"
    w.cboRoutingLayer.currentData.return_value = "layer-id-2"
    w.spnSiteElev.value.return_value = 100.0
    w.spnOmni_r.value.return_value = 300.0
    w.spnOmni_alpha.value.return_value = 1.0
    w.spnOmni_R.value.return_value = 3000.0
    w.chkOmniTurbine.isChecked.return_value = False
    w.spnOmni_j.value.return_value = 0.0
    w.spnOmni_h.value.return_value = 0.0
    w.txtOutputName.text.return_value = ""
    return w


def _make_dockwidget(mode_text="Directional"):
    """Return a partially initialised IlsLlzDockWidget with mocked Qt internals."""
    iface = Mock()
    iface.messageBar.return_value = Mock()

    dw = IlsLlzDockWidget.__new__(IlsLlzDockWidget)
    dw.iface = iface
    dw._validation_service = ValidationService()
    dw._layer_service = Mock()
    dw._widget = _make_widget_mock(mode_text)
    dw._init_mode_and_facilities()
    return dw


class TestIsOmniMode:
    def test_directional_returns_false(self):
        dw = _make_dockwidget("Directional")
        assert dw.is_omni_mode() is False

    def test_omni_returns_true(self):
        dw = _make_dockwidget("Omnidirectional")
        assert dw.is_omni_mode() is True

    def test_empty_defaults_to_directional(self):
        dw = _make_dockwidget("")
        assert dw.is_omni_mode() is False


class TestGetOmniParameters:
    def test_returns_none_when_no_layer(self):
        dw = _make_dockwidget("Omnidirectional")
        dw._widget.cboNavaidLayer.currentData.return_value = None
        with patch("qBRA.dockwidgets.ils.ils_llz_dockwidget.QgsProject") as mock_proj:
            mock_proj.instance.return_value.mapLayer.return_value = None
            result = dw.get_omni_parameters()
        assert result is None

    def test_returns_none_when_no_selection(self):
        dw = _make_dockwidget("Omnidirectional")
        layer = Mock()
        layer.__class__ = QgsVectorLayer
        layer.selectedFeatureCount.return_value = 0
        with patch("qBRA.dockwidgets.ils.ils_llz_dockwidget.QgsProject") as mock_proj:
            mock_proj.instance.return_value.mapLayer.return_value = layer
            result = dw.get_omni_parameters()
        assert result is None

    def test_returns_dict_when_valid(self):
        dw = _make_dockwidget("Omnidirectional")
        from qgis.core import QgsVectorLayer
        layer = Mock()
        layer.__class__ = QgsVectorLayer
        layer.selectedFeatureCount.return_value = 1
        with patch("qBRA.dockwidgets.ils.ils_llz_dockwidget.QgsProject") as mock_proj:
            mock_proj.instance.return_value.mapLayer.return_value = layer
            result = dw.get_omni_parameters()
        assert result is not None
        assert result["omni_r"] == 300.0
        assert result["omni_alpha"] == 1.0
        assert result["omni_R"] == 3000.0
        assert result["omni_turbine"] is False
        assert "active_layer" in result

    def test_display_name_uses_facility_label_when_no_custom(self):
        dw = _make_dockwidget("Omnidirectional")
        from qgis.core import QgsVectorLayer
        layer = Mock()
        layer.__class__ = QgsVectorLayer
        layer.selectedFeatureCount.return_value = 1
        with patch("qBRA.dockwidgets.ils.ils_llz_dockwidget.QgsProject") as mock_proj:
            mock_proj.instance.return_value.mapLayer.return_value = layer
            result = dw.get_omni_parameters()
        assert result["display_name"] == "ILS LLZ – single frequency"

    def test_display_name_combines_custom_and_label(self):
        dw = _make_dockwidget("Omnidirectional")
        dw._widget.txtOutputName.text.return_value = "EGLL"
        from qgis.core import QgsVectorLayer
        layer = Mock()
        layer.__class__ = QgsVectorLayer
        layer.selectedFeatureCount.return_value = 1
        with patch("qBRA.dockwidgets.ils.ils_llz_dockwidget.QgsProject") as mock_proj:
            mock_proj.instance.return_value.mapLayer.return_value = layer
            result = dw.get_omni_parameters()
        assert result["display_name"] == "EGLL - ILS LLZ – single frequency"


class TestOnModeChanged:
    def test_dir_mode_sets_correct_facilities(self):
        dw = _make_dockwidget("Directional")
        dw._on_mode_changed()
        # Directional: cboFacility populated with dir defs
        calls = dw._widget.cboFacility.addItem.call_args_list
        labels = [c[0][0] for c in calls]
        assert any("ILS LLZ" in lbl or "LOC" in lbl or "DME" in lbl for lbl in labels)

    def test_omni_mode_sets_omni_facilities(self):
        dw = _make_dockwidget("Omnidirectional")
        dw._on_mode_changed()
        calls = dw._widget.cboFacility.addItem.call_args_list
        labels = [c[0][0] for c in calls]
        assert any("omnidirectional" in lbl.lower() for lbl in labels)


class TestApplyFacilityDefaults:
    def test_gp_sets_fixed_a(self):
        """For GP facility, 'a' is fixed at 800 (not threshold-dependent)."""
        dw = _make_dockwidget("Directional")
        dw._widget.cboFacility.currentData.return_value = "GP"
        dw._apply_facility_defaults()
        dw._widget.spnA.setValue.assert_called_with(800.0)

    def test_loc_estimates_a_when_no_layers(self):
        """For LOC facility, 'a' should be estimated (returns 0.0 if no layers)."""
        dw = _make_dockwidget("Directional")
        dw._widget.cboFacility.currentData.return_value = "LOC"
        dw._widget.cboNavaidLayer.currentData.return_value = None
        with patch("qBRA.dockwidgets.ils.ils_llz_dockwidget.QgsProject") as mock_proj:
            mock_proj.instance.return_value.mapLayer.return_value = None
            dw._apply_facility_defaults()
        dw._widget.spnA.setValue.assert_called_with(0.0)

    def test_always_sets_b_regardless_of_a(self):
        """All params including b/h/D are applied even when 'a' is estimated."""
        dw = _make_dockwidget("Directional")
        dw._widget.cboFacility.currentData.return_value = "LOC"
        dw._widget.cboNavaidLayer.currentData.return_value = None
        with patch("qBRA.dockwidgets.ils.ils_llz_dockwidget.QgsProject") as mock_proj:
            mock_proj.instance.return_value.mapLayer.return_value = None
            dw._apply_facility_defaults()
        dw._widget.spnB.setValue.assert_called_with(500.0)
        dw._widget.spnh.setValue.assert_called_with(70.0)
