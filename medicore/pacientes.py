from .common import *


class PacientesMixin:
        def crear_pacientes(self):
            pestaña = QWidget()
            layout = QVBoxLayout()
            layout.setContentsMargins(14, 10, 14, 10)
            layout.setSpacing(8)

            formulario = QGridLayout()
            formulario.setContentsMargins(0, 0, 0, 0)
            formulario.setHorizontalSpacing(12)
            formulario.setVerticalSpacing(6)

            estilo_etiqueta = "QLabel { color: #25364A; font-size: 10pt; font-weight: 600; background: transparent; }"
            estilo_campo = "QLineEdit, QComboBox, QDateEdit { color: #26384B; background: #FFFFFF; border: 1px solid #D5DFE8; border-radius: 8px; padding: 6px 9px; min-height: 28px; font-size: 10pt; } QLineEdit:focus, QComboBox:focus, QDateEdit:focus { border: 1px solid #1EAA9B; }"

            self.cedula_paciente = QLineEdit()
            self.nombre_paciente = QLineEdit()
            self.fecha_nacimiento = QDateEdit()
            self.fecha_nacimiento.setCalendarPopup(True)
            self.fecha_nacimiento.setDate(QDate.currentDate())
            self.tipo_sangre = QComboBox()
            self.tipo_sangre.addItems(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
            self.sexo_paciente = QComboBox()
            self.sexo_paciente.addItems(["Seleccionar sexo", "Masculino", "Femenino"])

            campos = [
                ("Cédula:", self.cedula_paciente, 0, 0),
                ("Nombre:", self.nombre_paciente, 0, 2),
                ("Fecha de nacimiento:", self.fecha_nacimiento, 2, 0),
                ("Tipo de sangre:", self.tipo_sangre, 2, 2),
                ("Sexo:", self.sexo_paciente, 4, 0),
            ]

            for texto, campo, fila, columna in campos:
                etiqueta = QLabel(texto)
                etiqueta.setStyleSheet(estilo_etiqueta)
                campo.setStyleSheet(estilo_campo)
                campo.setMinimumHeight(34)
                formulario.addWidget(etiqueta, fila, columna)
                formulario.addWidget(campo, fila, columna + 1)
                formulario.setColumnStretch(columna + 1, 1)

            self.cedula_paciente.setMaximumWidth(260)
            self.nombre_paciente.setMaximumWidth(360)

            etiqueta_alergias = QLabel("Alergias:")
            etiqueta_alergias.setStyleSheet(estilo_etiqueta)
            self.alergias_paciente = QTextEdit()
            self.alergias_paciente.setPlaceholderText("Escribe las alergias o Ninguna")
            self.alergias_paciente.setFixedHeight(48)
            self.alergias_paciente.setStyleSheet("QTextEdit { color: #26384B; background: #FFFFFF; border: 1px solid #D5DFE8; border-radius: 8px; padding: 5px 8px; font-size: 10pt; } QTextEdit:focus { border: 1px solid #1EAA9B; }")
            formulario.addWidget(etiqueta_alergias, 6, 0)
            formulario.addWidget(self.alergias_paciente, 6, 1, 1, 3)
            formulario.setColumnStretch(3, 1)

            layout.addLayout(formulario)

            botones = QHBoxLayout()
            btn_guardar = QPushButton("Guardar")
            btn_editar = QPushButton("Editar")
            btn_eliminar = QPushButton("Eliminar")
            btn_limpiar = QPushButton("Limpiar")

            btn_guardar.clicked.connect(self.guardar_paciente)
            btn_editar.clicked.connect(self.editar_paciente)
            btn_eliminar.clicked.connect(self.eliminar_paciente)
            btn_limpiar.clicked.connect(self.limpiar_paciente)

            botones.addWidget(btn_guardar)
            botones.addWidget(btn_editar)
            botones.addWidget(btn_eliminar)
            botones.addWidget(btn_limpiar)
            layout.addLayout(botones)

            self.tabla_pacientes = QTableWidget()
            self.tabla_pacientes.setColumnCount(7)
            self.tabla_pacientes.setHorizontalHeaderLabels([
                "ID", "Cédula", "Nombre", "Fecha nacimiento", "Sexo", "Tipo sangre", "Alergias"
            ])
            self.tabla_pacientes.cellClicked.connect(self.seleccionar_paciente)
            layout.addWidget(self.tabla_pacientes)

            pestaña.setLayout(layout)
            self.tabs.addTab(pestaña, "Pacientes")

        def limpiar_paciente(self):
            self.cedula_paciente.clear()
            self.nombre_paciente.clear()
            self.fecha_nacimiento.setDate(QDate.currentDate())
            self.tipo_sangre.setCurrentIndex(0)
            self.sexo_paciente.setCurrentIndex(0)
            self.alergias_paciente.clear()

        def seleccionar_paciente(self, fila, columna):
            cedula = self.tabla_pacientes.item(fila, 1)
            nombre = self.tabla_pacientes.item(fila, 2)
            fecha = self.tabla_pacientes.item(fila, 3)
            sexo = self.tabla_pacientes.item(fila, 4)
            sangre = self.tabla_pacientes.item(fila, 5)
            alergias = self.tabla_pacientes.item(fila, 6)

            if cedula:
                # Los menores pueden no tener cédula ("Sin cédula" en la tabla).
                texto_cedula = cedula.text()
                self.cedula_paciente.setText(
                    "" if texto_cedula == "Sin cédula" else texto_cedula
                )

            if sexo:
                indice_sexo = self.sexo_paciente.findText(sexo.text())
                self.sexo_paciente.setCurrentIndex(max(indice_sexo, 0))

            if nombre:
                self.nombre_paciente.setText(nombre.text())

            if fecha:
                self.fecha_nacimiento.setDate(
                    QDate.fromString(fecha.text(), "yyyy-MM-dd")
                )

            if sangre:
                indice = self.tipo_sangre.findText(sangre.text())
                if indice >= 0:
                    self.tipo_sangre.setCurrentIndex(indice)

            if alergias:
                self.alergias_paciente.setPlainText(alergias.text())
