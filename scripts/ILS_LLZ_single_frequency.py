'''
BRA for ILS LLZ single frequency
'''


myglobals = set(globals().keys())

from qgis.core import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.gui import *
from qgis.PyQt.QtCore import QVariant
from math import *


from qgis.core import Qgis
iface.messageBar().pushMessage("QPANSOPY:", "BRA Areas", level=Qgis.Info)

remark ='RWY14R '




for layer in QgsProject.instance().mapLayers().values():

    if "routing" in layer.name():

        layer = layer

        selection = layer.selectedFeatures()

        geom=selection[0].geometry().asPolyline()

        #print (geom)

        d0 = selection[0].geometry().length()

        start_point = QgsPoint(geom[0])

        end_point = QgsPoint(geom[-1])

        angle0=start_point.azimuth(end_point)

        length0=selection[0].geometry().length()

        back_angle0 = angle0+180

        #print ("angle:",angle0,length0/1852)



#initial true azimuth data

azimuth =angle0

a=d0

print ("length:",d0)

#print (a)




navaid = 'DME'

if navaid == 'LOC':
    # Parameters
    # ILS Single Frequency
    a=d0
    b=500
    h=70
    r=6000+a
    D=500
    H=10
    L=2300
    phi=30

    

elif navaid == 'LOCII':

    # Parameters
    # ILS Dual Frequency

    a=d0
    b=500
    h=70
    r=6000+a
    D=500
    H=20
    L=1500
    phi=20
    
elif navaid == 'GP':

    ## Parameters
    # GP
    a=800
    b=50
    h=70
    r=6000
    D=250
    H=5
    L=325
    phi=10

elif navaid == 'DME':

    ## Parameters
    # GP
    a=300
    b=20
    h=70
    r=6000+a
    D=600
    H=20
    L=1500
    phi=40

else:
    pass


# Selects Navaid

layer = iface.activeLayer()



selection = layer.selectedFeatures()

# Gets x,y

for feat in selection:

    p_geom = feat.geometry().asPoint()

    attrs = feat.attributes()

    # print the second attribute (note zero-based indexing of Python lists)

    #idx = layer.fieldNameIndex('elevation_m')

    rem = attrs[5]

    site_elev = float(attrs[4])

    print('site elev: ',attrs[4])

    #print (p_geom)



remark =remark+'RWY'+rem



#print(feat.attributes()['elevation_m'])



#site_elev = 62 #elev in meters




side_elev = site_elev+H
#print (side_elev)

#function to convert from PointXY and add Z value
def pz (point,z):
    cPoint = QgsPoint(point)
    cPoint.addZValue()
    cPoint.setZ(z)
    return cPoint
    


# map_srid
map_srid = iface.mapCanvas().mapSettings().destinationCrs().authid()
#print (map_srid)




#Create memory layer
v_layer = QgsVectorLayer("PointZ?crs="+map_srid, "BRA template ", "memory")
an = QgsField( 'a', QVariant.String)
bn = QgsField( 'b', QVariant.String)
v_layer.dataProvider().addAttributes([an])
v_layer.dataProvider().addAttributes([bn])
v_layer.updateFields()
pr = v_layer.dataProvider()




# create box 

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

pt_drl= QgsPointXY(QgsGeometryUtils.segmentIntersection(QgsPoint(pt_al),QgsPoint(pt_alp),QgsPoint(pt_Ll),QgsPoint(pt_Llp))[1])
pt_drr= QgsPointXY(QgsGeometryUtils.segmentIntersection(QgsPoint(pt_ar),QgsPoint(pt_arp),QgsPoint(pt_Lr),QgsPoint(pt_Lrp))[1])


pt_rc=p_geom.project(r,azimuth)

#print (pt1)
# create storage for points 
lpt = []
#lpt.extend([pt_b,pt_al,pt_ar,pt_bl,pt_br,pt_Ll,pt_Lr,pt_rc,pt_drl,pt_drr])
lpt.extend([pt_f,pt_b,pt_al,pt_ar,pt_bl,pt_br,pt_Ll,pt_Lr,pt_drl,pt_drr,pt_rl,pt_rc,pt_rr])


for l in lpt:
    #print (l)
    pr = v_layer.dataProvider()
    seg = QgsFeature()
    seg.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(l)))
    #seg.setAttributes([ch])
    ## ...it was here that you can add attributes, after having defined....
    ## add the geometry to the layer
    #print (l)
    pr.addFeatures( [ seg ] )
    #ch= chr(ord(ch) + 1)    
    


