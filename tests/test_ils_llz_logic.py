"""Tests for ILS/LLZ logic functions."""

import pytest
from unittest.mock import Mock, patch

try:
    from qgis.core import QgsPoint, QgsGeometry, QgsPolygon, QgsLineString
    QGIS_AVAILABLE = True
except ImportError:
    QGIS_AVAILABLE = False


@pytest.mark.skipif(not QGIS_AVAILABLE, reason="QGIS not available")
class TestCreateFeature:
    """Test create_feature() function."""

    def test_create_feature_with_valid_inputs(self):
        """Test creating a feature with valid inputs."""
        from qBRA.models.bra_parameters import BRAParameters
        from qBRA.models.feature_definition import FeatureDefinition
        from qBRA.modules.ils_llz_logic import create_feature
        
        # Create mock layer
        mock_layer = Mock()
        
        # Create parameters
        params = BRAParameters(
            active_layer=mock_layer,
            azimuth=45.0,
            a=1000.0,
            b=500.0,
            h=100.0,
            r=7000.0,
            D=300.0,
            H=150.0,
            L=600.0,
            phi=30.0,
            site_elev=200.0,
            remark="RWY09",
            direction="forward",
            facility_key="LOC",
            facility_label="ILS LLZ",
        )
        
        # Create geometry
        points = [
            QgsPoint(0, 0, 0),
            QgsPoint(1, 0, 0),
            QgsPoint(1, 1, 0),
            QgsPoint(0, 1, 0),
            QgsPoint(0, 0, 0),
        ]
        geometry = QgsGeometry(QgsPolygon(QgsLineString(points)))
        
        # Create definition
        definition = FeatureDefinition(
            id=1,
            area="base",
            max_elev="200.0",
            area_name="Test BRA",
            geometry_points=points,
        )
        
        # Create feature
        feature = create_feature(definition, params, geometry)
        
        # Verify attributes
        attrs = feature.attributes()
        assert attrs[0] == 1  # id
        assert attrs[1] == "base"  # area
        assert attrs[2] == "200.0"  # max_elev
        assert attrs[3] == "Test BRA"  # area_name
        assert attrs[4] == "1000.0"  # a (rounded)
        assert attrs[5] == "500.0"  # b
        assert attrs[6] == "100.0"  # h
        assert attrs[7] == "7000.0"  # r (rounded)
        assert attrs[8] == "300.0"  # D
        assert attrs[9] == "150.0"  # H
        assert attrs[10] == "600.0"  # L
        assert attrs[11] == "30.0"  # phi
        assert attrs[12] == "ILS LLZ"  # type (facility_label)

        # Verify geometry is set
        assert feature.hasGeometry()

    def test_create_feature_uses_facility_label_as_type(self):
        """Test that facility_label is correctly stored as type attribute."""
        from qBRA.models.bra_parameters import BRAParameters
        from qBRA.models.feature_definition import FeatureDefinition
        from qBRA.modules.ils_llz_logic import create_feature

        mock_layer = Mock()

        params = BRAParameters(
            active_layer=mock_layer,
            azimuth=45.0,
            a=1000.0,
            b=500.0,
            h=100.0,
            r=7000.0,
            D=300.0,
            H=150.0,
            L=600.0,
            phi=30.0,
            site_elev=200.0,
            remark="RWY27",
            direction="forward",
            facility_key="LOC",
            facility_label="ILS LLZ – single frequency",
        )

        points = [
            QgsPoint(0, 0, 0),
            QgsPoint(1, 0, 0),
            QgsPoint(1, 1, 0),
            QgsPoint(0, 0, 0),
        ]
        geometry = QgsGeometry(QgsPolygon(QgsLineString(points)))

        definition = FeatureDefinition(
            id=1,
            area="wall",
            max_elev="300.0",
            area_name="Test Wall",
            geometry_points=points,
        )

        feature = create_feature(definition, params, geometry)

        attrs = feature.attributes()
        assert attrs[12] == "ILS LLZ – single frequency"

    def test_create_feature_rounds_a_and_r(self):
        """Test that 'a' and 'r' parameters are rounded to 2 decimal places."""
        from qBRA.models.bra_parameters import BRAParameters
        from qBRA.models.feature_definition import FeatureDefinition
        from qBRA.modules.ils_llz_logic import create_feature
        
        # Create mock layer
        mock_layer = Mock()
        
        # Create parameters with decimal values
        params = BRAParameters(
            active_layer=mock_layer,
            azimuth=45.0,
            a=1234.5678,  # Should round to 1234.57
            b=500.0,
            h=100.0,
            r=7890.1234,  # Should round to 7890.12
            D=300.0,
            H=150.0,
            L=600.0,
            phi=30.0,
            site_elev=200.0,
            remark="RWY09",
            direction="forward",
            facility_key="GP",
            facility_label="ILS GP M-Type",
        )
        
        # Create geometry
        points = [
            QgsPoint(0, 0, 0),
            QgsPoint(1, 0, 0),
            QgsPoint(1, 1, 0),
            QgsPoint(0, 0, 0),
        ]
        geometry = QgsGeometry(QgsPolygon(QgsLineString(points)))
        
        # Create definition
        definition = FeatureDefinition(
            id=3,
            area="slope",
            max_elev="300.0",
            area_name="Test Slope",
            geometry_points=points,
        )
        
        # Create feature
        feature = create_feature(definition, params, geometry)
        
        # Verify rounding
        attrs = feature.attributes()
        assert attrs[4] == "1234.57"  # a rounded
        assert attrs[7] == "7890.12"  # r rounded


