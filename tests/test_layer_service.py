"""Tests for LayerService.

Tests layer discovery and filtering functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock

try:
    from qgis.core import QgsWkbTypes
    QGIS_AVAILABLE = True
except ImportError:
    QGIS_AVAILABLE = False
    # Create mock QgsWkbTypes for type hints
    class QgsWkbTypes:  # type: ignore
        Point = 1
        LineString = 2
        PointGeometry = 0
        LineGeometry = 1

try:
    from qBRA.services.layer_service import LayerService
    LAYER_SERVICE_AVAILABLE = True
except ImportError:
    LAYER_SERVICE_AVAILABLE = False


@pytest.fixture
def mock_iface():
    """Create a mock QGIS interface."""
    iface = Mock()
    iface.activeLayer.return_value = None
    return iface


@pytest.fixture
def layer_service(mock_iface):
    """Create a LayerService instance with mock iface."""
    if not LAYER_SERVICE_AVAILABLE:
        pytest.skip("LayerService not available")
    return LayerService(mock_iface)


@pytest.mark.unit
class TestLayerService:
    """Test suite for LayerService."""
    
    def test_initialization(self, mock_iface):
        """Test that LayerService initializes with iface."""
        if not LAYER_SERVICE_AVAILABLE:
            pytest.skip("LayerService not available")
        
        service = LayerService(mock_iface)
        assert service.iface is mock_iface
    
    def test_get_active_layer_with_vector_layer(self, layer_service, mock_iface):
        """Test get_active_layer returns vector layer."""
        if not LAYER_SERVICE_AVAILABLE:
            pytest.skip("LayerService not available")
        
        # Mock a vector layer
        mock_layer = Mock()
        mock_layer.__class__.__name__ = "QgsVectorLayer"
        mock_iface.activeLayer.return_value = mock_layer
        
        result = layer_service.get_active_layer()
        assert result is mock_layer
    
    def test_get_active_layer_with_no_active(self, layer_service, mock_iface):
        """Test get_active_layer returns None when no active layer."""
        if not LAYER_SERVICE_AVAILABLE:
            pytest.skip("LayerService not available")
        
        mock_iface.activeLayer.return_value = None
        
        result = layer_service.get_active_layer()
        assert result is None
    
    def test_get_layer_field_names(self, layer_service):
        """Test get_layer_field_names returns field names."""
        if not LAYER_SERVICE_AVAILABLE:
            pytest.skip("LayerService not available")
        
        # Mock layer with fields
        mock_layer = Mock()
        mock_field1 = Mock()
        mock_field1.name.return_value = "id"
        mock_field2 = Mock()
        mock_field2.name.return_value = "name"
        mock_field3 = Mock()
        mock_field3.name.return_value = "runway"
        
        mock_layer.fields.return_value = [mock_field1, mock_field2, mock_field3]
        
        result = layer_service.get_layer_field_names(mock_layer)
        assert result == ["id", "name", "runway"]
    
    def test_find_field_index_with_match(self, layer_service):
        """Test find_field_index returns index of first match."""
        if not LAYER_SERVICE_AVAILABLE:
            pytest.skip("LayerService not available")
        
        # Mock layer fields
        mock_layer = Mock()
        mock_fields = Mock()
        mock_fields.indexFromName = Mock(side_effect=lambda name: {
            "runway": 0,
            "rwy": 1,
            "thr_rwy": 2,
        }.get(name, -1))
        mock_layer.fields.return_value = mock_fields
        
        result = layer_service.find_field_index(mock_layer, ["runway", "rwy", "thr_rwy"])
        assert result == 0  # First match
    
    def test_find_field_index_with_second_match(self, layer_service):
        """Test find_field_index returns second candidate if first not found."""
        if not LAYER_SERVICE_AVAILABLE:
            pytest.skip("LayerService not available")
        
        # Mock layer fields (runway doesn't exist, but rwy does)
        mock_layer = Mock()
        mock_fields = Mock()
        mock_fields.indexFromName = Mock(side_effect=lambda name: {
            "rwy": 1,
            "thr_rwy": 2,
        }.get(name, -1))
        mock_layer.fields.return_value = mock_fields
        
        result = layer_service.find_field_index(mock_layer, ["runway", "rwy", "thr_rwy"])
        assert result == 1  # Second candidate found
    
    def test_find_field_index_with_no_match(self, layer_service):
        """Test find_field_index returns -1 when no match."""
        if not LAYER_SERVICE_AVAILABLE:
            pytest.skip("LayerService not available")
        
        # Mock layer fields with no matches
        mock_layer = Mock()
        mock_fields = Mock()
        mock_fields.indexFromName = Mock(return_value=-1)
        mock_layer.fields.return_value = mock_fields
        
        result = layer_service.find_field_index(mock_layer, ["runway", "rwy", "thr_rwy"])
        assert result == -1  # No match found
