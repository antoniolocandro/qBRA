from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton

class NavaidDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('ILS/LLZ Parameters')
        layout = QVBoxLayout(self)

        hl = QHBoxLayout()
        hl.addWidget(QLabel('Navaid type:'))
        self.combo = QComboBox(self)
        self.combo.addItems(['LOC', 'LOCII', 'GP', 'DME'])
        self.combo.setCurrentText('DME')
        hl.addWidget(self.combo)
        layout.addLayout(hl)

        btns = QHBoxLayout()
        self.btn_ok = QPushButton('Run')
        self.btn_cancel = QPushButton('Cancel')
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        btns.addWidget(self.btn_ok)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)

    def selected_navaid(self):
        return self.combo.currentText()
