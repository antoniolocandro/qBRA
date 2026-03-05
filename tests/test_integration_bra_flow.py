"""Integration tests for BRA calculation flow.

These tests verify that the validation → model → create_feature pipeline
works end-to-end using QGIS stubs (no real QGIS installation needed).

Integration scope:
  ValidationService → BRAParameters → create_feature()
"""

import pytest
from unittest.mock import Mock, patch

from qgis.core import QgsVectorLayer, QgsWkbTypes

from qBRA.services.validation_service import ValidationService, ValidationError
from qBRA.models.bra_parameters import BRAParameters, FacilityConfig, FacilityDefaults
from qBRA.models.feature_definition import FeatureDefinition
from qBRA.modules.ils_llz_logic import create_feature
from qBRA.exceptions import BRACalculationError


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def point_layer_with_feature():
    """A mock point layer with one selected feature."""
    layer = Mock()
    layer.__class__ = QgsVectorLayer
    layer.wkbType.return_value = QgsWkbTypes.Point

    mock_point = Mock()
    mock_point.x.return_value = 10.0
    mock_point.y.return_value = 20.0

    mock_geom = Mock()
    mock_geom.asPoint.return_value = mock_point

    mock_feature = Mock()
    mock_feature.geometry.return_value = mock_geom

    layer.selectedFeatures.return_value = [mock_feature]
    return layer


@pytest.fixture
def point_layer_empty():
    """A mock point layer with NO selected features."""
    layer = Mock()
    layer.__class__ = QgsVectorLayer
    layer.wkbType.return_value = QgsWkbTypes.Point
    layer.selectedFeatures.return_value = []
    return layer


@pytest.fixture
def valid_params(point_layer_with_feature):
    return BRAParameters(
        active_layer=point_layer_with_feature,
        azimuth=90.0,
        a=1000.0,
        b=500.0,
        h=70.0,
        r=7000.0,
        D=500.0,
        H=10.0,
        L=2300.0,
        phi=30.0,
        site_elev=100.0,
        remark="RWY09",
        direction="forward",
        facility_key="LOC",
        facility_label="ILS LLZ – single frequency",
    )


@pytest.fixture
def geometry_points():
    return [Mock() for _ in range(5)]


# ============================================================================
# Integration: Validation → Model creation
# ============================================================================

@pytest.mark.integration
class TestValidationToModelFlow:
    """Verify that validation guards BRAParameters creation correctly."""

    def test_passes_when_layer_selected(self, point_layer_with_feature):
        """Full validation chain succeeds when conditions are met."""
        ValidationService.validate_layer_selected(point_layer_with_feature)
        ValidationService.validate_layer_type(
            point_layer_with_feature, QgsWkbTypes.PointGeometry
        )
        ValidationService.validate_feature_selected(point_layer_with_feature)

        params = BRAParameters(
            active_layer=point_layer_with_feature,
            azimuth=45.0,
            a=800.0,
            b=50.0,
            h=70.0,
            r=6800.0,
            D=250.0,
            H=5.0,
            L=325.0,
            phi=10.0,
            site_elev=50.0,
            remark="RWY27",
            direction="backward",
            facility_key="GP",
            facility_label="ILS GP M-Type",
        )
        assert params.remark == "RWY27"

    def test_validate_layer_selected_blocks_none(self):
        """validate_layer_selected raises when layer is None."""
        with pytest.raises(ValidationError, match="No navaid layer selected"):
            ValidationService.validate_layer_selected(None, "navaid layer")

    def test_validate_feature_selected_blocks_empty_layer(self, point_layer_empty):
        """validate_feature_selected raises when no features selected."""
        with pytest.raises(ValidationError, match="No feature selected"):
            ValidationService.validate_feature_selected(point_layer_empty)

    def test_bra_parameters_invalid_azimuth_surfaces_to_caller(self, point_layer_with_feature):
        """ValueError from BRAParameters propagates naturally to caller."""
        with pytest.raises(ValueError, match="azimuth"):
            BRAParameters(
                active_layer=point_layer_with_feature,
                azimuth=400.0,  # Invalid
                a=1000.0, b=500.0, h=70.0, r=7000.0,
                D=500.0, H=10.0, L=2300.0, phi=30.0, site_elev=100.0,
                remark="RWY09", direction="forward",
                facility_key="LOC", facility_label="ILS LLZ",
            )

    def test_bra_parameters_invalid_direction_surfaces_to_caller(self, point_layer_with_feature):
        """ValueError from BRAParameters propagates for bad direction."""
        with pytest.raises(ValueError, match="direction"):
            BRAParameters(
                active_layer=point_layer_with_feature,
                azimuth=90.0, a=1000.0, b=500.0, h=70.0, r=7000.0,
                D=500.0, H=10.0, L=2300.0, phi=30.0, site_elev=100.0,
                remark="RWY09", direction="sideways",
                facility_key="LOC", facility_label="ILS LLZ",
            )


# ============================================================================
# Integration: Model → create_feature()
# ============================================================================

