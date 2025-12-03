from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsGeometry, QgsPolygon, QgsLineString, QgsFeature, QgsPointXY, QgsCircularString, QgsGeometryUtils
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor

# NOTE: This module encapsulates the logic of ILS LLZ single frequency
# preserving the original calculations and geometry construction.
# It avoids using global state and "iface" directly; callers pass inputs.


def compute_parameters(navaid: str, a: float, d0: float):
    """Return parameters tuple preserving original formula selections."""
    if navaid == 'LOC':
        b=500; h=70; r=6000+a; D=500; H=10; L=2300; phi=30
    elif navaid == 'LOCII':
        b=500; h=70; r=6000+a; D=500; H=20; L=1500; phi=20
    elif navaid == 'GP':
        a=800; b=50; h=70; r=6000; D=250; H=5; L=325; phi=10
    elif navaid == 'DME':
        a=300; b=20; h=70; r=6000+a; D=600; H=20; L=1500; phi=40
    else:
        # default to DME as in original flow
        a=300; b=20; h=70; r=6000+a; D=600; H=20; L=1500; phi=40
    return a,b,h,r,D,H,L,phi


def make_point_z(point_xy, z: float):
    p = QgsPointXY(point_xy)
    # Convert to 3D point via geometry in later steps; use Z assignment in rings
    return p, z


