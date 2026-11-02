from .common import *


class ConsultasMixin:
        def crear_consultas(self):
            pestaña = QWidget()
            layout = QVBoxLayout()
            formulario = FormularioCompacto()
            formulario.setContentsMargins(0, 0, 0, 8)
            formulario.setHorizontalSpacing(18)
            formulario.setVerticalSpacing(12)
            formulario.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            formulario.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

            self.expediente_consulta = QComboBox()
            self.expediente_consulta.addItem("Seleccionar expediente")

            formulario.addRow(
                "Expediente:",
                self.expediente_consulta
            )

            self.medico_consulta = QComboBox()
            self.medico_consulta.addItem("Seleccionar médico")

            formulario.addRow(
                "Médico:",
                self.medico_consulta
            )

            self.cita_consulta = QComboBox()
            self.cita_consulta.addItem("Seleccionar cita")

            formulario.addRow(
                "Cita:",
                self.cita_consulta
            )

            self.fecha_consulta = QDateEdit()
            self.fecha_consulta.setCalendarPopup(True)
            self.fecha_consulta.setDate(QDate.currentDate())

            formulario.addRow(
                "Fecha de consulta:",
                self.fecha_consulta
            )

            self.presion_consulta = QLineEdit()
            formulario.addRow(
                "Presión arterial:",
                self.presion_consulta
            )

            self.peso_consulta = QDoubleSpinBox()
            self.peso_consulta.setRange(0.50, 500.00)
            self.peso_consulta.setDecimals(2)
            self.peso_consulta.setSuffix(" kg")

            formulario.addRow(
                "Peso:",
                self.peso_consulta
            )

            self.sintomas_consulta = QTextEdit()
            formulario.addRow(
                "Síntomas:",
                self.sintomas_consulta
            )

            self.diagnostico_consulta = QTextEdit()
            formulario.addRow(
                "Diagnóstico:",
                self.diagnostico_consulta
            )

            estilizar_formulario(formulario, layout)
            layout.addLayout(formulario)

            botones = QHBoxLayout()

            btn_guardar = QPushButton("Guardar")
            btn_editar = QPushButton("Editar")
            btn_eliminar = QPushButton("Eliminar")
            btn_limpiar = QPushButton("Limpiar")

            btn_guardar.clicked.connect(self.guardar_consulta)
            btn_editar.clicked.connect(self.editar_consulta)
            btn_eliminar.clicked.connect(self.eliminar_consulta)
            btn_limpiar.clicked.connect(self.limpiar_consulta)

            botones.addWidget(btn_guardar)
            botones.addWidget(btn_editar)
            botones.addWidget(btn_eliminar)
            botones.addWidget(btn_limpiar)

            layout.addLayout(botones)

            self.tabla_consultas = QTableWidget()
            self.tabla_consultas.setColumnCount(9)
            self.tabla_consultas.setHorizontalHeaderLabels([
                "ID",
                "Expediente",
                "Médico",
                "Cita",
                "Fecha",
                "Presión",
                "Peso",
                "Síntomas",
                "Diagnóstico"
            ])

            self.tabla_consultas.cellClicked.connect(
                self.seleccionar_consulta
            )

            layout.addWidget(self.tabla_consultas)

            pestaña.setLayout(layout)
            self.tabs.addTab(pestaña, "Consultas Historial")

        def limpiar_consulta(self):
            self.expediente_consulta.setCurrentIndex(0)
            self.medico_consulta.setCurrentIndex(0)
            self.cita_consulta.setCurrentIndex(0)
            self.fecha_consulta.setDate(QDate.currentDate())
            self.presion_consulta.clear()
            self.peso_consulta.setValue(0)
            self.sintomas_consulta.clear()
            self.diagnostico_consulta.clear()
