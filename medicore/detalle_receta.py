from .common import *


class DetalleRecetaMixin:
        def crear_detalle_receta(self):
            pestaña = QWidget()
            layout = QVBoxLayout()
            formulario = FormularioCompacto()
            formulario.setContentsMargins(0, 0, 0, 8)
            formulario.setHorizontalSpacing(18)
            formulario.setVerticalSpacing(12)
            formulario.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            formulario.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

            self.receta_detalle = QComboBox()
            self.receta_detalle.addItem("Seleccionar receta")

            formulario.addRow(
                "Receta:",
                self.receta_detalle
            )

            self.medicamento_detalle = QComboBox()
            self.medicamento_detalle.addItem("Seleccionar medicamento")

            formulario.addRow(
                "Medicamento:",
                self.medicamento_detalle
            )

            self.dosis_detalle = QLineEdit()
            formulario.addRow(
                "Dosis indicada:",
                self.dosis_detalle
            )

            self.frecuencia_detalle = QLineEdit()
            formulario.addRow(
                "Frecuencia:",
                self.frecuencia_detalle
            )

            self.duracion_detalle = QLineEdit()
            formulario.addRow(
                "Duración:",
                self.duracion_detalle
            )

            self.cantidad_detalle = QSpinBox()
            self.cantidad_detalle.setRange(1, 10000)
            self.cantidad_detalle.setSuffix(" unidades")
            self.cantidad_detalle.setToolTip(
                "Unidades que se descuentan de la existencia del medicamento"
            )
            formulario.addRow(
                "Cantidad a entregar:",
                self.cantidad_detalle
            )

            estilizar_formulario(formulario, layout)
            layout.addLayout(formulario)

            botones = QHBoxLayout()

            btn_guardar = QPushButton("Guardar")
            btn_editar = QPushButton("Editar")
            btn_eliminar = QPushButton("Eliminar")
            btn_limpiar = QPushButton("Limpiar")
            btn_pdf = QPushButton("Exportar PDF")
            btn_pdf.setToolTip(
                "Genera la receta lista para imprimir (tamaño media carta) "
                "con el logo, los medicamentos y espacio para firma y sello"
            )

            btn_guardar.clicked.connect(self.guardar_detalle_receta)
            btn_editar.clicked.connect(self.editar_detalle_receta)
            btn_eliminar.clicked.connect(self.eliminar_detalle_receta)
            btn_limpiar.clicked.connect(self.limpiar_detalle_receta)
            btn_pdf.clicked.connect(self.exportar_receta_pdf)

            botones.addWidget(btn_guardar)
            botones.addWidget(btn_editar)
            botones.addWidget(btn_eliminar)
            botones.addWidget(btn_limpiar)
            botones.addWidget(btn_pdf)

            layout.addLayout(botones)

            self.tabla_detalle_receta = QTableWidget()
            self.tabla_detalle_receta.setColumnCount(6)
            self.tabla_detalle_receta.setHorizontalHeaderLabels([
                "Receta",
                "Medicamento",
                "Dosis",
                "Frecuencia",
                "Duración",
                "Cantidad"
            ])

            self.tabla_detalle_receta.cellClicked.connect(
                self.seleccionar_detalle_receta
            )

            layout.addWidget(self.tabla_detalle_receta)

            pestaña.setLayout(layout)
            self.tabs.addTab(pestaña, "Detalle Receta")

        def limpiar_detalle_receta(self):
            self.receta_detalle.setCurrentIndex(0)
            self.medicamento_detalle.setCurrentIndex(0)
            self.dosis_detalle.clear()
            self.frecuencia_detalle.clear()
            self.duracion_detalle.clear()
            self.cantidad_detalle.setValue(1)
