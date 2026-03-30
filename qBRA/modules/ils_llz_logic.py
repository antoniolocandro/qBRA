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
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor

# Keep formulas and geometry construction identical to legacy script.

def build_layers(iface, params):
    # params expected keys: active_layer, azimuth, a, b, h, r, D, H, L, phi, remark, site_elev
    layer = params["active_layer"]
    selection = layer.selectedFeatures()
    if not selection:
        raise ValueError("Select one feature on the active layer")
    feat = selection[0]
    p_geom = feat.geometry().asPoint()

    map_srid = iface.mapCanvas().mapSettings().destinationCrs().authid()

    # Helper to add Z
    def pz(point, z):
        cPoint = QgsPoint(point)
        cPoint.addZValue()
        cPoint.setZ(z)
        return cPoint

    a = params["a"]
    b = params["b"]
    h = params["h"]
    r = params["r"]
    D = params["D"]
    H = params["H"]
    L = params["L"]
    phi = params["phi"]
    azimuth = params["azimuth"]
    remark = params["remark"]
    display_name = params.get("display_name") or remark
    site_elev = params["site_elev"]

    side_elev = site_elev + H

    # Points (direction is encoded solely by azimuth)
    pt_f = p_geom.project(a, azimuth)
    pt_b = p_geom.project(b, azimuth - 180)

    pt_al = pt_f.project(D, azimuth - 90)
    pt_ar = pt_f.project(D, azimuth + 90)
    pt_bl = pt_b.project(D, azimuth - 90)
    pt_br = pt_b.project(D, azimuth + 90)

    pt_Ll = pt_b.project(L, azimuth - 90)
    pt_Lr = pt_b.project(L, azimuth + 90)

    pt_rc = p_geom.project(r, azimuth)

    pt_Llp = pt_Ll.project(10000, azimuth)
    pt_alp = pt_al.project(10000, azimuth - phi)

    pt_Lrp = pt_Lr.project(10000, azimuth)
    pt_arp = pt_ar.project(10000, azimuth + phi)

    pt_rl = QgsPointXY(QgsGeometryUtils.lineCircleIntersection(p_geom, r, pt_al, pt_alp, pt_rc)[1])
    pt_rr = QgsPointXY(QgsGeometryUtils.lineCircleIntersection(p_geom, r, pt_ar, pt_arp, pt_rc)[1])

    pt_drl = QgsPointXY(
        QgsGeometryUtils.segmentIntersection(QgsPoint(pt_al), QgsPoint(pt_alp), QgsPoint(pt_Ll), QgsPoint(pt_Llp))[1]
    )
    pt_drr = QgsPointXY(
        QgsGeometryUtils.segmentIntersection(QgsPoint(pt_ar), QgsPoint(pt_arp), QgsPoint(pt_Lr), QgsPoint(pt_Lrp))[1]
    )

    # Memory layer for polygons
    z_layer = QgsVectorLayer("PolygonZ?crs=" + map_srid, f"{display_name} BRA_areas", "memory")
    fields = [
        QgsField("id", QVariant.Int),
        QgsField("area", QVariant.String),
        QgsField("max_elev", QVariant.String),
        QgsField("area_name", QVariant.String),
        QgsField("a", QVariant.String),
        QgsField("b", QVariant.String),
        QgsField("h", QVariant.String),
        QgsField("r", QVariant.String),
        QgsField("D", QVariant.String),
        QgsField("H", QVariant.String),
        QgsField("L", QVariant.String),
        QgsField("phi", QVariant.String),
        # Place 'type' as the last attribute per user request
        QgsField("type", QVariant.String),
    ]
    z_layer.dataProvider().addAttributes(fields)
    z_layer.updateFields()
    pr = z_layer.dataProvider()

    # Facility label preferred for 'type' attribute (falls back to key)
    _type_value = params.get("facility_label") or params.get("facility_key") or ""

    # Base
    base = [pz(pt_bl, site_elev), pz(pt_br, site_elev), pz(pt_ar, site_elev), pz(pt_al, site_elev), pz(pt_bl, site_elev)]
    seg = QgsFeature()
    seg.setGeometry(QgsPolygon(QgsLineString(base), rings=[]))
    seg.setAttributes([
        1,
        "base",
        str(site_elev),
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

    # Left level
    llevel = [pz(pt_Ll, side_elev), pz(pt_bl, side_elev), pz(pt_al, side_elev), pz(pt_drl, side_elev), pz(pt_Ll, side_elev)]
    seg = QgsFeature()
    seg.setGeometry(QgsPolygon(QgsLineString(llevel), rings=[]))
    seg.setAttributes([
        2,
        "left level",
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

    # Right level
    rlevel = [pz(pt_br, side_elev), pz(pt_Lr, side_elev), pz(pt_drr, side_elev), pz(pt_ar, side_elev), pz(pt_br, side_elev)]
    seg = QgsFeature()
    seg.setGeometry(QgsPolygon(QgsLineString(rlevel), rings=[]))
    seg.setAttributes([
        3,
        "right level",
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

    # Slope as curve + arc
    from qgis.core import QgsCircularString

    arc = QgsCircularString.fromTwoPointsAndCenter(
        pz(pt_rl, site_elev + h),
        pz(pt_rr, site_elev + h),
        pz(p_geom, site_elev + h),
    )

    line_start = QgsLineString(
        [pz(pt_rr, site_elev + h), pz(pt_ar, site_elev), pz(pt_al, site_elev), pz(pt_rl, site_elev + h)]
    )
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
        QgsField("id", QVariant.Int),
        QgsField("area", QVariant.String),
        QgsField("area_name", QVariant.String),
        QgsField("r", QVariant.String),
        QgsField("alpha", QVariant.String),
        QgsField("R", QVariant.String),
        QgsField("j", QVariant.String),
        QgsField("h", QVariant.String),
        QgsField("type", QVariant.String),
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
