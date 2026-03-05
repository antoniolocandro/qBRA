"""Unit tests for BRAParameters, FacilityConfig, and FacilityDefaults models.

These tests focus exclusively on validation logic inside __post_init__ and on
derived values (display_name, to_dict).  No QGIS geometry needed.
"""

import pytest
from unittest.mock import Mock

from qBRA.models.bra_parameters import BRAParameters, FacilityConfig, FacilityDefaults


# ============================================================================
# Helpers
# ============================================================================

def _valid_defaults(**overrides) -> FacilityDefaults:
    base = dict(b=500, h=70, D=500, H=10, L=2300, phi=30, r_expr="a+6000")
    base.update(overrides)
    return FacilityDefaults(**base)


def _valid_params(mock_layer, **overrides):
    base = dict(
        active_layer=mock_layer,
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
    base.update(overrides)
    return BRAParameters(**base)


# ============================================================================
# FacilityDefaults
# ============================================================================

@pytest.mark.unit
class TestFacilityDefaults:
    """Validation rules for FacilityDefaults dataclass."""

    def test_valid_with_r_expr(self):
        d = _valid_defaults()
        assert d.b == 500
        assert d.phi == 30
        assert d.r_expr == "a+6000"
        assert d.r is None

    def test_valid_with_fixed_r(self):
        d = _valid_defaults(r=6000, r_expr=None)
        assert d.r == 6000
        assert d.r_expr is None

    def test_valid_with_optional_a(self):
        d = _valid_defaults(a=800, r=6000, r_expr=None)
        assert d.a == 800

    def test_both_r_and_r_expr_raises(self):
        with pytest.raises(ValueError, match="Cannot specify both"):
            _valid_defaults(r=6000, r_expr="a+6000")

    def test_zero_b_raises(self):
        with pytest.raises(ValueError, match="b must be positive"):
            _valid_defaults(b=0)

    def test_negative_b_raises(self):
        with pytest.raises(ValueError, match="b must be positive"):
            _valid_defaults(b=-10)

    def test_zero_h_raises(self):
        with pytest.raises(ValueError, match="h must be positive"):
            _valid_defaults(h=0)

    def test_zero_D_raises(self):
        with pytest.raises(ValueError, match="D must be positive"):
            _valid_defaults(D=0)

    def test_zero_H_raises(self):
        with pytest.raises(ValueError, match="H must be positive"):
            _valid_defaults(H=0)

    def test_zero_L_raises(self):
        with pytest.raises(ValueError, match="L must be positive"):
            _valid_defaults(L=0)

    def test_phi_zero_raises(self):
        with pytest.raises(ValueError, match="phi must be between 0 and 180"):
            _valid_defaults(phi=0)

    def test_phi_exceeds_180_raises(self):
        with pytest.raises(ValueError, match="phi must be between 0 and 180"):
            _valid_defaults(phi=181)

    def test_phi_exactly_180_accepted(self):
        d = _valid_defaults(phi=180)
        assert d.phi == 180

    def test_negative_a_raises(self):
        with pytest.raises(ValueError, match="a must be non-negative"):
            _valid_defaults(a=-1, r=6000, r_expr=None)

    def test_zero_a_accepted(self):
        d = _valid_defaults(a=0, r=6000, r_expr=None)
        assert d.a == 0

    def test_negative_r_raises(self):
        with pytest.raises(ValueError, match="r must be positive"):
            _valid_defaults(r=-1, r_expr=None)

    def test_frozen_immutability(self):
        d = _valid_defaults()
        with pytest.raises((AttributeError, TypeError)):
            d.b = 999  # type: ignore


# ============================================================================
# FacilityConfig
# ============================================================================

@pytest.mark.unit
class TestFacilityConfig:
    """Validation rules for FacilityConfig dataclass."""

    def test_valid_a_depends_on_threshold_true(self):
        config = FacilityConfig(
            key="LOC",
            label="ILS LLZ – single frequency",
            a_depends_on_threshold=True,
            defaults=_valid_defaults(),
        )
        assert config.key == "LOC"
        assert config.a_depends_on_threshold is True

    def test_valid_a_depends_on_threshold_false(self):
        config = FacilityConfig(
            key="GP",
            label="ILS GP M-Type",
            a_depends_on_threshold=False,
            defaults=_valid_defaults(a=800, r=6000, r_expr=None),
        )
        assert config.key == "GP"
        assert config.a_depends_on_threshold is False

    def test_empty_key_raises(self):
        with pytest.raises(ValueError, match="key cannot be empty"):
            FacilityConfig(
                key="",
                label="ILS LLZ",
                a_depends_on_threshold=True,
                defaults=_valid_defaults(),
            )

    def test_empty_label_raises(self):
        with pytest.raises(ValueError, match="label cannot be empty"):
            FacilityConfig(
                key="LOC",
                label="",
                a_depends_on_threshold=True,
                defaults=_valid_defaults(),
            )

    def test_a_in_defaults_when_threshold_true_raises(self):
        with pytest.raises(ValueError, match="defaults should not specify 'a'"):
            FacilityConfig(
                key="LOC",
                label="ILS LLZ",
                a_depends_on_threshold=True,
                defaults=_valid_defaults(a=1000, r=6000, r_expr=None),
            )

    def test_no_a_in_defaults_when_threshold_false_raises(self):
        with pytest.raises(ValueError, match="defaults must specify 'a'"):
            FacilityConfig(
                key="GP",
                label="ILS GP",
                a_depends_on_threshold=False,
                defaults=_valid_defaults(),  # no 'a' in defaults
            )

    def test_frozen_immutability(self):
        config = FacilityConfig(
            key="LOC",
            label="ILS LLZ",
            a_depends_on_threshold=True,
            defaults=_valid_defaults(),
        )
        with pytest.raises((AttributeError, TypeError)):
            config.key = "NEW"  # type: ignore


# ============================================================================
# BRAParameters
# ============================================================================

@pytest.mark.unit
class TestBRAParameters:
    """Validation rules and derived values for BRAParameters dataclass."""

    def test_valid_parameters(self, mock_qgs_vector_layer):
        params = _valid_params(mock_qgs_vector_layer)
        assert params.azimuth == 90.0
        assert params.a == 1000.0
        assert params.direction == "forward"

    def test_display_name_computed_when_absent(self, mock_qgs_vector_layer):
        params = _valid_params(mock_qgs_vector_layer)
        assert params.display_name == "RWY09 - ILS LLZ – single frequency"

    def test_display_name_explicit(self, mock_qgs_vector_layer):
        params = _valid_params(mock_qgs_vector_layer, display_name="Custom Name")
        assert params.display_name == "Custom Name"

    def test_azimuth_zero_accepted(self, mock_qgs_vector_layer):
        params = _valid_params(mock_qgs_vector_layer, azimuth=0.0)
        assert params.azimuth == 0.0

    def test_azimuth_negative_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="azimuth"):
            _valid_params(mock_qgs_vector_layer, azimuth=-1.0)

    def test_azimuth_360_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="azimuth"):
            _valid_params(mock_qgs_vector_layer, azimuth=360.0)

    def test_azimuth_359_accepted(self, mock_qgs_vector_layer):
        params = _valid_params(mock_qgs_vector_layer, azimuth=359.9)
        assert params.azimuth == 359.9

    def test_a_zero_accepted(self, mock_qgs_vector_layer):
        params = _valid_params(mock_qgs_vector_layer, a=0.0)
        assert params.a == 0.0

    def test_a_negative_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="a must be non-negative"):
            _valid_params(mock_qgs_vector_layer, a=-1.0)

    def test_b_zero_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="b must be positive"):
            _valid_params(mock_qgs_vector_layer, b=0.0)

    def test_h_zero_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="h must be positive"):
            _valid_params(mock_qgs_vector_layer, h=0.0)

    def test_r_zero_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="r must be positive"):
            _valid_params(mock_qgs_vector_layer, r=0.0)

    def test_D_zero_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="D must be positive"):
            _valid_params(mock_qgs_vector_layer, D=0.0)

    def test_H_zero_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="H must be positive"):
            _valid_params(mock_qgs_vector_layer, H=0.0)

    def test_L_zero_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="L must be positive"):
            _valid_params(mock_qgs_vector_layer, L=0.0)

    def test_phi_zero_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="phi must be between 0 and 180"):
            _valid_params(mock_qgs_vector_layer, phi=0.0)

    def test_phi_180_accepted(self, mock_qgs_vector_layer):
        params = _valid_params(mock_qgs_vector_layer, phi=180.0)
        assert params.phi == 180.0

    def test_phi_exceeds_180_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="phi must be between 0 and 180"):
            _valid_params(mock_qgs_vector_layer, phi=181.0)

    def test_invalid_direction_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="direction must be"):
            _valid_params(mock_qgs_vector_layer, direction="sideways")

    def test_direction_backward_accepted(self, mock_qgs_vector_layer):
        params = _valid_params(mock_qgs_vector_layer, direction="backward")
        assert params.direction == "backward"

    def test_empty_remark_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="remark cannot be empty"):
            _valid_params(mock_qgs_vector_layer, remark="")

    def test_empty_facility_key_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="facility_key cannot be empty"):
            _valid_params(mock_qgs_vector_layer, facility_key="")

    def test_empty_facility_label_raises(self, mock_qgs_vector_layer):
        with pytest.raises(ValueError, match="facility_label cannot be empty"):
            _valid_params(mock_qgs_vector_layer, facility_label="")

    def test_to_dict_includes_all_fields(self, mock_qgs_vector_layer):
        params = _valid_params(mock_qgs_vector_layer)
        d = params.to_dict()
        assert d["azimuth"] == 90.0
        assert d["a"] == 1000.0
        assert d["direction"] == "forward"
        assert d["facility_key"] == "LOC"
        assert d["active_layer"] is mock_qgs_vector_layer

    def test_to_dict_preserves_display_name(self, mock_qgs_vector_layer):
        params = _valid_params(mock_qgs_vector_layer, display_name="My Area")
        d = params.to_dict()
        assert d["display_name"] == "My Area"

    @pytest.mark.parametrize("direction", ["forward", "backward"])
    def test_valid_directions(self, mock_qgs_vector_layer, direction):
        params = _valid_params(mock_qgs_vector_layer, direction=direction)
        assert params.direction == direction

    @pytest.mark.parametrize("azimuth", [0.0, 90.0, 180.0, 270.0, 359.9])
    def test_valid_azimuth_values(self, mock_qgs_vector_layer, azimuth):
        params = _valid_params(mock_qgs_vector_layer, azimuth=azimuth)
        assert params.azimuth == azimuth