class TestBuildLayersOmni:
    """Tests for build_layers_omni() function."""

    def _make_iface(self, srid="EPSG:4326"):
        iface = Mock()
        iface.mapCanvas.return_value.mapSettings.return_value.destinationCrs.return_value.authid.return_value = srid
        return iface

    def _make_layer(self, x=0.0, y=0.0):
        from qgis.core import QgsVectorLayer
        feat = Mock()
        pt = Mock()
        pt.x.return_value = x
        pt.y.return_value = y
        geom = Mock()
        geom.asPoint.return_value = pt
        feat.geometry.return_value = geom
        layer = Mock()
        layer.__class__ = QgsVectorLayer
        layer.selectedFeatures.return_value = [feat]
        return layer

    def test_raises_when_no_selection(self):
        """Raises ValueError when active layer has no selected features."""
        from qBRA.modules.ils_llz_logic import build_layers_omni
        from qgis.core import QgsVectorLayer
        layer = Mock()
        layer.__class__ = QgsVectorLayer
        layer.selectedFeatures.return_value = []
        iface = self._make_iface()
        with pytest.raises(ValueError, match="Select one feature"):
            build_layers_omni(iface, {"active_layer": layer, "omni_r": 300, "omni_alpha": 1.0, "omni_R": 3000})

    def test_raises_invalid_r_R(self):
        """Raises ValueError when r=0 or R=0."""
        from qBRA.modules.ils_llz_logic import build_layers_omni
        layer = self._make_layer()
        iface = self._make_iface()
        with pytest.raises(ValueError, match="r and R must be > 0"):
            build_layers_omni(iface, {"active_layer": layer, "omni_r": 0, "omni_alpha": 1.0, "omni_R": 3000})

    def test_raises_when_R_less_than_r(self):
        """Raises ValueError when R < r."""
        from qBRA.modules.ils_llz_logic import build_layers_omni
        layer = self._make_layer()
        iface = self._make_iface()
        with pytest.raises(ValueError, match="R must be >= r"):
            build_layers_omni(iface, {"active_layer": layer, "omni_r": 500, "omni_alpha": 1.0, "omni_R": 100})

    def test_raises_invalid_alpha(self):
        """Raises ValueError for alpha outside (0, 90]."""
        from qBRA.modules.ils_llz_logic import build_layers_omni
        layer = self._make_layer()
        iface = self._make_iface()
        with pytest.raises(ValueError, match="alpha must be in"):
            build_layers_omni(iface, {"active_layer": layer, "omni_r": 300, "omni_alpha": 0, "omni_R": 3000})

    def test_raises_turbine_invalid_j_h(self):
        """Raises ValueError when turbine=True but j or h is 0."""
        from qBRA.modules.ils_llz_logic import build_layers_omni
        layer = self._make_layer()
        iface = self._make_iface()
        with pytest.raises(ValueError, match="j and h must be > 0"):
            build_layers_omni(iface, {
                "active_layer": layer, "omni_r": 300, "omni_alpha": 1.0, "omni_R": 3000,
                "omni_turbine": True, "omni_j": 0, "omni_h": 50,
            })

    def test_raises_turbine_j_less_than_r(self):
        """Raises ValueError when j < r."""
        from qBRA.modules.ils_llz_logic import build_layers_omni
        layer = self._make_layer()
        iface = self._make_iface()
        with pytest.raises(ValueError, match="j must be >= r"):
            build_layers_omni(iface, {
                "active_layer": layer, "omni_r": 300, "omni_alpha": 1.0, "omni_R": 3000,
                "omni_turbine": True, "omni_j": 100, "omni_h": 50,
            })

    def test_valid_params_no_turbine(self):
        """Returns layer for valid params without turbine."""
        from qBRA.modules.ils_llz_logic import build_layers_omni
        layer = self._make_layer()
        iface = self._make_iface()
        mock_out = Mock()
        with patch("qBRA.modules.ils_llz_logic.QgsVectorLayer", return_value=mock_out):
            result = build_layers_omni(iface, {
                "active_layer": layer, "omni_r": 300, "omni_alpha": 1.0, "omni_R": 3000,
                "omni_turbine": False,
                "display_name": "TEST",
            })
        assert result is mock_out

    def test_valid_params_with_turbine(self):
        """Returns layer for valid params with turbine."""
        from qBRA.modules.ils_llz_logic import build_layers_omni
        layer = self._make_layer()
        iface = self._make_iface()
        mock_out = Mock()
        with patch("qBRA.modules.ils_llz_logic.QgsVectorLayer", return_value=mock_out):
            result = build_layers_omni(iface, {
                "active_layer": layer, "omni_r": 300, "omni_alpha": 1.0, "omni_R": 3000,
                "omni_turbine": True, "omni_j": 500, "omni_h": 52,
                "display_name": "TEST",
            })
        assert result is mock_out

