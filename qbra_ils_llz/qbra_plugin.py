from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsApplication, QgsProject, Qgis
import os

class QbraIlsLlzPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.plugin_dir = os.path.dirname(__file__)

    def tr(self, message):
        return QCoreApplication.translate('QbraIlsLlzPlugin', message)

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'resources', 'icon.png')
        self.action = QAction(QIcon(icon_path), self.tr('ILS LLZ (Single Freq)'), self.iface.mainWindow())
        self.action.setToolTip(self.tr('Abrir panel ILS/LLZ'))
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.tr('qBRA'), self.action)

    def unload(self):
        if self.action:
            self.iface.removeToolBarIcon(self.action)
            self.iface.removePluginMenu(self.tr('qBRA'), self.action)

    def run(self):
        try:
            # Abrir DockWidget anclado a la derecha, estilo qOLS
            from .ui.ils_llz_dockwidget import IlsLlzDockWidget
            dock = IlsLlzDockWidget(self.iface.mainWindow())
            dock.closingPlugin.connect(lambda: None)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, dock)
            dock.show()
            return

            # Validar contexto de capas y selección
            layers = list(QgsProject.instance().mapLayers().values())
            routing_layer = None
            for lyr in layers:
                if "routing" in lyr.name():
                    routing_layer = lyr
                    break
            if routing_layer is None:
                raise RuntimeError('No se encontró una capa con "routing" en el nombre.')

            sel = routing_layer.selectedFeatures()
            if not sel:
                raise RuntimeError('Seleccione al menos una línea en la capa de routing.')

            geom = sel[0].geometry().asPolyline()
            if not geom:
                raise RuntimeError('La geometría seleccionada no es una polilínea válida.')

            d0 = sel[0].geometry().length()
            start_point = geom[0]
            end_point = geom[-1]
            angle0 = start_point.azimuth(end_point)
            azimuth = angle0

            # Capa activa (navaid) y atributos esperados
            navaid_layer = self.iface.activeLayer()
            if navaid_layer is None:
                raise RuntimeError('No hay capa activa para el navaid.')

            navaid_sel = navaid_layer.selectedFeatures()
            if not navaid_sel:
                raise RuntimeError('Seleccione un punto del navaid en la capa activa.')

            feat = navaid_sel[0]
            p_geom = feat.geometry().asPoint()
            attrs = feat.attributes()
            if len(attrs) < 6:
                raise RuntimeError('La capa de navaid no tiene los atributos esperados (>=6).')
            rem = attrs[5]
            site_elev = float(attrs[4])
            remark = f'RWY{rem}'

            # CRS del mapa
            map_srid = self.iface.mapCanvas().mapSettings().destinationCrs().authid()

            # Parámetros iniciales
            a = d0  # compute_parameters ajustará según navaid

            # Construir capas con la lógica pythonizada, manteniendo cálculos
            from .module.ils_llz_logic import build_layers
            z_layer, v_layer = build_layers(p_geom, azimuth, site_elev, navaid, a, d0, map_srid, remark)

            # Añadir capas y replicar efectos visuales
            QgsProject.instance().addMapLayers([z_layer])
            z_layer.selectAll()
            canvas = self.iface.mapCanvas()
            canvas.zoomToSelected(z_layer)
            z_layer.removeSelection()
            z_layer.renderer().symbol().setOpacity(0.5)
            z_layer.renderer().symbol().setColor(QColor('green'))
            z_layer.triggerRepaint()
            z_layer.updateExtents()

            self.iface.messageBar().pushMessage('QPANSOPY:', 'BRA_Finished', level=Qgis.Success)
        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), self.tr('Error'), str(e))
