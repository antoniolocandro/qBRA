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
        
        # Assign __class__ so isinstance(layer, QgsVectorLayer) returns True
        from qgis.core import QgsVectorLayer
        mock_layer = Mock()
        mock_layer.__class__ = QgsVectorLayer
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


@pytest.mark.unit
class TestLayerServiceProjectMethods:
    """Tests for LayerService methods that interact with QgsProject."""

    def _make_node(self, layer=None, is_group=False):
        """Helper: create a mock tree node."""
        from qgis.core import QgsLayerTreeNode
        node = Mock()
        # layer_service uses child.NodeLayer / child.NodeGroup (instance attrs)
        node.NodeLayer = QgsLayerTreeNode.NodeLayer   # 0
        node.NodeGroup = QgsLayerTreeNode.NodeGroup   # 1
        node.nodeType.return_value = (
            QgsLayerTreeNode.NodeGroup if is_group else QgsLayerTreeNode.NodeLayer
        )
        if layer is not None:
            node.layer.return_value = layer
        return node

    def _make_vector_layer(self, name: str, wkb_type: int):
        """Helper: create a mock QgsVectorLayer."""
        from qgis.core import QgsVectorLayer
        layer = Mock()
        layer.__class__ = QgsVectorLayer
        layer.name.return_value = name
        layer.wkbType.return_value = wkb_type
        return layer

    def test_get_layers_from_project_empty_tree(self, mock_iface):
        """Returns empty list when project has no layers."""
        from unittest.mock import patch
        with patch("qBRA.services.layer_service.QgsProject") as mock_proj_cls:
            mock_root = Mock()
            mock_root.children.return_value = []
            mock_proj_cls.instance.return_value.layerTreeRoot.return_value = mock_root

            service = LayerService(mock_iface)
            result = service.get_layers_from_project()

        assert result == []

    def test_get_layers_from_project_returns_all_vector_layers(self, mock_iface):
        """Returns all vector layers without geometry filter."""
        from unittest.mock import patch
        from qgis.core import QgsWkbTypes
        point_layer = self._make_vector_layer("PointLayer", QgsWkbTypes.Point)
        line_layer = self._make_vector_layer("LineLayer", QgsWkbTypes.LineString)

        with patch("qBRA.services.layer_service.QgsProject") as mock_proj_cls:
            mock_root = Mock()
            mock_root.children.return_value = [
                self._make_node(point_layer),
                self._make_node(line_layer),
            ]
            mock_proj_cls.instance.return_value.layerTreeRoot.return_value = mock_root

            service = LayerService(mock_iface)
            result = service.get_layers_from_project()

        assert len(result) == 2
        assert ("PointLayer", point_layer) in result
        assert ("LineLayer", line_layer) in result

    def test_get_layers_from_project_skips_non_vector_layers(self, mock_iface):
        """Non-vector layers (raster, etc.) are skipped."""
        from unittest.mock import patch
        # A "raster" layer that is NOT a QgsVectorLayer instance
        raster_layer = Mock()  # __class__ is Mock, not QgsVectorLayer
        raster_layer.name.return_value = "RasterLayer"

        with patch("qBRA.services.layer_service.QgsProject") as mock_proj_cls:
            mock_root = Mock()
            mock_root.children.return_value = [self._make_node(raster_layer)]
            mock_proj_cls.instance.return_value.layerTreeRoot.return_value = mock_root

            service = LayerService(mock_iface)
            result = service.get_layers_from_project()

        assert result == []

    def test_get_layers_from_project_filters_by_point_geometry(self, mock_iface):
        """Returns only point layers when PointGeometry filter is applied."""
        from unittest.mock import patch
        from qgis.core import QgsWkbTypes
        point_layer = self._make_vector_layer("Points", QgsWkbTypes.Point)
        line_layer = self._make_vector_layer("Lines", QgsWkbTypes.LineString)

        with patch("qBRA.services.layer_service.QgsProject") as mock_proj_cls:
            mock_root = Mock()
            mock_root.children.return_value = [
                self._make_node(point_layer),
                self._make_node(line_layer),
            ]
            mock_proj_cls.instance.return_value.layerTreeRoot.return_value = mock_root

            service = LayerService(mock_iface)
            result = service.get_layers_from_project(QgsWkbTypes.PointGeometry)

        assert len(result) == 1
        assert result[0][0] == "Points"

    def test_get_layers_from_project_visits_group_children(self, mock_iface):
        """Layers inside groups are also discovered (recursive traversal)."""
        from unittest.mock import patch
        from qgis.core import QgsWkbTypes
        nested_layer = self._make_vector_layer("Nested", QgsWkbTypes.Point)

        with patch("qBRA.services.layer_service.QgsProject") as mock_proj_cls:
            group_node = self._make_node(is_group=True)
            group_node.children.return_value = [self._make_node(nested_layer)]

            mock_root = Mock()
            mock_root.children.return_value = [group_node]
            mock_proj_cls.instance.return_value.layerTreeRoot.return_value = mock_root

            service = LayerService(mock_iface)
            result = service.get_layers_from_project()

        assert len(result) == 1
        assert result[0][0] == "Nested"

    def test_get_point_layers_delegates_to_get_layers_from_project(self, mock_iface):
        """get_point_layers returns only point-geometry layers."""
        from unittest.mock import patch
        from qgis.core import QgsWkbTypes
        point_layer = self._make_vector_layer("P", QgsWkbTypes.Point)

        with patch("qBRA.services.layer_service.QgsProject") as mock_proj_cls:
            mock_root = Mock()
            mock_root.children.return_value = [self._make_node(point_layer)]
            mock_proj_cls.instance.return_value.layerTreeRoot.return_value = mock_root

            service = LayerService(mock_iface)
            result = service.get_point_layers()

        assert len(result) == 1
        assert result[0][0] == "P"

    def test_get_line_layers_delegates_to_get_layers_from_project(self, mock_iface):
        """get_line_layers returns only line-geometry layers."""
        from unittest.mock import patch
        from qgis.core import QgsWkbTypes
        line_layer = self._make_vector_layer("L", QgsWkbTypes.LineString)

        with patch("qBRA.services.layer_service.QgsProject") as mock_proj_cls:
            mock_root = Mock()
            mock_root.children.return_value = [self._make_node(line_layer)]
            mock_proj_cls.instance.return_value.layerTreeRoot.return_value = mock_root

            service = LayerService(mock_iface)
            result = service.get_line_layers()

        assert len(result) == 1
        assert result[0][0] == "L"

    def test_get_default_point_layer_returns_active_when_point(self, mock_iface):
        """Returns active layer when it is a point layer."""
        from qgis.core import QgsVectorLayer, QgsWkbTypes
        active = Mock()
        active.__class__ = QgsVectorLayer
        active.wkbType.return_value = QgsWkbTypes.Point
        mock_iface.activeLayer.return_value = active

        service = LayerService(mock_iface)
        assert service.get_default_point_layer() is active

    def test_get_default_point_layer_returns_none_when_line_active(self, mock_iface):
        """Returns None when active layer is a line layer, not point."""
        from qgis.core import QgsVectorLayer, QgsWkbTypes
        active = Mock()
        active.__class__ = QgsVectorLayer
        active.wkbType.return_value = QgsWkbTypes.LineString
        mock_iface.activeLayer.return_value = active

        service = LayerService(mock_iface)
        assert service.get_default_point_layer() is None

    def test_find_layer_by_name_found(self, mock_iface):
        """find_layer_by_name returns the matching layer."""
        from unittest.mock import patch
        from qgis.core import QgsWkbTypes
        target = self._make_vector_layer("RunwayPoints", QgsWkbTypes.Point)
        other = self._make_vector_layer("Other", QgsWkbTypes.Point)

        with patch("qBRA.services.layer_service.QgsProject") as mock_proj_cls:
            mock_root = Mock()
            mock_root.children.return_value = [
                self._make_node(target),
                self._make_node(other),
            ]
            mock_proj_cls.instance.return_value.layerTreeRoot.return_value = mock_root

            service = LayerService(mock_iface)
            result = service.find_layer_by_name("RunwayPoints")

        assert result is target

    def test_find_layer_by_name_not_found(self, mock_iface):
        """find_layer_by_name returns None when name not present."""
        from unittest.mock import patch
        from qgis.core import QgsWkbTypes
        layer = self._make_vector_layer("SomeName", QgsWkbTypes.Point)

        with patch("qBRA.services.layer_service.QgsProject") as mock_proj_cls:
            mock_root = Mock()
            mock_root.children.return_value = [self._make_node(layer)]
            mock_proj_cls.instance.return_value.layerTreeRoot.return_value = mock_root

            service = LayerService(mock_iface)
            result = service.find_layer_by_name("Missing")

        assert result is None
