from .common import *


class MedicosMixin:
        def crear_medicos(self):
            pestaña = QWidget()
            layout = QVBoxLayout()
            formulario = FormularioCompacto()
            formulario.setContentsMargins(0, 0, 0, 8)
            formulario.setHorizontalSpacing(18)
            formulario.setVerticalSpacing(12)
            formulario.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            formulario.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

            self.codigo_minsa = QLineEdit()
            self.nombre_medico = QLineEdit()

            formulario.addRow("Código MINSA:", self.codigo_minsa)
            formulario.addRow("Nombre:", self.nombre_medico)

            self.especialidad_medico = QComboBox()
            self.especialidad_medico.addItem("Seleccionar especialidad")

            formulario.addRow(
                "Especialidad:",
                self.especialidad_medico
            )

            self.turno_medico = QComboBox()
            self.turno_medico.addItems([
                "Matutino",
                "Vespertino",
                "Nocturno"
            ])

            formulario.addRow("Turno:", self.turno_medico)

            estilizar_formulario(formulario, layout)
            layout.addLayout(formulario)

            botones = QHBoxLayout()

            btn_guardar = QPushButton("Guardar")
            btn_editar = QPushButton("Editar")
            btn_eliminar = QPushButton("Eliminar")
            btn_limpiar = QPushButton("Limpiar")

            btn_guardar.clicked.connect(self.guardar_medico)
            btn_editar.clicked.connect(self.editar_medico)
            btn_eliminar.clicked.connect(self.eliminar_medico)
            btn_limpiar.clicked.connect(self.limpiar_medico)

            botones.addWidget(btn_guardar)
            botones.addWidget(btn_editar)
            botones.addWidget(btn_eliminar)
            botones.addWidget(btn_limpiar)

            layout.addLayout(botones)

            self.tabla_medicos = QTableWidget()
            self.tabla_medicos.setColumnCount(5)
            self.tabla_medicos.setHorizontalHeaderLabels([
                "ID",
                "Código MINSA",
                "Nombre",
                "Especialidad",
                "Turno"
            ])

            self.tabla_medicos.cellClicked.connect(
                self.seleccionar_medico
            )

            layout.addWidget(self.tabla_medicos)

            pestaña.setLayout(layout)
            self.tabs.addTab(pestaña, "Médicos")

        def limpiar_medico(self):
            self.codigo_minsa.clear()
            self.nombre_medico.clear()
            self.especialidad_medico.setCurrentIndex(0)
            self.turno_medico.setCurrentIndex(0)

        def seleccionar_medico(self, fila, columna):
            codigo = self.tabla_medicos.item(fila, 1)
            nombre = self.tabla_medicos.item(fila, 2)
            especialidad = self.tabla_medicos.item(fila, 3)
            turno = self.tabla_medicos.item(fila, 4)

            if codigo:
                self.codigo_minsa.setText(codigo.text())

            if nombre:
                self.nombre_medico.setText(nombre.text())

            if especialidad:
                indice = self.especialidad_medico.findText(
                    especialidad.text()
                )
                if indice >= 0:
                    self.especialidad_medico.setCurrentIndex(indice)

            if turno:
                indice = self.turno_medico.findText(turno.text())
                if indice >= 0:
                    self.turno_medico.setCurrentIndex(indice)
