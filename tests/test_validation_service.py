"""Tests for ValidationService.

Tests all validation methods with valid and invalid inputs.
"""

import pytest
from unittest.mock import Mock

from qgis.core import QgsWkbTypes, QgsVectorLayer
from qBRA.services.validation_service import ValidationService, ValidationError

VALIDATION_SERVICE_AVAILABLE = True


@pytest.fixture
def mock_point_layer():
    """Create a mock point layer that passes isinstance(layer, QgsVectorLayer)."""
    layer = Mock()
    layer.__class__ = QgsVectorLayer
    layer.wkbType.return_value = QgsWkbTypes.Point
    layer.selectedFeatures.return_value = []
    return layer


@pytest.fixture
def mock_line_layer():
    """Create a mock line layer that passes isinstance(layer, QgsVectorLayer)."""
    layer = Mock()
    layer.__class__ = QgsVectorLayer
    layer.wkbType.return_value = QgsWkbTypes.LineString
    layer.selectedFeatures.return_value = []
    return layer


@pytest.mark.unit
class TestValidationService:
    """Test suite for ValidationService."""
    
    def test_validate_layer_selected_with_none(self):
        """Test that validate_layer_selected raises error for None."""
        if not VALIDATION_SERVICE_AVAILABLE:
            pytest.skip("ValidationService not available")
        
        with pytest.raises(ValidationError) as exc_info:
            ValidationService.validate_layer_selected(None, "navaid layer")
        
        assert "No navaid layer selected" in str(exc_info.value)
        assert exc_info.value.field == "navaid layer"
    
    def test_validate_layer_selected_with_layer(self, mock_point_layer):
        """Test that validate_layer_selected passes with valid layer."""
        if not VALIDATION_SERVICE_AVAILABLE:
            pytest.skip("ValidationService not available")
        
        # Should not raise
        ValidationService.validate_layer_selected(mock_point_layer, "test layer")
    
    def test_validate_positive_number_with_zero(self):
        """Test that validate_positive_number rejects zero with exclusive=True."""
        if not VALIDATION_SERVICE_AVAILABLE:
            pytest.skip("ValidationService not available")
        
        with pytest.raises(ValidationError) as exc_info:
            ValidationService.validate_positive_number(0.0, "distance", exclusive=True)
        
        assert "distance must be greater than 0" in str(exc_info.value)
    
    def test_validate_positive_number_with_negative(self):
        """Test that validate_positive_number rejects negative."""
        if not VALIDATION_SERVICE_AVAILABLE:
            pytest.skip("ValidationService not available")
        
        with pytest.raises(ValidationError) as exc_info:
            ValidationService.validate_positive_number(-10.0, "height")
        
        assert "height must be greater than 0" in str(exc_info.value)
    
    def test_validate_positive_number_with_positive(self):
        """Test that validate_positive_number accepts positive value."""
        if not VALIDATION_SERVICE_AVAILABLE:
            pytest.skip("ValidationService not available")
        
        # Should not raise
        ValidationService.validate_positive_number(100.0, "distance")
    
    def test_validate_angle_range_within_range(self):
        """Test that validate_angle_range accepts value in range."""
        if not VALIDATION_SERVICE_AVAILABLE:
            pytest.skip("ValidationService not available")
        
        # Should not raise
        ValidationService.validate_angle_range(180.0, "azimuth", 0.0, 360.0)
    
    def test_validate_angle_range_out_of_range(self):
        """Test that validate_angle_range rejects value out of range."""
        if not VALIDATION_SERVICE_AVAILABLE:
            pytest.skip("ValidationService not available")
        
        with pytest.raises(ValidationError) as exc_info:
            ValidationService.validate_angle_range(450.0, "azimuth", 0.0, 360.0)
        
        assert "azimuth must be in range" in str(exc_info.value)
        assert "450.0" in str(exc_info.value)
    
    def test_validate_direction_valid_forward(self):
        """Test that validate_direction accepts 'forward'."""
        if not VALIDATION_SERVICE_AVAILABLE:
            pytest.skip("ValidationService not available")
        
        # Should not raise
        ValidationService.validate_direction("forward")
    
    def test_validate_direction_valid_backward(self):
        """Test that validate_direction accepts 'backward'."""
        if not VALIDATION_SERVICE_AVAILABLE:
            pytest.skip("ValidationService not available")
        
        # Should not raise
        ValidationService.validate_direction("backward")
    
    def test_validate_direction_invalid(self):
        """Test that validate_direction rejects invalid direction."""
        if not VALIDATION_SERVICE_AVAILABLE:
            pytest.skip("ValidationService not available")
        
        with pytest.raises(ValidationError) as exc_info:
            ValidationService.validate_direction("sideways")
        
        assert "direction must be one of" in str(exc_info.value)
        assert "sideways" in str(exc_info.value)
    
    def test_validate_non_empty_string_with_empty(self):
        """Test that validate_non_empty_string rejects empty string."""
        if not VALIDATION_SERVICE_AVAILABLE:
            pytest.skip("ValidationService not available")
        
        with pytest.raises(ValidationError) as exc_info:
            ValidationService.validate_non_empty_string("", "remark")
        
        assert "remark cannot be empty" in str(exc_info.value)
    
    def test_validate_non_empty_string_with_whitespace(self):
        """Test that validate_non_empty_string rejects whitespace-only string."""
        if not VALIDATION_SERVICE_AVAILABLE:
            pytest.skip("ValidationService not available")
        
        with pytest.raises(ValidationError) as exc_info:
            ValidationService.validate_non_empty_string("   ", "facility_key")
        
        assert "facility_key cannot be empty" in str(exc_info.value)
    
    def test_validate_non_empty_string_with_valid(self):
        """Test that validate_non_empty_string accepts non-empty string."""
        if not VALIDATION_SERVICE_AVAILABLE:
            pytest.skip("ValidationService not available")
        
        # Should not raise
        ValidationService.validate_non_empty_string("RWY09", "remark")

    def test_validation_error_has_field_attribute(self):
        """Test that ValidationError stores field name."""
        if not VALIDATION_SERVICE_AVAILABLE:
            pytest.skip("ValidationService not available")

        error = ValidationError("Test message", field="test_field")
        assert error.field == "test_field"
        assert error.message == "Test message"
        assert "Test message" in str(error)


