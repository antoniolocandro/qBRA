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
    z_layer = QgsVectorLayer("PolygonZ?crs=" + map_srid, f"{remark} BRA_areas", "memory")
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
    ]
    z_layer.dataProvider().addAttributes(fields)
    z_layer.updateFields()
    pr = z_layer.dataProvider()

    # Base
    base = [pz(pt_bl, site_elev), pz(pt_br, site_elev), pz(pt_ar, site_elev), pz(pt_al, site_elev), pz(pt_bl, site_elev)]
    seg = QgsFeature()
    seg.setGeometry(QgsPolygon(QgsLineString(base), rings=[]))
    seg.setAttributes([
        1,
        "base",
        str(site_elev),
        remark,
        str(round(a, 2)),
        str(b),
        str(h),
        str(round(r, 2)),
        str(D),
        str(H),
        str(L),
        str(phi),
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
        remark,
        str(round(a, 2)),
        str(b),
        str(h),
        str(round(r, 2)),
        str(D),
        str(H),
        str(L),
        str(phi),
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
        remark,
        str(round(a, 2)),
        str(b),
        str(h),
        str(round(r, 2)),
        str(D),
        str(H),
        str(L),
        str(phi),
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
        remark,
        str(round(a, 2)),
        str(b),
        str(h),
        str(round(r, 2)),
        str(D),
        str(H),
        str(L),
        str(phi),
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
        remark,
        str(round(a, 2)),
        str(b),
        str(h),
        str(round(r, 2)),
        str(D),
        str(H),
        str(L),
        str(phi),
    ])
    pr.addFeatures([seg])

    wall2 = [pz(pt_al, site_elev), pz(pt_al, side_elev), pz(pt_bl, side_elev), pz(pt_bl, site_elev), pz(pt_al, site_elev)]
    seg = QgsFeature()
    seg.setGeometry(QgsPolygon(QgsLineString(wall2), rings=[]))
    seg.setAttributes([
        6,
        "wall",
        str(side_elev),
        remark,
        str(round(a, 2)),
        str(b),
        str(h),
        str(round(r, 2)),
        str(D),
        str(H),
        str(L),
        str(phi),
    ])
    pr.addFeatures([seg])

    wall3 = [pz(pt_ar, site_elev), pz(pt_ar, side_elev), pz(pt_br, side_elev), pz(pt_br, site_elev), pz(pt_ar, site_elev)]
    seg = QgsFeature()
    seg.setGeometry(QgsPolygon(QgsLineString(wall3), rings=[]))
    seg.setAttributes([
        7,
        "wall",
        str(side_elev),
        remark,
        str(round(a, 2)),
        str(b),
        str(h),
        str(round(r, 2)),
        str(D),
        str(H),
        str(L),
        str(phi),
    ])
    pr.addFeatures([seg])

    # Styling
    z_layer.renderer().symbol().setOpacity(0.5)
    z_layer.renderer().symbol().setColor(QColor("green"))
    z_layer.triggerRepaint()
    z_layer.updateExtents()

    return z_layer