## update extent of the layer (not necessary)
v_layer.updateExtents()


# Change style of layer 
v_layer.renderer().symbol().setOpacity(1.0)
v_layer.renderer().symbol().setColor(QColor("red"))
#v_layer.renderer().symbol().setWidth(0.5)
iface.layerTreeView().refreshLayerSymbology( iface.activeLayer().id() )
v_layer.triggerRepaint()


# show construction points  
#QgsProject.instance().addMapLayers([v_layer])


#Create memory layer
z_layer = QgsVectorLayer("PolygonZ?crs="+map_srid, remark+' '+navaid+" - BRA_areas", "memory")
id = QgsField('id',QVariant.Int)
area = QgsField('area',QVariant.String)
max_elev = QgsField('max_elev',QVariant.String)
area_name = QgsField('area_name',QVariant.String)

a1 = QgsField('a',QVariant.String)

b1 = QgsField('b',QVariant.String)

h1 = QgsField('h',QVariant.String)

r1 = QgsField('r',QVariant.String)

D1 = QgsField('D',QVariant.String)

H1 = QgsField('H',QVariant.String)

L1 = QgsField('L',QVariant.String)

phi1 =QgsField('phi',QVariant.String)

#z_layer.dataProvider().addAttributes([id,area,max_elev,area_name,a])

z_layer.dataProvider().addAttributes([id,area,max_elev,area_name,a1,b1,h1,r1,D1,H1,L1,phi1])
z_layer.updateFields()
pr = z_layer.dataProvider()

# add base

#base = [pt_bl,pt_br,pt_ar,pt_al,pt_bl]
base = [pz(pt_bl,site_elev),pz(pt_br,site_elev),pz(pt_ar,site_elev),pz(pt_al,site_elev),pz(pt_bl,site_elev)]
seg = QgsFeature()
seg.setGeometry(QgsPolygon(QgsLineString(base), rings=[]))
geom=QgsPolygon(QgsLineString(base), rings=[])
seg.setAttributes([1,'base',str(site_elev),remark+' '+navaid,str(round(a,2)),str(b),str(h),str(round(r,2)),str(D),str(H),str(L),str(phi)])
pr.addFeatures( [ seg ] )

# add left level
#llevel = [pt_Ll,pt_bl,pt_al,pt_drl,pt_Ll]
llevel = [pz(pt_Ll,side_elev),pz(pt_bl,side_elev),pz(pt_al,side_elev),pz(pt_drl,side_elev),pz(pt_Ll,side_elev)]
seg = QgsFeature()
seg.setGeometry(QgsPolygon(QgsLineString(llevel), rings=[]))
geom=QgsPolygon(QgsLineString(llevel), rings=[])
seg.setAttributes([2,'left level',str(side_elev),remark+' '+navaid,str(round(a,2)),str(b),str(h),str(round(r,2)),str(D),str(H),str(L),str(phi)])
pr.addFeatures( [ seg ] )

# add right level
#rlevel = [pt_br,pt_Lr,pt_drr,pt_ar,pt_br]
rlevel = [pz(pt_br,side_elev),pz(pt_Lr,side_elev),pz(pt_drr,side_elev),pz(pt_ar,side_elev),pz(pt_br,side_elev)]
seg = QgsFeature()
seg.setGeometry(QgsPolygon(QgsLineString(rlevel), rings=[]))
geom=QgsPolygon(QgsLineString(rlevel), rings=[])
seg.setAttributes([3,'right level',str(side_elev),remark+' '+navaid,str(round(a,2)),str(b),str(h),str(round(r,2)),str(D),str(H),str(L),str(phi)])
pr.addFeatures( [ seg ] )

# add sloping surface 

# slope1 = [pt_al,pt_ar,pt_drr,pt_rr,pt_rl,pt_drl,pt_al]
# seg = QgsFeature()
# seg.setGeometry(QgsPolygon(QgsLineString(slope1), rings=[]))
# geom=QgsPolygon(QgsLineString(slope1), rings=[])
# seg.setAttributes([4,'slope1'])
# pr.addFeatures( [ seg ] )
# # Update extent
# layer.updateExtents()

# Create the arc segment
arc = QgsCircularString.fromTwoPointsAndCenter(
    pz(pt_rl,site_elev+h),
    pz(pt_rr,site_elev+h),
    pz(p_geom,site_elev+h)
)

