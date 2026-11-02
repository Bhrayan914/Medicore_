import re

from .common import *
from .autenticacion import crear_hash


LONGITUD_MINIMA_CONTRASENA = 6
PATRON_USUARIO = re.compile(r"^[A-Za-z0-9_.-]{4,50}$")


class UsuariosMixin:
    """Gestión de cuentas de acceso. Solo el rol Administrador puede
    llegar a este módulo y usar sus acciones."""

    def crear_usuarios(self):
        self._usuario_en_edicion = None
        self._rol_en_edicion = None

        pestaña = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)

        formulario = QGridLayout()
        formulario.setContentsMargins(0, 0, 0, 0)
        formulario.setHorizontalSpacing(12)
        formulario.setVerticalSpacing(6)

        estilo_etiqueta = (
            "QLabel { color: #25364A; font-size: 10pt; "
            "font-weight: 600; background: transparent; }"
        )
        estilo_campo = (
            "QLineEdit, QComboBox { color: #26384B; background: #FFFFFF; "
            "border: 1px solid #D5DFE8; border-radius: 8px; "
            "padding: 6px 9px; min-height: 28px; font-size: 10pt; } "
            "QLineEdit:focus, QComboBox:focus { border: 1px solid #1EAA9B; } "
            "QLineEdit:read-only { background: #EEF3F7; } "
            "QComboBox:disabled { background: #EEF3F7; color: #7A8CA0; }"
        )

        self.usuario_nombre = QLineEdit()
        self.usuario_nombre.setPlaceholderText("Ej. dr.mendoza (sin espacios)")
        self.usuario_nombre.setMaxLength(50)

        self.usuario_nombre_completo = QLineEdit()
        self.usuario_nombre_completo.setPlaceholderText(
            "Ej. Dr. Juan Jose Mendoza Torres"
        )
        self.usuario_nombre_completo.setMaxLength(120)

        self.usuario_contrasena = QLineEdit()
        self.usuario_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        self.usuario_contrasena.setPlaceholderText(
            f"Mínimo {LONGITUD_MINIMA_CONTRASENA} caracteres"
        )
        self.usuario_contrasena.setMaxLength(100)

        self.usuario_confirmar = QLineEdit()
        self.usuario_confirmar.setEchoMode(QLineEdit.EchoMode.Password)
        self.usuario_confirmar.setPlaceholderText("Repite la contraseña")
        self.usuario_confirmar.setMaxLength(100)

        self.usuario_rol = QComboBox()
        self.usuario_rol.addItem("Médico", "Medico")
        self.usuario_rol.addItem("Administrativo", "Administrativo")
        self.usuario_rol.currentIndexChanged.connect(
            self._rol_usuario_cambiado
        )

        self.usuario_medico = QComboBox()
        self.usuario_medico.addItem("Seleccionar médico", None)

        self.usuario_estado = QComboBox()
        self.usuario_estado.addItems(["Activo", "Inactivo"])

        campos = [
            ("Usuario:", self.usuario_nombre, 0, 0),
            ("Nombre completo:", self.usuario_nombre_completo, 0, 2),
            ("Contraseña:", self.usuario_contrasena, 1, 0),
            ("Confirmar contraseña:", self.usuario_confirmar, 1, 2),
            ("Rol:", self.usuario_rol, 2, 0),
            ("Médico asociado:", self.usuario_medico, 2, 2),
            ("Estado:", self.usuario_estado, 3, 0),
        ]

        for texto, campo, fila, columna in campos:
            etiqueta = QLabel(texto)
            etiqueta.setStyleSheet(estilo_etiqueta)
            campo.setStyleSheet(estilo_campo)
            campo.setMinimumHeight(34)
            formulario.addWidget(etiqueta, fila, columna)
            formulario.addWidget(campo, fila, columna + 1)
            formulario.setColumnStretch(columna + 1, 1)

        ayuda = QLabel(
            "Para un usuario Médico, elige el médico registrado al que "
            "pertenece la cuenta. Al editar, deja la contraseña vacía si "
            "no quieres cambiarla."
        )
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet(
            "QLabel { color: #62748A; font-size: 9pt; background: transparent; }"
        )
        formulario.addWidget(ayuda, 3, 2, 1, 2)

        layout.addLayout(formulario)

        botones = QHBoxLayout()
        botones.setSpacing(8)

        btn_guardar = QPushButton("Guardar")
        btn_editar = QPushButton("Editar")
        btn_eliminar = QPushButton("Eliminar")
        btn_limpiar = QPushButton("Limpiar")

        btn_guardar.clicked.connect(self.guardar_usuario)
        btn_editar.clicked.connect(self.editar_usuario)
        btn_eliminar.clicked.connect(self.eliminar_usuario)
        btn_limpiar.clicked.connect(self.limpiar_usuario)

        for boton in (btn_guardar, btn_editar, btn_eliminar, btn_limpiar):
            boton.setMinimumHeight(36)
            botones.addWidget(boton)

        layout.addLayout(botones)

        self.tabla_usuarios = QTableWidget()
        self.tabla_usuarios.setColumnCount(6)
        self.tabla_usuarios.setHorizontalHeaderLabels([
            "ID", "Usuario", "Nombre completo", "Rol",
            "Médico asociado", "Estado"
        ])
        self.tabla_usuarios.cellClicked.connect(self.seleccionar_usuario)
        layout.addWidget(self.tabla_usuarios)

        pestaña.setLayout(layout)
        self.tabs.addTab(pestaña, "Usuarios")

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _rol_usuario_cambiado(self, *_):
        es_medico = self.usuario_rol.currentData() == "Medico"
        editando = self._usuario_en_edicion is not None

        self.usuario_medico.setEnabled(es_medico and not editando)

        if not es_medico and not editando:
            self.usuario_medico.setCurrentIndex(0)

    def _cargar_medicos_usuario(self, incluir_id=None):
        """Llena el combo con los médicos que aún no tienen cuenta
        (más el médico de la cuenta seleccionada, si hay una)."""
        con = None

        try:
            con = self._db()
            cur = con.cursor()
            cur.execute(
                "SELECT m.ID_Medico, m.Nombre, esp.Nombre_Especialidad "
                "FROM Medicos m "
                "JOIN Especialidades_Medicas esp "
                "     ON esp.ID_Especialidad = m.ID_Especialidad "
                "WHERE NOT EXISTS ("
                "    SELECT 1 FROM Usuarios u WHERE u.ID_Medico = m.ID_Medico"
                ") OR m.ID_Medico = %s "
                "ORDER BY m.Nombre",
                (incluir_id,)
            )

            self.usuario_medico.clear()
            self.usuario_medico.addItem("Seleccionar médico", None)

            for id_medico, nombre, especialidad in cur.fetchall():
                self.usuario_medico.addItem(
                    f"{nombre} — {especialidad}", id_medico
                )
        finally:
            if con:
                con.close()

    @staticmethod
    def _nombre_rol(rol):
        return "Médico" if rol == "Medico" else rol

    def _validar_contrasena(self, contrasena, confirmar):
        """Devuelve un mensaje de error, o None si la contraseña es válida."""
        if len(contrasena) < LONGITUD_MINIMA_CONTRASENA:
            return (
                "La contraseña debe tener al menos "
                f"{LONGITUD_MINIMA_CONTRASENA} caracteres."
            )

        if contrasena != confirmar:
            return "Las contraseñas no coinciden."

        return None

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------
    def actualizar_usuarios(self):
        if not hasattr(self, "tabla_usuarios"):
            return

        # Solo el administrador puede ver o cargar cuentas.
        if (self.usuario_actual or {}).get("Rol") != "Administrador":
            return

        con = None

        try:
            con = self._db()
            cur = con.cursor()
            cur.execute(
                "SELECT u.ID_Usuario, u.Nombre_Usuario, u.Nombre_Completo, "
                "u.Rol, COALESCE(m.Nombre, '—'), u.Estado "
                "FROM Usuarios u "
                "LEFT JOIN Medicos m ON m.ID_Medico = u.ID_Medico "
                "ORDER BY u.ID_Usuario"
            )

            filas = [
                (f[0], f[1], f[2], self._nombre_rol(f[3]), f[4], f[5])
                for f in cur.fetchall()
            ]
            self._cargar_tabla(self.tabla_usuarios, filas)

            if self._usuario_en_edicion is None:
                self._cargar_medicos_usuario()
                self._rol_usuario_cambiado()

        except Exception as error:
            self._mensaje_error("Usuarios", error)
        finally:
            if con:
                con.close()

    def seleccionar_usuario(self, fila, columna):
        con = None

        try:
            id_usuario = int(self._item(self.tabla_usuarios, fila, 0))

            con = self._db()
            cur = con.cursor()
            cur.execute(
                "SELECT Nombre_Usuario, Nombre_Completo, Rol, ID_Medico, "
                "Estado FROM Usuarios WHERE ID_Usuario = %s",
                (id_usuario,)
            )
            registro = cur.fetchone()

            if registro is None:
                return

            usuario, nombre, rol, id_medico, estado = registro

            self._usuario_en_edicion = id_usuario
            self._rol_en_edicion = rol

            self._cargar_medicos_usuario(id_medico)

            # Las cuentas de administrador solo se muestran.
            if self.usuario_rol.findData("Administrador") < 0:
                self.usuario_rol.addItem("Administrador", "Administrador")

            self.usuario_nombre.setText(usuario)
            self.usuario_nombre.setReadOnly(True)
            self.usuario_nombre_completo.setText(nombre)
            self.usuario_contrasena.clear()
            self.usuario_confirmar.clear()
            self.usuario_rol.setCurrentIndex(self.usuario_rol.findData(rol))
            self.usuario_rol.setEnabled(False)
            self.usuario_medico.setCurrentIndex(
                max(self.usuario_medico.findData(id_medico), 0)
            )
            self.usuario_medico.setEnabled(False)
            self.usuario_estado.setCurrentText(estado)

        except Exception as error:
            self._mensaje_error("Seleccionar usuario", error)
        finally:
            if con:
                con.close()

    def limpiar_usuario(self):
        self._usuario_en_edicion = None
        self._rol_en_edicion = None

        indice_admin = self.usuario_rol.findData("Administrador")

        if indice_admin >= 0:
            self.usuario_rol.removeItem(indice_admin)

        self.usuario_nombre.clear()
        self.usuario_nombre.setReadOnly(False)
        self.usuario_nombre_completo.clear()
        self.usuario_contrasena.clear()
        self.usuario_confirmar.clear()
        self.usuario_rol.setEnabled(True)
        self.usuario_rol.setCurrentIndex(0)
        self.usuario_estado.setCurrentIndex(0)
        self.tabla_usuarios.clearSelection()

        try:
            self._cargar_medicos_usuario()
        except Exception as error:
            self._mensaje_error("Usuarios", error)

        self._rol_usuario_cambiado()

    # ------------------------------------------------------------------
    # Registrar
    # ------------------------------------------------------------------
    def guardar_usuario(self):
        if not self._permitir("Usuarios", "crear"):
            return

        if self._usuario_en_edicion is not None:
            QMessageBox.information(
                self,
                "Nuevo usuario",
                "Tienes una cuenta seleccionada de la tabla.\n"
                "Pulsa Limpiar para registrar un usuario nuevo."
            )
            return

        usuario = self.usuario_nombre.text().strip()
        nombre = self.usuario_nombre_completo.text().strip()
        contrasena = self.usuario_contrasena.text()
        confirmar = self.usuario_confirmar.text()
        rol = self.usuario_rol.currentData()
        id_medico = self.usuario_medico.currentData()
        estado = self.usuario_estado.currentText()

        error = None

        if not PATRON_USUARIO.match(usuario):
            error = (
                "El usuario debe tener entre 4 y 50 caracteres y usar solo "
                "letras, números, punto, guion o guion bajo (sin espacios)."
            )
        elif not nombre:
            error = "Escribe el nombre completo de la persona."
        elif rol not in ("Medico", "Administrativo"):
            error = "Selecciona el rol del usuario."
        elif rol == "Medico" and id_medico is None:
            error = "Selecciona el médico al que pertenece esta cuenta."
        else:
            error = self._validar_contrasena(contrasena, confirmar)

        if error:
            QMessageBox.warning(self, "Validación", error)
            return

        if rol != "Medico":
            id_medico = None

        con = None

        try:
            con = self._db()
            cur = con.cursor()
            cur.execute(
                "INSERT INTO Usuarios (Nombre_Usuario, Contrasena_Hash, "
                "Nombre_Completo, Rol, ID_Medico, Estado) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (usuario, crear_hash(contrasena), nombre, rol,
                 id_medico, estado)
            )
            con.commit()

        except Exception as e:
            if con:
                con.rollback()

            if getattr(e, "errno", None) == 1062:
                texto = str(e)

                if "ID_Medico" in texto or "uq_usuario_medico" in texto:
                    QMessageBox.warning(
                        self,
                        "Médico con cuenta",
                        "Ese médico ya tiene una cuenta de usuario."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Usuario repetido",
                        "Ya existe una cuenta con ese nombre de usuario. "
                        "Elige otro."
                    )
            else:
                self._mensaje_error("No se pudo registrar el usuario", e)
            return
        finally:
            if con:
                con.close()

        QMessageBox.information(
            self,
            "Usuario registrado",
            f"La cuenta «{usuario}» se registró correctamente."
        )
        self.limpiar_usuario()
        self.actualizar_usuarios()

    # ------------------------------------------------------------------
    # Editar
    # ------------------------------------------------------------------
    def editar_usuario(self):
        if not self._permitir("Usuarios", "editar"):
            return

        id_usuario = self._usuario_en_edicion

        if id_usuario is None:
            QMessageBox.warning(
                self, "Validación", "Selecciona un usuario de la tabla."
            )
            return

        if self._rol_en_edicion == "Administrador":
            QMessageBox.warning(
                self,
                "Cuenta protegida",
                "Las cuentas de administrador no se modifican desde este módulo."
            )
            return

        nombre = self.usuario_nombre_completo.text().strip()
        contrasena = self.usuario_contrasena.text()
        confirmar = self.usuario_confirmar.text()
        estado = self.usuario_estado.currentText()

        if not nombre:
            QMessageBox.warning(
                self, "Validación", "Escribe el nombre completo de la persona."
            )
            return

        if contrasena or confirmar:
            error = self._validar_contrasena(contrasena, confirmar)

            if error:
                QMessageBox.warning(self, "Validación", error)
                return

        if not self._confirmar_edicion("este usuario"):
            return

        con = None

        try:
            con = self._db()
            cur = con.cursor()

            if contrasena:
                cur.execute(
                    "UPDATE Usuarios SET Nombre_Completo = %s, Estado = %s, "
                    "Contrasena_Hash = %s WHERE ID_Usuario = %s",
                    (nombre, estado, crear_hash(contrasena), id_usuario)
                )
            else:
                cur.execute(
                    "UPDATE Usuarios SET Nombre_Completo = %s, Estado = %s "
                    "WHERE ID_Usuario = %s",
                    (nombre, estado, id_usuario)
                )

            con.commit()

        except Exception as e:
            if con:
                con.rollback()
            self._mensaje_error("No se pudo actualizar el usuario", e)
            return
        finally:
            if con:
                con.close()

        self.limpiar_usuario()
        self.actualizar_usuarios()

    # ------------------------------------------------------------------
    # Eliminar
    # ------------------------------------------------------------------
    def eliminar_usuario(self):
        if not self._permitir("Usuarios", "eliminar"):
            return

        id_usuario = self._usuario_en_edicion

        if id_usuario is None:
            QMessageBox.warning(
                self, "Validación", "Selecciona un usuario de la tabla."
            )
            return

        if self._rol_en_edicion == "Administrador":
            QMessageBox.warning(
                self,
                "Cuenta protegida",
                "Las cuentas de administrador no se eliminan desde este módulo."
            )
            return

        if not self._confirmar_eliminacion("este usuario"):
            return

        con = None

        try:
            con = self._db()
            cur = con.cursor()
            cur.execute(
                "DELETE FROM Usuarios WHERE ID_Usuario = %s", (id_usuario,)
            )
            con.commit()

        except Exception as e:
            if con:
                con.rollback()
            self._mensaje_error("No se pudo eliminar el usuario", e)
            return
        finally:
            if con:
                con.close()

        self.limpiar_usuario()
        self.actualizar_usuarios()