@pytest.mark.integration
class TestModelToCreateFeature:
    """Verify create_feature produces correct attributes from BRAParameters."""

    def test_attributes_match_params(self, valid_params, geometry_points):
        geom = Mock()
        defn = FeatureDefinition(
            id=1, area="base", max_elev="110.0",
            area_name="Base BRA", geometry_points=geometry_points,
        )
        feature = create_feature(defn, valid_params, geom)
        attrs = feature.attributes()

        assert attrs[0] == 1            # id
        assert attrs[1] == "base"       # area
        assert attrs[2] == "110.0"      # max_elev
        assert attrs[3] == "Base BRA"   # area_name
        assert attrs[4] == "1000.0"     # a
        assert attrs[5] == "500.0"      # b
        assert attrs[12] == "ILS LLZ – single frequency"  # type

    def test_geometry_stored_on_feature(self, valid_params, geometry_points):
        geom = Mock()
        defn = FeatureDefinition(
            id=2, area="slope", max_elev="120.0",
            area_name="Slope BRA", geometry_points=geometry_points,
        )
        feature = create_feature(defn, valid_params, geom)
        assert feature.hasGeometry()

    def test_a_and_r_rounded_to_2_decimals(self, point_layer_with_feature, geometry_points):
        params = BRAParameters(
            active_layer=point_layer_with_feature,
            azimuth=90.0,
            a=1234.5678,
            b=500.0, h=70.0,
            r=9876.5432,
            D=500.0, H=10.0, L=2300.0, phi=30.0, site_elev=100.0,
            remark="RWY09", direction="forward",
            facility_key="LOC", facility_label="ILS LLZ",
        )
        geom = Mock()
        defn = FeatureDefinition(
            id=1, area="base", max_elev="110.0",
            area_name="Base BRA", geometry_points=geometry_points,
        )
        feature = create_feature(defn, params, geom)
        attrs = feature.attributes()
        assert attrs[4] == "1234.57"   # a rounded
        assert attrs[7] == "9876.54"   # r rounded

    def test_multiple_features_share_same_params(self, valid_params, geometry_points):
        """All features created from the same params share identical attribute values."""
        geom1, geom2 = Mock(), Mock()
        defn1 = FeatureDefinition(
            id=1, area="base", max_elev="100.0",
            area_name="Base", geometry_points=geometry_points,
        )
        defn2 = FeatureDefinition(
            id=2, area="slope", max_elev="150.0",
            area_name="Slope", geometry_points=geometry_points,
        )
        f1 = create_feature(defn1, valid_params, geom1)
        f2 = create_feature(defn2, valid_params, geom2)

        # Shared params (a, b, h, r, ...) must be identical on both features
        for i in range(4, 13):
            assert f1.attributes()[i] == f2.attributes()[i]


# ============================================================================
# Integration: FacilityConfig → BRAParameters
# ============================================================================

@pytest.mark.integration
class TestFacilityConfigToParams:
    """Verify FacilityConfig defaults compose correctly into BRAParameters."""

    def test_loc_config_defaults_applied(self, point_layer_with_feature):
        """LOC facility defaults match what ILS LLZ expects."""
        config = FacilityConfig(
            key="LOC",
            label="ILS LLZ – single frequency",
            a_depends_on_threshold=True,
            defaults=FacilityDefaults(
                b=500, h=70, D=500, H=10, L=2300, phi=30, r_expr="a+6000"
            ),
        )
        d = config.defaults
        params = BRAParameters(
            active_layer=point_layer_with_feature,
            azimuth=90.0,
            a=1000.0,
            b=d.b,
            h=d.h,
            r=7000.0,  # a + 6000
            D=d.D,
            H=d.H,
            L=d.L,
            phi=d.phi,
            site_elev=100.0,
            remark="RWY09",
            direction="forward",
            facility_key=config.key,
            facility_label=config.label,
        )
        assert params.b == 500
        assert params.phi == 30
        assert params.facility_key == "LOC"

    def test_gp_config_has_fixed_a(self):
        """GP facility has a fixed 'a' value (does not depend on threshold)."""
        config = FacilityConfig(
            key="GP",
            label="ILS GP M-Type",
            a_depends_on_threshold=False,
            defaults=FacilityDefaults(
                a=800, b=50, h=70, D=250, H=5, L=325, phi=10, r=6000
            ),
        )
        assert config.defaults.a == 800
        assert config.a_depends_on_threshold is False

    @pytest.mark.parametrize("key,label,a_dep,a,r_expr,r", [
        ("LOC",   "ILS LLZ – single frequency", True,  None, "a+6000", None),
        ("LOCII", "ILS LLZ – dual frequency",   True,  None, "a+6000", None),
        ("GP",    "ILS GP M-Type",               False, 800,  None,     6000),
        ("DME",   "DME (directional)",           True,  None, "a+6000", None),
    ])
    def test_all_facility_configs_valid(self, key, label, a_dep, a, r_expr, r):
        """Smoke-test that all four standard facility configs can be created."""
        kwargs = dict(b=200, h=70, D=300, H=10, L=1000, phi=20)
        if a is not None:
            kwargs["a"] = a
        if r is not None:
            kwargs["r"] = r
        if r_expr is not None:
            kwargs["r_expr"] = r_expr

        config = FacilityConfig(
            key=key, label=label,
            a_depends_on_threshold=a_dep,
            defaults=FacilityDefaults(**kwargs),
        )
        assert config.key == key
