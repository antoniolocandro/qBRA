"""ILS/LLZ BRA geometry calculation logic.

This module contains the core geometry functions for computing Building
Restriction Areas (BRA) around ILS/LLZ navaids.  The formulas and polygon
construction logic are kept identical to the legacy
``ILS_LLZ_single_frequency.py`` script — do NOT modify the geometry
calculations without a corresponding aeronautical review.

Public API
----------
create_feature(definition, params, geometry) -> QgsFeature
    Builds a single QGIS feature from a :class:`FeatureDefinition` and
    :class:`BRAParameters`.

build_layers(iface, params) -> QgsVectorLayer   # requires live QGIS
    Runs the full BRA calculation and returns a memory layer with all
    polygon features added to the QGIS project.
"""

from typing import Any, Union

from qgis.core import (
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsGeometryUtils,
    QgsProject,
    QgsPoint,
    QgsPointXY,
    QgsPolygon,
    QgsLineString,
)
from qgis.PyQt.QtGui import QColor

from ..models.bra_parameters import BRAParameters
from ..models.feature_definition import FeatureDefinition
from ..exceptions import BRACalculationError
from ..constants import PROJECTION_DISTANCE, CRS_TEMPLATE_PREFIX, LAYER_NAME_SUFFIX
from ..utils.qt_compat import QVariantInt, QVariantString

# Keep formulas and geometry construction identical to legacy script.


def create_feature(
    definition: FeatureDefinition,
    params: BRAParameters,
    geometry: QgsGeometry,
) -> QgsFeature:
    """Create a BRA feature from a definition and parameters.
    
    This function eliminates code duplication by providing a single place
    to create features with consistent attributes.
    
    Args:
        definition: FeatureDefinition with id, area, max_elev, area_name
        params: BRAParameters with all calculation parameters
        geometry: QgsGeometry for the feature polygon
        
    Returns:
        QgsFeature with geometry and attributes set
    """
    # Facility label preferred for 'type' attribute (falls back to key)
    type_value = params.facility_label or params.facility_key or ""
    
    feature = QgsFeature()
    feature.setGeometry(geometry)
    feature.setAttributes([
        definition.id,
        definition.area,
        definition.max_elev,
        definition.area_name,
        str(round(params.a, 2)),
        str(params.b),
        str(params.h),
        str(round(params.r, 2)),
        str(params.D),
        str(params.H),
        str(params.L),
        str(params.phi),
        type_value,
    ])
    
    return feature