line_start =QgsLineString([pz(pt_rr,site_elev+h),pz(pt_ar,site_elev),pz(pt_al,site_elev),pz(pt_rl,site_elev+h)])

# join both segments together
curve = line_start.toCurveType()
curve.addCurve(arc)

# create polygon geometry from exterior line
polygon = QgsPolygon()
polygon.setExteriorRing(curve)
geom = QgsGeometry(polygon)
seg = QgsFeature()
seg.setGeometry(geom)
seg.setAttributes([4,'slope',str(site_elev+h),remark+' '+navaid,str(round(a,2)),str(b),str(h),str(round(r,2)),str(D),str(H),str(L),str(phi)])
pr.addFeatures([seg])
# Update extent
layer.updateExtents()


# add walls 
wall1 = [pz(pt_bl,site_elev),pz(pt_bl,side_elev),pz(pt_br,side_elev),pz(pt_br,site_elev)]
seg = QgsFeature()
seg.setGeometry(QgsPolygon(QgsLineString(wall1), rings=[]))
geom=QgsPolygon(QgsLineString(wall1), rings=[])
seg.setAttributes([5,'wall',str(side_elev),remark+' '+navaid,str(round(a,2)),str(b),str(h),str(round(r,2)),str(D),str(H),str(L),str(phi)])
pr.addFeatures( [ seg ] )

wall1 = [pz(pt_al,site_elev),pz(pt_al,side_elev),pz(pt_bl,side_elev),pz(pt_bl,site_elev),pz(pt_al,site_elev)]
seg = QgsFeature()
seg.setGeometry(QgsPolygon(QgsLineString(wall1), rings=[]))
geom=QgsPolygon(QgsLineString(wall1), rings=[])
seg.setAttributes([6,'wall',str(side_elev),remark+' '+navaid,str(round(a,2)),str(b),str(h),str(round(r,2)),str(D),str(H),str(L),str(phi)])
pr.addFeatures( [ seg ] )

wall3 = [pz(pt_ar,site_elev),pz(pt_ar,side_elev),pz(pt_br,side_elev),pz(pt_br,site_elev),pz(pt_ar,site_elev)]
seg = QgsFeature()
seg.setGeometry(QgsPolygon(QgsLineString(wall3), rings=[]))
geom=QgsPolygon(QgsLineString(wall3), rings=[])
seg.setAttributes([7,'wall',str(side_elev),remark+' '+navaid,str(round(a,2)),str(b),str(h),str(round(r,2)),str(D),str(H),str(L),str(phi)])
pr.addFeatures( [ seg ] )

# wall4 = [pz(pt_al,site_elev),pz(pt_al,side_elev),pz(pt_drl,side_elev),pz(pt_al,site_elev)]
# seg = QgsFeature()
# seg.setGeometry(QgsPolygon(QgsLineString(wall4), rings=[]))
# geom=QgsPolygon(QgsLineString(wall4), rings=[])
# seg.setAttributes([8,'wall',str(side_elev),remark+' '+navaid])
# pr.addFeatures( [ seg ] )

# wall5 = [pz(pt_ar,site_elev),pz(pt_ar,side_elev),pz(pt_drr,side_elev),pz(pt_ar,site_elev)]
# seg = QgsFeature()
# seg.setGeometry(QgsPolygon(QgsLineString(wall5), rings=[]))
# geom=QgsPolygon(QgsLineString(wall5), rings=[])
# seg.setAttributes([9,'wall',str(side_elev),remark+' '+navaid])
# pr.addFeatures( [ seg ] )


QgsProject.instance().addMapLayers([z_layer])

z_layer.selectAll()

canvas = iface.mapCanvas()

canvas.zoomToSelected(z_layer)

z_layer.removeSelection()



# Change style of layer 
z_layer.renderer().symbol().setOpacity(0.5)
z_layer.renderer().symbol().setColor(QColor("green"))
#print(z_layer.renderer().symbol().symbolLayers()[0].properties())
#z_layer.renderer().symbol().setStrokeColor(QColor("blue"))
#v_layer.renderer().symbol().setWidth(0.5)
iface.layerTreeView().refreshLayerSymbology( iface.activeLayer().id() )
z_layer.triggerRepaint()
z_layer.updateExtents()



iface.messageBar().pushMessage("QPANSOPY:", "BRA_Finished", level=Qgis.Success)

set(globals().keys()).difference(myglobals)

for g in set(globals().keys()).difference(myglobals):
    if g != 'myglobals':
        del globals()[g]