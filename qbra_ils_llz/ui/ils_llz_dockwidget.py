# -*- coding: utf-8 -*-
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import Qgis, QgsProject
from qgis.utils import iface
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ils_llz_dockwidget_base.ui'))


class IlsLlzDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super(IlsLlzDockWidget, self).__init__(parent)
        self.setupUi(self)
        self._populate_layer_combos()
        self.btnClose.clicked.connect(self._on_close)
        self.btnCalculate.clicked.connect(self._on_calculate)
        # default selection
        self.comboNavaidType.setCurrentText('DME')

    def _populate_layer_combos(self):
        self.comboRouting.clear()
        self.comboNavaid.clear()
        for lyr in QgsProject.instance().mapLayers().values():
            self.comboRouting.addItem(lyr.name(), lyr)
            self.comboNavaid.addItem(lyr.name(), lyr)

    def _on_close(self):
        try:
            self.closingPlugin.emit()
            self.close()
        except Exception as e:
            iface.messageBar().pushMessage('Dock Close Error', str(e), level=Qgis.Warning, duration=5)

    def _selected_layer(self, combo: QtWidgets.QComboBox):
        idx = combo.currentIndex()
        if idx < 0:
            return None
        return combo.itemData(idx)

    def _on_calculate(self):
        try:
            routing_layer = self._selected_layer(self.comboRouting)
            navaid_layer = self._selected_layer(self.comboNavaid)
            if routing_layer is None or navaid_layer is None:
                raise RuntimeError('Select both routing and navaid layers.')

            # Respect Selected Only flags
            routing_selection = routing_layer.selectedFeatures() if self.checkRoutingSelected.isChecked() else list(routing_layer.getFeatures())
            navaid_selection = navaid_layer.selectedFeatures() if self.checkNavaidSelected.isChecked() else list(navaid_layer.getFeatures())
            if not routing_selection:
                raise RuntimeError('No routing feature selected/available.')
            if not navaid_selection:
                raise RuntimeError('No navaid point selected/available.')

            geom = routing_selection[0].geometry().asPolyline()
            if not geom:
                raise RuntimeError('Routing geometry is not a polyline.')
            d0 = routing_selection[0].geometry().length()
            start_point = geom[0]; end_point = geom[-1]
            azimuth = start_point.azimuth(end_point)

            feat = navaid_selection[0]
            p_geom = feat.geometry().asPoint()
            attrs = feat.attributes()
            if len(attrs) < 6:
                raise RuntimeError('Navaid layer does not have expected attributes (>=6).')
            rem = attrs[5]
            site_elev = float(attrs[4])
            remark = f'RWY{rem}'
            map_srid = iface.mapCanvas().mapSettings().destinationCrs().authid()

            # Parameters
            navaid = self.comboNavaidType.currentText()
            a = d0

            from ..module.ils_llz_logic import build_layers
            z_layer, v_layer = build_layers(p_geom, azimuth, site_elev, navaid, a, d0, map_srid, remark)

            QgsProject.instance().addMapLayers([z_layer])
            z_layer.selectAll(); iface.mapCanvas().zoomToSelected(z_layer); z_layer.removeSelection()
            iface.messageBar().pushMessage('QPANSOPY:', 'BRA_Finished', level=Qgis.Success, duration=5)
        except Exception as e:
            iface.messageBar().pushMessage('ILS/LLZ Error', str(e), level=Qgis.Critical, duration=7)
