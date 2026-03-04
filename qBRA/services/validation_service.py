"""Validation service for qBRA plugin.

Provides validation logic for layers, features, and parameters.
All methods are pure functions for easy testing.
"""

from typing import Optional, Any
from qgis.core import QgsVectorLayer, QgsWkbTypes


class ValidationError(Exception):
    """Raised when validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None) -> None:
        """Initialize validation error.
        
        Args:
            message: Human-readable error message
            field: Optional field name that failed validation
        """
        super().__init__(message)
        self.field = field
        self.message = message


class ValidationService:
    """Service for validating layers, features, and parameters.
    
    This service contains pure validation logic with no side effects.
    All methods are static for easy testing and reuse.
    """
    
    @staticmethod
    def validate_layer_selected(
        layer: Optional[Any],
        layer_name: str = "layer"
    ) -> None:
        """Validate that a layer is selected.
        
        Args:
            layer: Layer object to validate
            layer_name: Name of the layer for error message
            
        Raises:
            ValidationError: If layer is not selected
        """
        if layer is None:
            raise ValidationError(
                f"No {layer_name} selected",
                field=layer_name
            )
    
    @staticmethod
    def validate_layer_type(
        layer: QgsVectorLayer,
        expected_type: QgsWkbTypes.GeometryType,
        layer_name: str = "layer"
    ) -> None:
        """Validate that a layer has the expected geometry type.
        
        Args:
            layer: Vector layer to validate
            expected_type: Expected geometry type (e.g., QgsWkbTypes.PointGeometry)
            layer_name: Name of the layer for error message
            
        Raises:
            ValidationError: If layer has wrong geometry type
        """
        if not isinstance(layer, QgsVectorLayer):
            raise ValidationError(
                f"{layer_name} is not a vector layer",
                field=layer_name
            )
        
        actual_type = QgsWkbTypes.geometryType(layer.wkbType())
        if actual_type != expected_type:
            type_names = {
                QgsWkbTypes.PointGeometry: "point",
                QgsWkbTypes.LineGeometry: "line",
                QgsWkbTypes.PolygonGeometry: "polygon",
            }
            expected_name = type_names.get(expected_type, str(expected_type))
            actual_name = type_names.get(actual_type, str(actual_type))
            
            raise ValidationError(
                f"{layer_name} must be {expected_name} layer, got {actual_name}",
                field=layer_name
            )
    
    @staticmethod
    def validate_feature_selected(
        layer: QgsVectorLayer,
        layer_name: str = "layer"
    ) -> None:
        """Validate that layer has at least one selected feature.
        
        Args:
            layer: Vector layer to check
            layer_name: Name of the layer for error message
            
        Raises:
            ValidationError: If no features are selected
        """
        if not layer.selectedFeatures():
            raise ValidationError(
                f"No feature selected on {layer_name}",
                field=layer_name
            )
    
    @staticmethod
    def validate_geometry_vertices(
        layer: QgsVectorLayer,
        min_vertices: int = 2,
        layer_name: str = "layer"
    ) -> None:
        """Validate that selected feature has sufficient vertices.
        
        Args:
            layer: Vector layer with selected feature
            min_vertices: Minimum number of vertices required
            layer_name: Name of the layer for error message
            
        Raises:
            ValidationError: If geometry has insufficient vertices
        """
        selected = layer.selectedFeatures()
        if not selected:
            raise ValidationError(
                f"No feature selected on {layer_name}",
                field=layer_name
            )
        
        feature = selected[0]
        geom = feature.geometry()
        
        # Get vertices based on geometry type
        if geom.isMultipart():
            parts = geom.asMultiPolyline() if geom.type() == QgsWkbTypes.LineGeometry else geom.asMultiPolygon()
            if not parts or not parts[0]:
                raise ValidationError(
                    f"{layer_name} geometry has no vertices",
                    field=layer_name
                )
            vertices = parts[0]
        else:
            vertices = geom.asPolyline() if geom.type() == QgsWkbTypes.LineGeometry else geom.asPolygon()
        
        if not vertices or len(vertices) < min_vertices:
            raise ValidationError(
                f"{layer_name} geometry must have at least {min_vertices} vertices, got {len(vertices) if vertices else 0}",
                field=layer_name
            )
    
    @staticmethod
    def validate_positive_number(
        value: float,
        field_name: str,
        min_value: float = 0.0,
        exclusive: bool = True
    ) -> None:
        """Validate that a number is positive.
        
        Args:
            value: Number to validate
            field_name: Name of the field for error message
            min_value: Minimum allowed value
            exclusive: If True, value must be > min_value; if False, value must be >= min_value
            
        Raises:
            ValidationError: If value is not positive
        """
        if exclusive:
            if value <= min_value:
                raise ValidationError(
                    f"{field_name} must be greater than {min_value}, got {value}",
                    field=field_name
                )
        else:
            if value < min_value:
                raise ValidationError(
                    f"{field_name} must be at least {min_value}, got {value}",
                    field=field_name
                )
    
    @staticmethod
    def validate_angle_range(
        value: float,
        field_name: str,
        min_angle: float = 0.0,
        max_angle: float = 360.0,
        inclusive_min: bool = True,
        inclusive_max: bool = False
    ) -> None:
        """Validate that an angle is within range.
        
        Args:
            value: Angle value to validate (degrees)
            field_name: Name of the field for error message
            min_angle: Minimum angle (degrees)
            max_angle: Maximum angle (degrees)
            inclusive_min: If True, min_angle is inclusive
            inclusive_max: If True, max_angle is inclusive
            
        Raises:
            ValidationError: If angle is out of range
        """
        min_ok = value >= min_angle if inclusive_min else value > min_angle
        max_ok = value <= max_angle if inclusive_max else value < max_angle
        
        if not (min_ok and max_ok):
            min_bracket = "[" if inclusive_min else "("
            max_bracket = "]" if inclusive_max else ")"
            raise ValidationError(
                f"{field_name} must be in range {min_bracket}{min_angle}, {max_angle}{max_bracket}, got {value}",
                field=field_name
            )
    
    @staticmethod
    def validate_direction(value: str) -> None:
        """Validate routing direction value.
        
        Args:
            value: Direction string to validate
            
        Raises:
            ValidationError: If direction is invalid
        """
        valid_directions = ("forward", "backward")
        if value not in valid_directions:
            raise ValidationError(
                f"direction must be one of {valid_directions}, got '{value}'",
                field="direction"
            )
    
    @staticmethod
    def validate_non_empty_string(value: str, field_name: str) -> None:
        """Validate that a string is not empty.
        
        Args:
            value: String to validate
            field_name: Name of the field for error message
            
        Raises:
            ValidationError: If string is empty
        """
        if not value or not value.strip():
            raise ValidationError(
                f"{field_name} cannot be empty",
                field=field_name
            )
