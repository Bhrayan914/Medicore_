from .common import *


class EspecialidadesMixin:
        def crear_especialidades(self):
            pestaña = QWidget()
            layout = QVBoxLayout()
            formulario = FormularioCompacto()
            formulario.setContentsMargins(0, 0, 0, 8)
            formulario.setHorizontalSpacing(18)
            formulario.setVerticalSpacing(12)
            formulario.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            formulario.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

            self.nombre_especialidad = QLineEdit()

            formulario.addRow(
                "Nombre de especialidad:",
                self.nombre_especialidad
            )

            estilizar_formulario(formulario, layout)
            layout.addLayout(formulario)

            botones = QHBoxLayout()

            btn_guardar = QPushButton("Guardar")
            btn_editar = QPushButton("Editar")
            btn_eliminar = QPushButton("Eliminar")
            btn_limpiar = QPushButton("Limpiar")

            btn_guardar.clicked.connect(self.guardar_especialidad)
            btn_editar.clicked.connect(self.editar_especialidad)
            btn_eliminar.clicked.connect(self.eliminar_especialidad)
            btn_limpiar.clicked.connect(self.limpiar_especialidad)

            botones.addWidget(btn_guardar)
            botones.addWidget(btn_editar)
            botones.addWidget(btn_eliminar)
            botones.addWidget(btn_limpiar)

            layout.addLayout(botones)

            self.tabla_especialidades = QTableWidget()
            self.tabla_especialidades.setColumnCount(2)
            self.tabla_especialidades.setHorizontalHeaderLabels([
                "ID Especialidad",
                "Nombre Especialidad"
            ])

            self.tabla_especialidades.cellClicked.connect(
                self.seleccionar_especialidad
            )

            layout.addWidget(self.tabla_especialidades)

            pestaña.setLayout(layout)

            self.tabs.addTab(pestaña, "Especialidades")

        def limpiar_especialidad(self):
            self.nombre_especialidad.clear()

        def seleccionar_especialidad(self, fila, columna):
            nombre = self.tabla_especialidades.item(fila, 1)

            if nombre:
                self.nombre_especialidad.setText(nombre.text())
