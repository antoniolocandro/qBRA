"""Tests for ValidationService.

Tests all validation methods with valid and invalid inputs.
"""

import pytest
from unittest.mock import Mock

try:
    from qgis.core import QgsWkbTypes
    QGIS_AVAILABLE = True
except ImportError:
    QGIS_AVAILABLE = False
    # Create mock QgsWkbTypes for type hints
    class QgsWkbTypes:  # type: ignore
        Point = 1
        LineString = 2

try:
    from qBRA.services.validation_service import ValidationService, ValidationError
    VALIDATION_SERVICE_AVAILABLE = True
except ImportError:
    VALIDATION_SERVICE_AVAILABLE = False


@pytest.fixture
def mock_point_layer():
    """Create a mock point layer."""
    layer = Mock()
    layer.wkbType.return_value = QgsWkbTypes.Point
    layer.selectedFeatures.return_value = []
    return layer


@pytest.fixture
def mock_line_layer():
    """Create a mock line layer."""
    layer = Mock()
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
        assert str(error) == "Test message"