def build_layers(iface: Any, params: BRAParameters) -> QgsVectorLayer:  # pragma: no cover
    """Build BRA (Building Restriction Areas) vector layer with polygons.
    
    Args:
        iface: QGIS interface object
        params: BRAParameters dataclass with all calculation parameters
    
    Returns:
        QgsVectorLayer with BRA polygon features
        
    Raises:
        BRACalculationError: If feature selection or geometry calculation fails
    """
    # Extract parameters from dataclass
    layer = params.active_layer
    selection = layer.selectedFeatures()
    if not selection:
        raise BRACalculationError(
            "No feature selected on active layer",
            "Layer must have at least one selected feature for BRA calculation"
        )
    feat = selection[0]
    p_geom = feat.geometry().asPoint()

    map_srid = iface.mapCanvas().mapSettings().destinationCrs().authid()

    # Helper to add Z
    def pz(point: Union[QgsPoint, QgsPointXY], z: float) -> QgsPoint:
        """Add Z coordinate to a point.
        
        Args:
            point: 2D or 3D point
            z: Z elevation value
            
        Returns:
            QgsPoint with Z coordinate set
        """
        cPoint = QgsPoint(point)
        cPoint.addZValue()
        cPoint.setZ(z)
        return cPoint

    a = params.a
    b = params.b
    h = params.h
    r = params.r
    D = params.D
    H = params.H
    L = params.L
    phi = params.phi
    azimuth = params.azimuth
    remark = params.remark
    display_name = params.display_name or params.remark
    site_elev = params.site_elev

    side_elev = site_elev + H

    # Geometry reference — all points in the map CRS:
    #   pt_threshold             navaid projected forward  by `a` (threshold point)
    #   pt_back                  navaid projected backward by `b`
    #   pt_ahead_left/right      threshold offset laterally by half-width `D`
    #   pt_back_left/right       back-center offset laterally by `D`
    #   pt_lateral_left/right    back-center offset laterally by full lateral distance `L`
    #   pt_arc_ref               navaid projected forward by `r` (arc centre-line reference)
    #   pt_*_projected           ray endpoints used for line / circle intersection
    #   pt_arc_left/right        diverging line ∩ circle(radius=r)
    #   pt_diverge_left/right    diverging line ∩ lateral boundary

    pt_threshold = p_geom.project(a, azimuth)
    pt_back      = p_geom.project(b, azimuth - 180)

    pt_ahead_left  = pt_threshold.project(D, azimuth - 90)
    pt_ahead_right = pt_threshold.project(D, azimuth + 90)
    pt_back_left   = pt_back.project(D, azimuth - 90)
    pt_back_right  = pt_back.project(D, azimuth + 90)

    pt_lateral_left  = pt_back.project(L, azimuth - 90)
    pt_lateral_right = pt_back.project(L, azimuth + 90)

    pt_arc_ref = p_geom.project(r, azimuth)

    # Projected ray endpoints for intersection calculations
    pt_lateral_left_projected  = pt_lateral_left.project(PROJECTION_DISTANCE, azimuth)
    pt_ahead_left_projected    = pt_ahead_left.project(PROJECTION_DISTANCE, azimuth - phi)

    pt_lateral_right_projected = pt_lateral_right.project(PROJECTION_DISTANCE, azimuth)
    pt_ahead_right_projected   = pt_ahead_right.project(PROJECTION_DISTANCE, azimuth + phi)

    # Diverging line ∩ circle(r)
    pt_arc_left  = QgsPointXY(QgsGeometryUtils.lineCircleIntersection(
        p_geom, r, pt_ahead_left, pt_ahead_left_projected, pt_arc_ref)[1])
    pt_arc_right = QgsPointXY(QgsGeometryUtils.lineCircleIntersection(
        p_geom, r, pt_ahead_right, pt_ahead_right_projected, pt_arc_ref)[1])

    # Diverging line ∩ lateral boundary
    pt_diverge_left = QgsPointXY(
        QgsGeometryUtils.segmentIntersection(
            QgsPoint(pt_ahead_left),  QgsPoint(pt_ahead_left_projected),
            QgsPoint(pt_lateral_left), QgsPoint(pt_lateral_left_projected))[1]
    )
    pt_diverge_right = QgsPointXY(
        QgsGeometryUtils.segmentIntersection(
            QgsPoint(pt_ahead_right),  QgsPoint(pt_ahead_right_projected),
            QgsPoint(pt_lateral_right), QgsPoint(pt_lateral_right_projected))[1]
    )

    # Memory layer for polygons
    z_layer = QgsVectorLayer(CRS_TEMPLATE_PREFIX + map_srid, f"{display_name} {LAYER_NAME_SUFFIX}", "memory")
    fields = [
        QgsField("id", QVariantInt),
        QgsField("area", QVariantString),
        QgsField("max_elev", QVariantString),
        QgsField("area_name", QVariantString),
        QgsField("a", QVariantString),
        QgsField("b", QVariantString),
        QgsField("h", QVariantString),
        QgsField("r", QVariantString),
        QgsField("D", QVariantString),
        QgsField("H", QVariantString),
        QgsField("L", QVariantString),
        QgsField("phi", QVariantString),
        # Place 'type' as the last attribute per user request
        QgsField("type", QVariantString),
    ]
    z_layer.dataProvider().addAttributes(fields)
    z_layer.updateFields()
    pr = z_layer.dataProvider()

    # Build all feature geometries (preserving exact calculations from legacy script)
    
    # Base geometry
    base_points = [pz(pt_back_left, site_elev), pz(pt_back_right, site_elev), pz(pt_ahead_right, site_elev), pz(pt_ahead_left, site_elev), pz(pt_back_left, site_elev)]
    base_geom = QgsGeometry(QgsPolygon(QgsLineString(base_points), rings=[]))

    # Left level geometry
    llevel_points = [pz(pt_lateral_left, side_elev), pz(pt_back_left, side_elev), pz(pt_ahead_left, side_elev), pz(pt_diverge_left, side_elev), pz(pt_lateral_left, side_elev)]
    llevel_geom = QgsGeometry(QgsPolygon(QgsLineString(llevel_points), rings=[]))

    # Right level geometry
    rlevel_points = [pz(pt_back_right, side_elev), pz(pt_lateral_right, side_elev), pz(pt_diverge_right, side_elev), pz(pt_ahead_right, side_elev), pz(pt_back_right, side_elev)]
    rlevel_geom = QgsGeometry(QgsPolygon(QgsLineString(rlevel_points), rings=[]))

    # Slope geometry (with curve + arc)
    from qgis.core import QgsCircularString

    arc = QgsCircularString.fromTwoPointsAndCenter(
        pz(pt_arc_left, site_elev + h),
        pz(pt_arc_right, site_elev + h),
        pz(p_geom, site_elev + h),
    )
    slope_points = [
        pz(pt_arc_right, site_elev + h),
        pz(pt_ahead_right, site_elev),
        pz(pt_ahead_left, site_elev),
        pz(pt_arc_left, site_elev + h),
    ]
    line_start = QgsLineString(slope_points)
    curve = line_start.toCurveType()
    curve.addCurve(arc)
    polygon = QgsPolygon()
    polygon.setExteriorRing(curve)
    slope_geom = QgsGeometry(polygon)

    # Wall geometries
    wall1_points = [pz(pt_back_left, site_elev), pz(pt_back_left, side_elev), pz(pt_back_right, side_elev), pz(pt_back_right, site_elev)]
    wall1_geom = QgsGeometry(QgsPolygon(QgsLineString(wall1_points), rings=[]))

    wall2_points = [pz(pt_ahead_left, site_elev), pz(pt_ahead_left, side_elev), pz(pt_back_left, side_elev), pz(pt_back_left, site_elev), pz(pt_ahead_left, site_elev)]
    wall2_geom = QgsGeometry(QgsPolygon(QgsLineString(wall2_points), rings=[]))

    wall3_points = [pz(pt_ahead_right, site_elev), pz(pt_ahead_right, side_elev), pz(pt_back_right, site_elev), pz(pt_back_right, site_elev), pz(pt_ahead_right, site_elev)]
    wall3_geom = QgsGeometry(QgsPolygon(QgsLineString(wall3_points), rings=[]))

    # Define all features declaratively (eliminates code duplication)
    feature_definitions = [
        (FeatureDefinition(1, "base", str(site_elev), display_name, base_points), base_geom),
        (FeatureDefinition(2, "left level", str(side_elev), display_name, llevel_points), llevel_geom),
        (FeatureDefinition(3, "right level", str(side_elev), display_name, rlevel_points), rlevel_geom),
        (FeatureDefinition(4, "slope", str(site_elev + h), display_name, slope_points), slope_geom),
        (FeatureDefinition(5, "wall", str(side_elev), display_name, wall1_points), wall1_geom),
        (FeatureDefinition(6, "wall", str(side_elev), display_name, wall2_points), wall2_geom),
        (FeatureDefinition(7, "wall", str(side_elev), remark, wall3_points), wall3_geom),
    ]

    # Create all features using generic function (DRY principle)
    features = [create_feature(definition, params, geometry) for definition, geometry in feature_definitions]
    pr.addFeatures(features)

    # Styling
    z_layer.renderer().symbol().setOpacity(0.5)
    z_layer.renderer().symbol().setColor(QColor("green"))
    z_layer.triggerRepaint()
    z_layer.updateExtents()

    return z_layer
