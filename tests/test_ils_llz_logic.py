"""Tests for ILS/LLZ logic functions."""

import pytest
from unittest.mock import Mock

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
