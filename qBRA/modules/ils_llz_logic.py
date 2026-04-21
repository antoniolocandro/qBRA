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
from math import tan, radians, cos, sin, pi
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
    geom = QgsGeometry(polygon)
    seg = QgsFeature()
    seg.setGeometry(geom)
    seg.setAttributes([
        4,
        "slope",
        str(site_elev + h),
        display_name,
        str(round(a, 2)),
        str(b),
        str(h),
        str(round(r, 2)),
        str(D),
        str(H),
        str(L),
        str(phi),
        _type_value,
    ])
    pr.addFeatures([seg])

    # Walls
    wall1 = [pz(pt_bl, site_elev), pz(pt_bl, side_elev), pz(pt_br, side_elev), pz(pt_br, site_elev)]
    seg = QgsFeature()
    seg.setGeometry(QgsPolygon(QgsLineString(wall1), rings=[]))
    seg.setAttributes([
        5,
        "wall",
        str(side_elev),
        display_name,
        str(round(a, 2)),
        str(b),
        str(h),
        str(round(r, 2)),
        str(D),
        str(H),
        str(L),
        str(phi),
        _type_value,
    ])
    pr.addFeatures([seg])

    wall2 = [pz(pt_al, site_elev), pz(pt_al, side_elev), pz(pt_bl, side_elev), pz(pt_bl, site_elev), pz(pt_al, site_elev)]
    seg = QgsFeature()
    seg.setGeometry(QgsPolygon(QgsLineString(wall2), rings=[]))
    seg.setAttributes([
        6,
        "wall",
        str(side_elev),
        display_name,
        str(round(a, 2)),
        str(b),
        str(h),
        str(round(r, 2)),
        str(D),
        str(H),
        str(L),
        str(phi),
        _type_value,
    ])
    pr.addFeatures([seg])

    wall3 = [pz(pt_ar, site_elev), pz(pt_ar, side_elev), pz(pt_br, side_elev), pz(pt_br, site_elev), pz(pt_ar, site_elev)]
    seg = QgsFeature()
    seg.setGeometry(QgsPolygon(QgsLineString(wall3), rings=[]))
    seg.setAttributes([
        7,
        "wall",
        str(side_elev),
        display_name,
        str(round(a, 2)),
        str(b),
        str(h),
        str(round(r, 2)),
        str(D),
        str(H),
        str(L),
        str(phi),
        _type_value,
    ])
    pr.addFeatures([seg])

    # Styling
    z_layer.renderer().symbol().setOpacity(0.5)
    z_layer.renderer().symbol().setColor(QColor("green"))
    z_layer.triggerRepaint()
    z_layer.updateExtents()

    return z_layer


def build_layers_omni(iface, params):
    """
    Build omnidirectional BRA shapes as 2D footprints:
    - Inner cylinder: circle of radius r
    - Outer cone footprint: circle of radius R
    - Optional turbine analysis cylinder: circle of radius j
    Attributes include r, alpha, R, j, h and type (last column).
    """
    layer = params["active_layer"]
    selection = layer.selectedFeatures()
    if not selection:
        raise ValueError("Select one feature on the active layer")
    feat = selection[0]
    p_geom = feat.geometry().asPoint()

    map_srid = iface.mapCanvas().mapSettings().destinationCrs().authid()

    display_name = params.get("display_name") or params.get("remark") or "BRA"
    r = float(params.get("omni_r", 0.0))
    alpha = float(params.get("omni_alpha", 1.0))
    R = float(params.get("omni_R", 0.0))
    turbine = bool(params.get("omni_turbine", False))
    j = float(params.get("omni_j", 0.0)) if turbine else 0.0
    h = float(params.get("omni_h", 0.0)) if turbine else 0.0
    base_z = float(params.get("site_elev", 0.0))

    if r <= 0 or R <= 0:
        raise ValueError("Omni parameters invalid: r and R must be > 0")
    if R < r:
        raise ValueError("Omni parameter invalid: R must be >= r")
    if alpha <= 0 or alpha > 90:
        raise ValueError("Omni parameter invalid: alpha must be in (0, 90]")
    if turbine:
        if j <= 0 or h <= 0:
            raise ValueError("Omni turbine parameters invalid: j and h must be > 0")
        if j < r:
            raise ValueError("Omni turbine parameter invalid: j must be >= r")

    # Heights from cone geometry (Figure 2.1/2.2): z = radius * tan(alpha)
    alpha_rad = radians(alpha)
    h_cone_outer = R * tan(alpha_rad)
    h_cone_inner = r * tan(alpha_rad)

    segments = 128

    # Create memory layer for 3D polygons
    layer_out = QgsVectorLayer("PolygonZ?crs=" + map_srid, f"{display_name} BRA_omni", "memory")
    fields = [
        QgsField("id", QVariantInt),
        QgsField("area", QVariantString),
        QgsField("area_name", QVariantString),
        QgsField("r", QVariantString),
        QgsField("alpha", QVariantString),
        QgsField("R", QVariantString),
        QgsField("j", QVariantString),
        QgsField("h", QVariantString),
        QgsField("type", QVariantString),
    ]
    pr = layer_out.dataProvider()
    pr.addAttributes(fields)
    layer_out.updateFields()

    _type_value = params.get("facility_label") or params.get("facility_key") or ""

    def circle_points(center_pt, radius, z_value):
        pts = []
        cx = center_pt.x()
        cy = center_pt.y()
        for i in range(segments):
            ang = 2.0 * pi * i / segments
            x = cx + radius * cos(ang)
            y = cy + radius * sin(ang)
            pts.append(QgsPoint(x, y, z_value + base_z))
        pts.append(pts[0])
        return pts

    # Inner cylinder top (flat disk at z = h_cone_inner)
    inner_ring = circle_points(p_geom, r, h_cone_inner)
    f1 = QgsFeature()
    f1.setGeometry(QgsGeometry(QgsPolygon(QgsLineString(inner_ring), rings=[])))
    f1.setAttributes([
        1,
        "inner cylinder top",
        display_name,
        str(r),
        str(alpha),
        str(R),
        str(j if turbine else 0.0),
        str(h if turbine else 0.0),
        _type_value,
    ])
    pr.addFeatures([f1])

    # Cone mantle approximated as polygon with outer ring at z=h_cone_outer and inner ring at z=h_cone_inner
    outer_ring = circle_points(p_geom, R, h_cone_outer)
    inner_ring_cone = circle_points(p_geom, r, h_cone_inner)[::-1]  # reverse for hole
    f2 = QgsFeature()
    f2.setGeometry(QgsGeometry(QgsPolygon(QgsLineString(outer_ring), rings=[QgsLineString(inner_ring_cone)])))
    f2.setAttributes([
        2,
        "cone mantle",
        display_name,
        str(r),
        str(alpha),
        str(R),
        str(j if turbine else 0.0),
        str(h if turbine else 0.0),
        _type_value,
    ])
    pr.addFeatures([f2])

    # Optional turbine cylinder top at height h
    if turbine and j > 0:
        turbine_ring = circle_points(p_geom, j, h)
        f3 = QgsFeature()
        f3.setGeometry(QgsGeometry(QgsPolygon(QgsLineString(turbine_ring), rings=[])))
        f3.setAttributes([
            3,
            "turbine cylinder top",
            display_name,
            str(r),
            str(alpha),
            str(R),
            str(j),
            str(h),
            _type_value,
        ])
        pr.addFeatures([f3])

    layer_out.triggerRepaint()
    layer_out.updateExtents()
    return layer_out
