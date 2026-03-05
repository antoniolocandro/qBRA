"""Tests for feature definition models."""

import pytest
from unittest.mock import Mock

# FeatureDefinition uses QgsPoint = Any (via TYPE_CHECKING), so any object
# can serve as a geometry point — no real QGIS needed.
from qBRA.models.feature_definition import FeatureDefinition


def _make_points(n: int = 4):
    """Create n generic point mocks."""
    return [Mock() for _ in range(n)]


@pytest.mark.unit
class TestFeatureDefinition:
    """Test FeatureDefinition dataclass."""

    def test_valid_definition(self):
        """Test creating a valid feature definition."""
        points = _make_points(4)
        definition = FeatureDefinition(
            id=1,
            area="base",
            max_elev="100.0",
            area_name="Test Area",
            geometry_points=points,
        )

        assert definition.id == 1
        assert definition.area == "base"
        assert definition.max_elev == "100.0"
        assert definition.area_name == "Test Area"
        assert len(definition.geometry_points) == 4

    def test_invalid_id(self):
        """Test that invalid id raises ValueError."""
        points = _make_points(4)
        with pytest.raises(ValueError, match="Feature id must be positive"):
            FeatureDefinition(
                id=0,
                area="base",
                max_elev="100.0",
                area_name="Test",
                geometry_points=points,
            )

    def test_empty_area(self):
        """Test that empty area raises ValueError."""
        points = _make_points(4)
        with pytest.raises(ValueError, match="Feature area cannot be empty"):
            FeatureDefinition(
                id=1,
                area="",
                max_elev="100.0",
                area_name="Test",
                geometry_points=points,
            )

    def test_empty_area_name(self):
        """Test that empty area_name raises ValueError."""
        points = _make_points(4)
        with pytest.raises(ValueError, match="Feature area_name cannot be empty"):
            FeatureDefinition(
                id=1,
                area="base",
                max_elev="100.0",
                area_name="",
                geometry_points=points,
            )

    def test_insufficient_points(self):
        """Test that less than 3 points raises ValueError."""
        points = _make_points(2)
        with pytest.raises(ValueError, match="Feature geometry must have at least 3 points"):
            FeatureDefinition(
                id=1,
                area="base",
                max_elev="100.0",
                area_name="Test",
                geometry_points=points,
            )

    def test_frozen_dataclass(self):
        """Test that FeatureDefinition is frozen (immutable)."""
        points = _make_points(4)
        definition = FeatureDefinition(
            id=1,
            area="base",
            max_elev="100.0",
            area_name="Test",
            geometry_points=points,
        )

        with pytest.raises(AttributeError):
            definition.id = 2  # type: ignore

    def test_area_types(self):
        """Test different valid area types."""
        points = _make_points(4)
        area_types = ["base", "left level", "right level", "slope", "wall"]

        for area_type in area_types:
            definition = FeatureDefinition(
                id=1,
                area=area_type,
                max_elev="100.0",
                area_name="Test",
                geometry_points=points,
            )
            assert definition.area == area_type
