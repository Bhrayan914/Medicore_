from .common import *
from conexion import obtener_conexion


class ExpedientesMixin:

    def crear_expedientes(self):
        pestaña = QWidget()
        layout = QVBoxLayout()

        formulario = FormularioCompacto()
        formulario.setContentsMargins(0, 0, 0, 8)
        formulario.setHorizontalSpacing(18)
        formulario.setVerticalSpacing(12)
        formulario.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft |
            Qt.AlignmentFlag.AlignVCenter
        )
        formulario.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )

        self.paciente_expediente = QComboBox()
        self.paciente_expediente.addItem(
            "Seleccionar paciente", None
        )
        formulario.addRow(
            "Paciente:", self.paciente_expediente
        )

        self.fecha_expediente = QDateEdit()
        self.fecha_expediente.setCalendarPopup(True)
        self.fecha_expediente.setDate(QDate.currentDate())
        formulario.addRow(
            "Fecha de creación:", self.fecha_expediente
        )

        self.lugar_expediente = QLineEdit()
        formulario.addRow(
            "Lugar del expediente:", self.lugar_expediente
        )

        estilizar_formulario(formulario, layout)
        layout.addLayout(formulario)

        botones = QHBoxLayout()

        btn_guardar = QPushButton("Guardar")
        btn_editar = QPushButton("Editar")
        btn_eliminar = QPushButton("Eliminar")
        btn_limpiar = QPushButton("Limpiar")

        btn_guardar.clicked.connect(self.guardar_expediente)
        btn_editar.clicked.connect(self.editar_expediente)
        btn_eliminar.clicked.connect(self.eliminar_expediente)
        btn_limpiar.clicked.connect(self.limpiar_expediente)

        for boton in (
            btn_guardar, btn_editar,
            btn_eliminar, btn_limpiar
        ):
            botones.addWidget(boton)

        layout.addLayout(botones)

        self.tabla_expedientes = QTableWidget()
        self.tabla_expedientes.setColumnCount(5)
        self.tabla_expedientes.setHorizontalHeaderLabels([
            "ID", "Paciente", "Fecha creación", "Lugar", "Estado"
        ])
        self.tabla_expedientes.cellClicked.connect(
            self.seleccionar_expediente
        )

        layout.addWidget(self.tabla_expedientes)

        pestaña.setLayout(layout)
        self.tabs.addTab(pestaña, "Expedientes Clínicos")

        self.actualizar_expedientes()

    def _conexion_expedientes(self):
        conexion = obtener_conexion()

        if conexion is None:
            raise RuntimeError(
                "No se pudo conectar con la base de datos MediCore."
            )

        return conexion

    def guardar_expediente(self):
        paciente_id = self.paciente_expediente.currentData()
        fecha = self.fecha_expediente.date().toString(
            "yyyy-MM-dd"
        )
        lugar = self.lugar_expediente.text().strip().upper()

        if paciente_id is None:
            QMessageBox.warning(
                self,
                "Paciente",
                "Debes seleccionar un paciente."
            )
            return

        conexion = None

        try:
            conexion = self._conexion_expedientes()
            cursor = conexion.cursor()

            cursor.execute("""
                INSERT INTO Expedientes_Clinicos
                    (ID_Paciente, Fecha_Creacion, Lugar_Expediente)
                VALUES (%s, %s, %s)
            """, (paciente_id, fecha, lugar))

            conexion.commit()
            cursor.close()

            self.limpiar_expediente()
            self.actualizar_expedientes()

            QMessageBox.information(
                self,
                "Expediente registrado",
                "El expediente clínico fue registrado correctamente."
            )

        except Exception as error:
            if conexion:
                conexion.rollback()

            if getattr(error, "errno", None) == 1062:
                if "Lugar_Expediente" in str(error):
                    QMessageBox.warning(
                        self,
                        "Lugar ya asignado",
                        "Ese lugar ya está asignado a otro expediente."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Expediente duplicado",
                        "Este paciente ya tiene un expediente clínico."
                    )
            else:
                QMessageBox.critical(
                    self,
                    "Error al guardar",
                    str(error)
                )

        finally:
            if conexion:
                conexion.close()

    def editar_expediente(self):
        fila = self.tabla_expedientes.currentRow()

        if fila < 0:
            QMessageBox.warning(
                self,
                "Seleccionar registro",
                "Selecciona un expediente."
            )
            return

        item_id = self.tabla_expedientes.item(fila, 0)
        paciente_id = self.paciente_expediente.currentData()

        if item_id is None or paciente_id is None:
            QMessageBox.warning(
                self,
                "Datos incompletos",
                "Selecciona un expediente y un paciente."
            )
            return

        expediente_id = int(item_id.text())
        fecha = self.fecha_expediente.date().toString(
            "yyyy-MM-dd"
        )
        lugar = self.lugar_expediente.text().strip().upper()

        if not self._confirmar_edicion("el expediente"):
            return

        conexion = None

        try:
            conexion = self._conexion_expedientes()
            cursor = conexion.cursor()

            cursor.execute("""
                UPDATE Expedientes_Clinicos
                SET ID_Paciente = %s,
                    Fecha_Creacion = %s,
                    Lugar_Expediente = %s
                WHERE ID_Expediente = %s
            """, (paciente_id, fecha, lugar, expediente_id))

            if cursor.rowcount == 0:
                cursor.execute("""
                    SELECT ID_Expediente
                    FROM Expedientes_Clinicos
                    WHERE ID_Expediente = %s
                """, (expediente_id,))

                if cursor.fetchone() is None:
                    conexion.rollback()
                    QMessageBox.warning(
                        self,
                        "Registro no encontrado",
                        "El expediente ya no existe."
                    )
                    return

            conexion.commit()
            cursor.close()

            self.limpiar_expediente()
            self.actualizar_expedientes()

            QMessageBox.information(
                self,
                "Expediente actualizado",
                "Los datos se actualizaron correctamente."
            )

        except Exception as error:
            if conexion:
                conexion.rollback()

            if getattr(error, "errno", None) == 1062:
                if "Lugar_Expediente" in str(error):
                    QMessageBox.warning(
                        self,
                        "Lugar ya asignado",
                        "Ese lugar ya está asignado a otro expediente."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Expediente duplicado",
                        "El paciente seleccionado ya tiene otro expediente."
                    )
            else:
                QMessageBox.critical(
                    self,
                    "Error al editar",
                    str(error)
                )

        finally:
            if conexion:
                conexion.close()

    def eliminar_expediente(self):
        fila = self.tabla_expedientes.currentRow()

        if fila < 0:
            QMessageBox.warning(
                self,
                "Seleccionar registro",
                "Selecciona un expediente."
            )
            return

        item_id = self.tabla_expedientes.item(fila, 0)

        if item_id is None:
            return

        expediente_id = int(item_id.text())

        if not self._confirmar_eliminacion("este expediente"):
            return

        conexion = None

        try:
            conexion = self._conexion_expedientes()
            cursor = conexion.cursor()

            cursor.execute("""
                DELETE FROM Expedientes_Clinicos
                WHERE ID_Expediente = %s
            """, (expediente_id,))

            conexion.commit()
            cursor.close()

            self.limpiar_expediente()
            self.actualizar_expedientes()

            QMessageBox.information(
                self,
                "Expediente eliminado",
                "El expediente fue eliminado correctamente."
            )

        except Exception as error:
            if conexion:
                conexion.rollback()

            if getattr(error, "errno", None) == 1451:
                QMessageBox.warning(
                    self,
                    "No se puede eliminar",
                    "Este expediente tiene consultas relacionadas. "
                    "No se puede eliminar mientras existan esos registros."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error al eliminar",
                    str(error)
                )

        finally:
            if conexion:
                conexion.close()

    def limpiar_expediente(self):
        self.paciente_expediente.setCurrentIndex(0)
        self.fecha_expediente.setDate(QDate.currentDate())
        self.lugar_expediente.clear()
        self.tabla_expedientes.clearSelection()

    def seleccionar_expediente(self, fila, columna):
        if fila < 0:
            return

        paciente = self.tabla_expedientes.item(fila, 1)
        fecha = self.tabla_expedientes.item(fila, 2)
        lugar = self.tabla_expedientes.item(fila, 3)

        if lugar:
            self.lugar_expediente.setText(
                "" if lugar.text() == "Sin asignar" else lugar.text()
            )

        if paciente:
            indice = self.paciente_expediente.findText(
                paciente.text()
            )

            if indice >= 0:
                self.paciente_expediente.setCurrentIndex(indice)

        if fecha:
            self.fecha_expediente.setDate(
                QDate.fromString(
                    fecha.text(), "yyyy-MM-dd"
                )
            )