def build_layers(p_geom, azimuth: float, site_elev: float, navaid: str, a: float, d0: float, map_srid: str, remark: str):
    """
    Create memory layers (PointZ and PolygonZ) with geometries exactly as in the legacy script.
    Returns the constructed polygon layer and point layer.
    """
    a,b,h,r,D,H,L,phi = compute_parameters(navaid, a, d0)
    side_elev = site_elev + H

    # PointZ layer
    v_layer = QgsVectorLayer(f"PointZ?crs={map_srid}", "BRA template", "memory")
    v_layer.dataProvider().addAttributes([QgsField('a', QVariant.String), QgsField('b', QVariant.String)])
    v_layer.updateFields()

    # Geometry construction points (replicating original steps)
    pt_f = p_geom.project(a,azimuth)
    pt_b = p_geom.project(b,azimuth-180)

    pt_al=pt_f.project(D,azimuth-90)
    pt_ar=pt_f.project(D,azimuth+90)
    pt_bl=pt_b.project(D,azimuth-90)
    pt_br=pt_b.project(D,azimuth+90)

    pt_Ll=pt_b.project(L,azimuth-90)
    pt_Lr=pt_b.project(L,azimuth+90)

    pt_rc=p_geom.project(r,azimuth)

    pt_Llp=pt_Ll.project(10000,azimuth)
    pt_alp=pt_al.project(10000,azimuth-phi)

    pt_Lrp=pt_Lr.project(10000,azimuth)
    pt_arp=pt_ar.project(10000,azimuth+phi)

    pt_rl = QgsPointXY(QgsGeometryUtils.lineCircleIntersection(p_geom,r,pt_al,pt_alp,pt_rc)[1])
    pt_rr = QgsPointXY(QgsGeometryUtils.lineCircleIntersection(p_geom,r,pt_ar,pt_arp,pt_rc)[1])

    pt_drl= QgsPointXY(QgsGeometryUtils.segmentIntersection(pt_al,pt_alp,pt_Ll,pt_Llp)[1])
    pt_drr= QgsPointXY(QgsGeometryUtils.segmentIntersection(pt_ar,pt_arp,pt_Lr,pt_Lrp)[1])

    lpt = [pt_f,pt_b,pt_al,pt_ar,pt_bl,pt_br,pt_Ll,pt_Lr,pt_drl,pt_drr,pt_rl,pt_rc,pt_rr]

    pr_v = v_layer.dataProvider()
    for l in lpt:
        seg = QgsFeature()
        seg.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(l)))
        pr_v.addFeatures([seg])
    v_layer.updateExtents()
    v_layer.renderer().symbol().setOpacity(1.0)
    v_layer.renderer().symbol().setColor(QColor("red"))

    # PolygonZ layer
    z_layer = QgsVectorLayer(f"PolygonZ?crs={map_srid}", f"{remark} {navaid} - BRA_areas", "memory")
    fields = [
        QgsField('id',QVariant.Int), QgsField('area',QVariant.String), QgsField('max_elev',QVariant.String), QgsField('area_name',QVariant.String),
        QgsField('a',QVariant.String), QgsField('b',QVariant.String), QgsField('h',QVariant.String), QgsField('r',QVariant.String),
        QgsField('D',QVariant.String), QgsField('H',QVariant.String), QgsField('L',QVariant.String), QgsField('phi',QVariant.String)
    ]
    z_layer.dataProvider().addAttributes(fields)
    z_layer.updateFields()
    pr_z = z_layer.dataProvider()

    def ring(points_with_z):
        return QgsLineString([QgsPointXY(p) for p,_ in points_with_z])

    # Base
    base_pts = [(pt_bl,site_elev),(pt_br,site_elev),(pt_ar,site_elev),(pt_al,site_elev),(pt_bl,site_elev)]
    geom = QgsPolygon(rings=[])
    geom.setExteriorRing(ring(base_pts))
    seg = QgsFeature(); seg.setGeometry(QgsGeometry(geom))
    seg.setAttributes([1,'base',str(site_elev),f"{remark} {navaid}",str(round(a,2)),str(b),str(h),str(round(r,2)),str(D),str(H),str(L),str(phi)])
    pr_z.addFeatures([seg])

    # Left level
    llevel_pts = [(pt_Ll,side_elev),(pt_bl,side_elev),(pt_al,side_elev),(pt_drl,side_elev),(pt_Ll,side_elev)]
    geom = QgsPolygon(); geom.setExteriorRing(ring(llevel_pts))
    seg = QgsFeature(); seg.setGeometry(QgsGeometry(geom))
    seg.setAttributes([2,'left level',str(side_elev),f"{remark} {navaid}",str(round(a,2)),str(b),str(h),str(round(r,2)),str(D),str(H),str(L),str(phi)])
    pr_z.addFeatures([seg])

    # Right level
    rlevel_pts = [(pt_br,side_elev),(pt_Lr,side_elev),(pt_drr,side_elev),(pt_ar,side_elev),(pt_br,side_elev)]
    geom = QgsPolygon(); geom.setExteriorRing(ring(rlevel_pts))
    seg = QgsFeature(); seg.setGeometry(QgsGeometry(geom))
    seg.setAttributes([3,'right level',str(side_elev),f"{remark} {navaid}",str(round(a,2)),str(b),str(h),str(round(r,2)),str(D),str(H),str(L),str(phi)])
    pr_z.addFeatures([seg])

    # Slope curve polygon
    arc = QgsCircularString.fromTwoPointsAndCenter(
        QgsPointXY(pt_rl),
        QgsPointXY(pt_rr),
        QgsPointXY(p_geom)
    )
    line_start = QgsLineString([QgsPointXY(pt_rr),QgsPointXY(pt_ar),QgsPointXY(pt_al),QgsPointXY(pt_rl)])
    curve = line_start.toCurveType(); curve.addCurve(arc)
    polygon = QgsPolygon(); polygon.setExteriorRing(curve)
    seg = QgsFeature(); seg.setGeometry(QgsGeometry(polygon))
    seg.setAttributes([4,'slope',str(site_elev+h),f"{remark} {navaid}",str(round(a,2)),str(b),str(h),str(round(r,2)),str(D),str(H),str(L),str(phi)])
    pr_z.addFeatures([seg])

    # Walls
    wall1_pts = [(pt_bl,site_elev),(pt_bl,side_elev),(pt_br,side_elev),(pt_br,site_elev)]
    geom = QgsPolygon(); geom.setExteriorRing(ring(wall1_pts))
    seg = QgsFeature(); seg.setGeometry(QgsGeometry(geom))
    seg.setAttributes([5,'wall',str(side_elev),f"{remark} {navaid}",str(round(a,2)),str(b),str(h),str(round(r,2)),str(D),str(H),str(L),str(phi)])
    pr_z.addFeatures([seg])

    wall2_pts = [(pt_al,site_elev),(pt_al,side_elev),(pt_bl,side_elev),(pt_bl,site_elev),(pt_al,site_elev)]
    geom = QgsPolygon(); geom.setExteriorRing(ring(wall2_pts))
    seg = QgsFeature(); seg.setGeometry(QgsGeometry(geom))
    seg.setAttributes([6,'wall',str(side_elev),f"{remark} {navaid}",str(round(a,2)),str(b),str(h),str(round(r,2)),str(D),str(H),str(L),str(phi)])
    pr_z.addFeatures([seg])

    wall3_pts = [(pt_ar,site_elev),(pt_ar,side_elev),(pt_br,side_elev),(pt_br,site_elev),(pt_ar,site_elev)]
    geom = QgsPolygon(); geom.setExteriorRing(ring(wall3_pts))
    seg = QgsFeature(); seg.setGeometry(QgsGeometry(geom))
    seg.setAttributes([7,'wall',str(side_elev),f"{remark} {navaid}",str(round(a,2)),str(b),str(h),str(round(r,2)),str(D),str(H),str(L),str(phi)])
    pr_z.addFeatures([seg])

    z_layer.updateExtents()
    return z_layer, v_layer