@pytest.mark.unit
class TestValidationServiceLayerMethods:
    """Tests for ValidationService methods that depend on QGIS layer types."""

    def test_validate_layer_type_correct_point(self, mock_point_layer):
        """Passing a point layer for point type should not raise."""
        ValidationService.validate_layer_type(
            mock_point_layer, QgsWkbTypes.PointGeometry, "navaid"
        )

    def test_validate_layer_type_wrong_type_raises(self, mock_line_layer):
        """Passing a line layer where point expected should raise."""
        with pytest.raises(ValidationError, match="navaid must be point"):
            ValidationService.validate_layer_type(
                mock_line_layer, QgsWkbTypes.PointGeometry, "navaid"
            )

    def test_validate_layer_type_not_vector_raises(self):
        """Non-QgsVectorLayer object should raise ValidationError."""
        plain_mock = Mock()  # not __class__ = QgsVectorLayer
        with pytest.raises(ValidationError, match="not a vector layer"):
            ValidationService.validate_layer_type(
                plain_mock, QgsWkbTypes.PointGeometry, "navaid"
            )

    def test_validate_feature_selected_no_features_raises(self, mock_point_layer):
        """Layer with no selected features should raise."""
        mock_point_layer.selectedFeatures.return_value = []
        with pytest.raises(ValidationError, match="No feature selected"):
            ValidationService.validate_feature_selected(mock_point_layer, "navaid")

    def test_validate_feature_selected_with_feature_passes(self, mock_point_layer):
        """Layer with at least one selected feature should pass."""
        mock_point_layer.selectedFeatures.return_value = [Mock()]
        ValidationService.validate_feature_selected(mock_point_layer, "navaid")

    def test_validate_geometry_vertices_sufficient(self, mock_point_layer):
        """Layer feature with enough vertices should pass."""
        mock_geom = Mock()
        mock_geom.isMultipart.return_value = False
        mock_geom.type.return_value = QgsWkbTypes.LineGeometry
        mock_geom.asPolyline.return_value = [Mock(), Mock(), Mock()]

        mock_feature = Mock()
        mock_feature.geometry.return_value = mock_geom
        mock_point_layer.selectedFeatures.return_value = [mock_feature]

        ValidationService.validate_geometry_vertices(mock_point_layer, min_vertices=2)

    def test_validate_geometry_vertices_insufficient_raises(self, mock_point_layer):
        """Layer feature with fewer vertices than required should raise."""
        mock_geom = Mock()
        mock_geom.isMultipart.return_value = False
        mock_geom.type.return_value = QgsWkbTypes.LineGeometry
        mock_geom.asPolyline.return_value = [Mock()]  # only 1 vertex

        mock_feature = Mock()
        mock_feature.geometry.return_value = mock_geom
        mock_point_layer.selectedFeatures.return_value = [mock_feature]

        with pytest.raises(ValidationError, match="at least 2 vertices"):
            ValidationService.validate_geometry_vertices(mock_point_layer, min_vertices=2)

