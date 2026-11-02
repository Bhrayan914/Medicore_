from .common import *
from conexion import obtener_conexion


class CitasMixin:

    def crear_citas(self):
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

        self.paciente_cita = QComboBox()
        self.paciente_cita.addItem("Seleccionar paciente", None)
        formulario.addRow("Paciente:", self.paciente_cita)

        self.medico_cita = QComboBox()
        self.medico_cita.addItem("Seleccionar médico", None)
        formulario.addRow("Médico:", self.medico_cita)

        self.fecha_cita = QDateEdit()
        self.fecha_cita.setCalendarPopup(True)
        self.fecha_cita.setDate(QDate.currentDate())
        formulario.addRow("Fecha:", self.fecha_cita)

        self.hora_cita = QTimeEdit()
        self.hora_cita.setTime(QTime(8, 0))
        formulario.addRow("Hora:", self.hora_cita)

        self.estado_cita = QComboBox()
        self.estado_cita.addItems([
            "Programada",
            "Asistio",
            "Cancelada"
        ])
        formulario.addRow("Estado:", self.estado_cita)

        estilizar_formulario(formulario, layout)
        layout.addLayout(formulario)

        botones = QHBoxLayout()

        btn_guardar = QPushButton("Guardar")
        btn_editar = QPushButton("Editar")
        btn_eliminar = QPushButton("Eliminar")
        btn_limpiar = QPushButton("Limpiar")

        btn_guardar.clicked.connect(self.guardar_cita)
        btn_editar.clicked.connect(self.editar_cita)
        btn_eliminar.clicked.connect(self.eliminar_cita)
        btn_limpiar.clicked.connect(self.limpiar_cita)

        for boton in (
            btn_guardar, btn_editar,
            btn_eliminar, btn_limpiar
        ):
            botones.addWidget(boton)

        layout.addLayout(botones)

        self.tabla_citas = QTableWidget()
        self.tabla_citas.setColumnCount(6)
        self.tabla_citas.setHorizontalHeaderLabels([
            "ID", "Paciente", "Médico",
            "Fecha", "Hora", "Estado"
        ])
        self.tabla_citas.cellClicked.connect(
            self.seleccionar_cita
        )
        layout.addWidget(self.tabla_citas)

        pestaña.setLayout(layout)
        self.tabs.addTab(pestaña, "Citas Médicas")

        self.actualizar_citas()

    def _rol_citas(self):
        return self.usuario_actual.get("Rol", "")

    def _medico_asociado_citas(self):
        return self.usuario_actual.get("ID_Medico")

    def _es_medico_citas(self):
        return self._rol_citas() == "Medico"

    def _abrir_bd_citas(self):
        conexion = obtener_conexion()
        if conexion is None:
            raise RuntimeError(
                "No se pudo conectar con la base de datos MediCore."
            )
        return conexion

    def _cargar_combos_citas(self):
        conexion = self._abrir_bd_citas()

        try:
            cursor = conexion.cursor(dictionary=True)

            self.paciente_cita.clear()
            self.paciente_cita.addItem(
                "Seleccionar paciente", None
            )

            cursor.execute("""
                SELECT ID_Paciente, Nombre
                FROM Pacientes
                ORDER BY Nombre
            """)

            for paciente in cursor.fetchall():
                self.paciente_cita.addItem(
                    paciente["Nombre"],
                    paciente["ID_Paciente"]
                )

            self.medico_cita.clear()
            self.medico_cita.addItem(
                "Seleccionar médico", None
            )

            if self._es_medico_citas():
                medico_id = self._medico_asociado_citas()

                if medico_id is None:
                    raise RuntimeError(
                        "Esta cuenta médica no tiene un médico asociado."
                    )

                cursor.execute("""
                    SELECT ID_Medico, Nombre
                    FROM Medicos
                    WHERE ID_Medico = %s
                """, (medico_id,))
            else:
                cursor.execute("""
                    SELECT ID_Medico, Nombre
                    FROM Medicos
                    ORDER BY Nombre
                """)

            for medico in cursor.fetchall():
                self.medico_cita.addItem(
                    medico["Nombre"],
                    medico["ID_Medico"]
                )

            if self._es_medico_citas():
                self.medico_cita.setCurrentIndex(
                    1 if self.medico_cita.count() > 1 else 0
                )
                self.medico_cita.setEnabled(False)
            else:
                self.medico_cita.setEnabled(True)

            cursor.close()

        finally:
            conexion.close()

    def actualizar_citas(self):
        if not hasattr(self, "tabla_citas"):
            return

        try:
            self._cargar_combos_citas()

            conexion = self._abrir_bd_citas()

            try:
                cursor = conexion.cursor(dictionary=True)

                consulta = """
                    SELECT
                        c.ID_Cita,
                        c.ID_Paciente,
                        c.ID_Medico,
                        p.Nombre AS Paciente,
                        m.Nombre AS Medico,
                        c.Fecha,
                        c.Hora,
                        c.Estado
                    FROM Citas_Medicas c
                    INNER JOIN Pacientes p
                        ON p.ID_Paciente = c.ID_Paciente
                    INNER JOIN Medicos m
                        ON m.ID_Medico = c.ID_Medico
                """

                if self._es_medico_citas():
                    consulta += " WHERE c.ID_Medico = %s"
                    cursor.execute(
                        consulta + " ORDER BY c.Fecha, c.Hora",
                        (self._medico_asociado_citas(),)
                    )
                else:
                    cursor.execute(
                        consulta + " ORDER BY c.Fecha, c.Hora"
                    )

                citas = cursor.fetchall()
                self.tabla_citas.setRowCount(0)

                for cita in citas:
                    fila = self.tabla_citas.rowCount()
                    self.tabla_citas.insertRow(fila)

                    valores = [
                        cita["ID_Cita"],
                        cita["Paciente"],
                        cita["Medico"],
                        cita["Fecha"].strftime("%Y-%m-%d"),
                        str(cita["Hora"]),
                        cita["Estado"]
                    ]

                    for columna, valor in enumerate(valores):
                        self.tabla_citas.setItem(
                            fila, columna,
                            QTableWidgetItem(str(valor))
                        )

                    self.tabla_citas.item(
                        fila, 0
                    ).setData(
                        Qt.ItemDataRole.UserRole,
                        cita["ID_Medico"]
                    )

                cursor.close()

            finally:
                conexion.close()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Error al cargar citas",
                str(error)
            )

    def _validar_cita_seleccionada(self, fila):
        if fila < 0:
            return None

        item_id = self.tabla_citas.item(fila, 0)

        if item_id is None:
            return None

        cita_id = int(item_id.text())
        medico_id = item_id.data(Qt.ItemDataRole.UserRole)

        if self._es_medico_citas():
            if medico_id != self._medico_asociado_citas():
                QMessageBox.warning(
                    self,
                    "Acceso denegado",
                    "Solo puedes gestionar tus propias citas."
                )
                return None

        return cita_id

    def guardar_cita(self):
        paciente_id = self.paciente_cita.currentData()
        medico_id = self.medico_cita.currentData()

        if paciente_id is None:
            QMessageBox.warning(
                self, "Paciente", "Selecciona un paciente."
            )
            return

        if medico_id is None:
            QMessageBox.warning(
                self, "Médico", "Selecciona un médico."
            )
            return

        if self._es_medico_citas():
            medico_id = self._medico_asociado_citas()

        fecha = self.fecha_cita.date().toString("yyyy-MM-dd")
        hora = self.hora_cita.time().toString("HH:mm:ss")
        estado = self.estado_cita.currentText()

        conexion = None

        try:
            conexion = self._abrir_bd_citas()
            cursor = conexion.cursor()

            cursor.execute("""
                INSERT INTO Citas_Medicas
                    (ID_Paciente, ID_Medico, Fecha, Hora, Estado)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                paciente_id, medico_id, fecha, hora, estado
            ))

            conexion.commit()
            cursor.close()

            self.limpiar_cita()
            self.actualizar_citas()

        except Exception as error:
            if conexion:
                conexion.rollback()

            QMessageBox.critical(
                self, "Error al guardar cita", str(error)
            )

        finally:
            if conexion:
                conexion.close()

    def editar_cita(self):
        fila = self.tabla_citas.currentRow()
        cita_id = self._validar_cita_seleccionada(fila)

        if cita_id is None:
            QMessageBox.warning(
                self,
                "Seleccionar registro",
                "Selecciona una cita válida."
            )
            return

        paciente_id = self.paciente_cita.currentData()
        medico_id = self.medico_cita.currentData()

        if paciente_id is None or medico_id is None:
            QMessageBox.warning(
                self,
                "Datos incompletos",
                "Selecciona un paciente y un médico."
            )
            return

        if self._es_medico_citas():
            medico_id = self._medico_asociado_citas()

        fecha = self.fecha_cita.date().toString("yyyy-MM-dd")
        hora = self.hora_cita.time().toString("HH:mm:ss")
        estado = self.estado_cita.currentText()

        if not self._confirmar_edicion("la cita"):
            return

        conexion = None

        try:
            conexion = self._abrir_bd_citas()
            cursor = conexion.cursor()

            if self._es_medico_citas():
                cursor.execute("""
                    UPDATE Citas_Medicas
                    SET ID_Paciente = %s, Fecha = %s,
                        Hora = %s, Estado = %s
                    WHERE ID_Cita = %s AND ID_Medico = %s
                """, (
                    paciente_id, fecha, hora, estado,
                    cita_id, medico_id
                ))
            else:
                cursor.execute("""
                    UPDATE Citas_Medicas
                    SET ID_Paciente = %s, ID_Medico = %s,
                        Fecha = %s, Hora = %s, Estado = %s
                    WHERE ID_Cita = %s
                """, (
                    paciente_id, medico_id, fecha,
                    hora, estado, cita_id
                ))

            if cursor.rowcount == 0:
                conexion.rollback()
                QMessageBox.warning(
                    self,
                    "Sin cambios",
                    "La cita no existe o no tienes permiso para modificarla."
                )
                return

            conexion.commit()
            cursor.close()

            self.limpiar_cita()
            self.actualizar_citas()

        except Exception as error:
            if conexion:
                conexion.rollback()

            QMessageBox.critical(
                self, "Error al editar cita", str(error)
            )

        finally:
            if conexion:
                conexion.close()

    def eliminar_cita(self):
        fila = self.tabla_citas.currentRow()
        cita_id = self._validar_cita_seleccionada(fila)

        if cita_id is None:
            QMessageBox.warning(
                self,
                "Seleccionar registro",
                "Selecciona una cita válida."
            )
            return

        if not self._confirmar_eliminacion("esta cita"):
            return

        conexion = None

        try:
            conexion = self._abrir_bd_citas()
            cursor = conexion.cursor()

            if self._es_medico_citas():
                cursor.execute("""
                    DELETE FROM Citas_Medicas
                    WHERE ID_Cita = %s AND ID_Medico = %s
                """, (
                    cita_id, self._medico_asociado_citas()
                ))
            else:
                cursor.execute("""
                    DELETE FROM Citas_Medicas
                    WHERE ID_Cita = %s
                """, (cita_id,))

            if cursor.rowcount == 0:
                conexion.rollback()
                QMessageBox.warning(
                    self,
                    "Acceso denegado",
                    "La cita no existe o no tienes permiso para eliminarla."
                )
                return

            conexion.commit()
            cursor.close()

            self.limpiar_cita()
            self.actualizar_citas()

        except Exception as error:
            if conexion:
                conexion.rollback()

            QMessageBox.critical(
                self, "Error al eliminar cita", str(error)
            )

        finally:
            if conexion:
                conexion.close()

    def limpiar_cita(self):
        self.paciente_cita.setCurrentIndex(0)

        if self._es_medico_citas():
            self.medico_cita.setCurrentIndex(
                1 if self.medico_cita.count() > 1 else 0
            )
        else:
            self.medico_cita.setCurrentIndex(0)

        self.fecha_cita.setDate(QDate.currentDate())
        self.hora_cita.setTime(QTime(8, 0))
        self.estado_cita.setCurrentIndex(0)
        self.tabla_citas.clearSelection()

    def seleccionar_cita(self, fila, columna):
        if fila < 0:
            return

        paciente = self.tabla_citas.item(fila, 1)
        medico = self.tabla_citas.item(fila, 2)
        fecha = self.tabla_citas.item(fila, 3)
        hora = self.tabla_citas.item(fila, 4)
        estado = self.tabla_citas.item(fila, 5)

        if paciente:
            indice = self.paciente_cita.findText(paciente.text())
            if indice >= 0:
                self.paciente_cita.setCurrentIndex(indice)

        if medico:
            indice = self.medico_cita.findText(medico.text())
            if indice >= 0:
                self.medico_cita.setCurrentIndex(indice)

        if fecha:
            self.fecha_cita.setDate(
                QDate.fromString(fecha.text(), "yyyy-MM-dd")
            )

        if hora:
            self.hora_cita.setTime(
                QTime.fromString(hora.text()[:8], "HH:mm:ss")
            )

        if estado:
            indice = self.estado_cita.findText(estado.text())
            if indice >= 0:
                self.estado_cita.setCurrentIndex(indice)