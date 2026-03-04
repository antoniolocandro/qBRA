"""Layer service for qBRA plugin.

Provides layer management operations for QGIS layers.
Handles layer discovery, filtering, and default selection logic.
"""

from typing import Any, List, Tuple, Optional
from qgis.core import QgsProject, QgsVectorLayer, QgsWkbTypes, QgsLayerTreeNode


class LayerService:
    """Service for QGIS layer operations.
    
    This service handles layer discovery and filtering from the QGIS project.
    It depends on QGIS iface for accessing the active layer.
    """
    
    def __init__(self, iface: Any) -> None:
        """Initialize layer service.
        
        Args:
            iface: QGIS interface object
        """
        self.iface = iface
    
    def get_layers_from_project(
        self, 
        geometry_type: Optional[QgsWkbTypes.GeometryType] = None
    ) -> List[Tuple[str, QgsVectorLayer]]:
        """Get all vector layers from the project, optionally filtered by geometry type.
        
        This method traverses the layer tree including layers inside groups.
        
        Args:
            geometry_type: Optional geometry type to filter by (e.g., QgsWkbTypes.PointGeometry)
            
        Returns:
            List of tuples (layer_name, layer_object)
        """
        layers: List[Tuple[str, QgsVectorLayer]] = []
        root = QgsProject.instance().layerTreeRoot()
        
        def visit(node: QgsLayerTreeNode) -> None:
            """Recursively visit layer tree nodes."""
            for child in node.children():
                if child.nodeType() == child.NodeLayer:
                    layer = child.layer()
                    if not isinstance(layer, QgsVectorLayer):
                        continue
                    
                    # Filter by geometry type if specified
                    if geometry_type is not None:
                        layer_geom_type = QgsWkbTypes.geometryType(layer.wkbType())
                        if layer_geom_type != geometry_type:
                            continue
                    
                    layers.append((layer.name(), layer))
                    
                elif child.nodeType() == child.NodeGroup:
                    # Recursively visit group children
                    visit(child)
        
        visit(root)
        return layers
    
    def get_point_layers(self) -> List[Tuple[str, QgsVectorLayer]]:
        """Get all point layers from the project.
        
        Returns:
            List of tuples (layer_name, layer_object) for point layers
        """
        return self.get_layers_from_project(QgsWkbTypes.PointGeometry)
    
    def get_line_layers(self) -> List[Tuple[str, QgsVectorLayer]]:
        """Get all line layers from the project.
        
        Returns:
            List of tuples (layer_name, layer_object) for line layers
        """
        return self.get_layers_from_project(QgsWkbTypes.LineGeometry)
    
    def get_polygon_layers(self) -> List[Tuple[str, QgsVectorLayer]]:
        """Get all polygon layers from the project.
        
        Returns:
            List of tuples (layer_name, layer_object) for polygon layers
        """
        return self.get_layers_from_project(QgsWkbTypes.PolygonGeometry)
    
    def get_active_layer(self) -> Optional[QgsVectorLayer]:
        """Get the currently active layer in QGIS.
        
        Returns:
            Active vector layer, or None if no layer is active or active layer is not a vector layer
        """
        active = self.iface.activeLayer()
        if active and isinstance(active, QgsVectorLayer):
            return active
        return None
    
    def get_default_point_layer(self) -> Optional[QgsVectorLayer]:
        """Get the default point layer (active layer if it's a point layer).
        
        Returns:
            Active point layer, or None if active layer is not a point layer
        """
        active = self.get_active_layer()
        if active:
            geom_type = QgsWkbTypes.geometryType(active.wkbType())
            if geom_type == QgsWkbTypes.PointGeometry:
                return active
        return None
    
    def find_layer_by_name(
        self,
        name: str,
        geometry_type: Optional[QgsWkbTypes.GeometryType] = None
    ) -> Optional[QgsVectorLayer]:
        """Find a layer by name, optionally filtered by geometry type.
        
        Args:
            name: Layer name to search for
            geometry_type: Optional geometry type to filter by
            
        Returns:
            First matching layer, or None if not found
        """
        layers = self.get_layers_from_project(geometry_type)
        for layer_name, layer in layers:
            if layer_name == name:
                return layer
        return None
    
    def get_layer_field_names(self, layer: QgsVectorLayer) -> List[str]:
        """Get list of field names from a layer.
        
        Args:
            layer: Vector layer to get fields from
            
        Returns:
            List of field names
        """
        return [field.name() for field in layer.fields()]
    
    def find_field_index(
        self,
        layer: QgsVectorLayer,
        field_candidates: List[str]
    ) -> int:
        """Find first matching field index from a list of candidates.
        
        Args:
            layer: Vector layer to search in
            field_candidates: List of field names to try (in order of preference)
            
        Returns:
            Field index of first match, or -1 if no match found
        """
        fields = layer.fields()
        for candidate in field_candidates:
            idx: int = fields.indexFromName(candidate)
            if idx >= 0:
                return idx
        return -1
