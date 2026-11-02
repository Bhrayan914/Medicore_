import tempfile
from pathlib import Path

from .common import *
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QDialog
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QPolygonF


def _guardar_icono(nombre, dibujar, lado=36):
    """Dibuja un icono PNG en la carpeta temporal y devuelve su ruta."""
    carpeta = Path(tempfile.gettempdir()) / "medicore_iconos"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / nombre

    pixmap = QPixmap(lado, lado)
    pixmap.fill(Qt.GlobalColor.transparent)

    pintor = QPainter(pixmap)
    pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
    dibujar(pintor)
    pintor.end()

    pixmap.save(str(ruta), "PNG")
    return ruta.as_posix()


def _dibujar_calendario(p):
    color = QColor("#0F766E")

    # Marco del calendario
    p.setPen(QPen(color, 3))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(4, 7, 28, 25), 4, 4)

    # Franja superior
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    p.drawRect(QRectF(4, 7, 28, 8))

    # Argollas
    p.setPen(QPen(color, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(11, 3, 11, 10)
    p.drawLine(25, 3, 25, 10)

    # Días
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    for y in (20, 26):
        for x in (9, 16, 23):
            p.drawRect(QRectF(x, y, 4, 3))


def _dibujar_flecha(p):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#475569"))
    p.drawPolygon(QPolygonF([
        QPointF(9, 13), QPointF(27, 13), QPointF(18, 24)
    ]))


class InterfazMixin:
    def crear_interfaz(self):
        self.setMinimumSize(1180, 760)

        contenedor = QWidget()
        contenedor.setObjectName("contenedorPrincipal")
        self.setCentralWidget(contenedor)

        layout_general = QHBoxLayout(contenedor)
        layout_general.setContentsMargins(0, 0, 0, 0)
        layout_general.setSpacing(0)

        self.panel_lateral = QFrame()
        self.panel_lateral.setObjectName("panelLateral")
        self.panel_lateral.setFixedWidth(238)

        layout_lateral = QVBoxLayout(self.panel_lateral)
        layout_lateral.setContentsMargins(16, 22, 16, 18)
        layout_lateral.setSpacing(8)

        marca = QHBoxLayout()

        logo = QLabel("✚")
        logo.setObjectName("logoMarca")
        logo.setFixedSize(44, 44)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        marca_texto = QVBoxLayout()
        marca_texto.setContentsMargins(0, 0, 0, 0)
        marca_texto.setSpacing(3)

        nombre_marca = QLabel("MediCore")
        nombre_marca.setObjectName("nombreMarca")
        nombre_marca.setMinimumWidth(145)
        nombre_marca.setMinimumHeight(30)
        nombre_marca.setWordWrap(False)

        lema_marca = QLabel("SISTEMA INTEGRAL")
        lema_marca.setObjectName("lemaMarca")
        lema_marca.setMinimumWidth(145)
        lema_marca.setMinimumHeight(16)
        lema_marca.setWordWrap(False)

        marca_texto.addWidget(nombre_marca)
        marca_texto.addWidget(lema_marca)
        marca.addWidget(logo)
        marca.addLayout(marca_texto, 1)
        layout_lateral.addLayout(marca)

        separador = QFrame()
        separador.setObjectName("separadorLateral")
        separador.setFixedHeight(1)
        layout_lateral.addWidget(separador)
        layout_lateral.addSpacing(10)

        etiqueta_menu = QLabel("MENÚ PRINCIPAL")
        etiqueta_menu.setObjectName("etiquetaMenu")
        layout_lateral.addWidget(etiqueta_menu)

        boton_acerca = QPushButton("ⓘ   Acerca de MediCore")
        boton_acerca.setObjectName("botonNavegacion")
        boton_acerca.setCursor(Qt.CursorShape.PointingHandCursor)
        boton_acerca.clicked.connect(self.mostrar_acerca_de)
        layout_lateral.addWidget(boton_acerca)

        self.tabs = QTabWidget()

        self.crear_especialidades()
        self.crear_medicos()
        self.crear_pacientes()
        self.crear_agenda()
        self.crear_citas()
        self.crear_expedientes()
        self.crear_consultas()
        self.crear_recetas()
        self.crear_medicamentos()
        self.crear_detalle_receta()
        self.crear_usuarios()
        self.aplicar_placeholders()

        self.tabs.tabBar().hide()
        self.tabs.setObjectName("areaModulos")
        self.botones_navegacion = []

        # Permisos de navegación según el rol autenticado.
        rol = self.usuario_actual.get("Rol", "")

        permisos = {
            "Administrador": [
                "Especialidades",
                "Médicos",
                "Pacientes",
                "Agenda Horarios",
                "Citas Médicas",
                "Consultas Historial",
                "Expedientes Clínicos",
                "Recetas Médicas",
                "Medicamentos",
                "Detalle Receta",
                "Usuarios",
            ],
            "Administrativo": [
                "Pacientes",
                "Agenda Horarios",
                "Citas Médicas",
            ],
            "Medico": [
                "Pacientes",
                "Agenda Horarios",
                "Citas Médicas",
                "Consultas Historial",
                "Expedientes Clínicos",
                "Recetas Médicas",
                "Detalle Receta",
            ],
        }

        modulos_permitidos = permisos.get(rol, [])

        grupos = {
            "GESTIÓN MÉDICA": [
                "Especialidades",
                "Médicos",
                "Pacientes",
            ],
            "AGENDA Y ATENCIÓN": [
                "Agenda Horarios",
                "Citas Médicas",
                "Consultas Historial",
            ],
            "EXPEDIENTES Y FARMACIA": [
                "Expedientes Clínicos",
                "Recetas Médicas",
                "Medicamentos",
                "Detalle Receta",
            ],
            "ADMINISTRACIÓN": [
                "Usuarios",
            ],
        }

        # Ocultar las pestañas que el rol no tiene autorizadas.
        indices_permitidos = []

        for indice in range(self.tabs.count()):
            nombre_tab = self.tabs.tabText(indice)
            visible = nombre_tab in modulos_permitidos

            self.tabs.setTabVisible(indice, visible)

            if visible:
                indices_permitidos.append(indice)

        # Área desplazable únicamente para las funciones del menú lateral.
        # La marca superior y la tarjeta del usuario permanecen fijas.
        self.scroll_menu_lateral = QScrollArea()
        self.scroll_menu_lateral.setObjectName("scrollMenuLateral")
        self.scroll_menu_lateral.setWidgetResizable(True)
        self.scroll_menu_lateral.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_menu_lateral.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_menu_lateral.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        contenido_menu = QWidget()
        contenido_menu.setObjectName("contenidoMenuLateral")

        layout_menu = QVBoxLayout(contenido_menu)
        layout_menu.setContentsMargins(0, 0, 6, 0)
        layout_menu.setSpacing(8)

        # Crear únicamente los botones autorizados.
        for grupo, nombres in grupos.items():
            nombres_visibles = [
                nombre
                for nombre in nombres
                if nombre in modulos_permitidos
            ]

            if not nombres_visibles:
                continue

            etiqueta = QLabel(grupo)
            etiqueta.setObjectName("etiquetaGrupo")

            layout_menu.addSpacing(14)
            layout_menu.addWidget(etiqueta)

            for nombre in nombres_visibles:
                indice = self._buscar_indice_tab(nombre)

                if indice < 0:
                    continue

                boton = QPushButton(nombre)
                boton.setObjectName("botonNavegacion")
                boton.setCheckable(True)
                boton.setProperty("indiceTab", indice)
                boton.setCursor(
                    Qt.CursorShape.PointingHandCursor
                )

                boton.clicked.connect(
                    lambda checked=False, i=indice:
                    self.cambiar_modulo(i)
                )

                layout_menu.addWidget(boton)
                self.botones_navegacion.append(boton)

        layout_menu.addStretch()
        self.scroll_menu_lateral.setWidget(contenido_menu)
        layout_lateral.addWidget(self.scroll_menu_lateral, 1)

        tarjeta_usuario = QFrame()
        tarjeta_usuario.setObjectName("tarjetaUsuario")

        usuario_layout = QVBoxLayout(tarjeta_usuario)
        usuario_layout.setContentsMargins(12, 12, 12, 12)
        usuario_layout.setSpacing(4)

        usuario_titulo = QLabel(
            self.usuario_actual.get(
                "Nombre_Completo", "Usuario"
            )
        )
        usuario_titulo.setObjectName("usuarioTitulo")

        usuario_subtitulo = QLabel(
            f"Rol: {rol}"
        )
        usuario_subtitulo.setObjectName("usuarioSubtitulo")

        usuario_layout.addWidget(usuario_titulo)
        usuario_layout.addWidget(usuario_subtitulo)
        layout_lateral.addWidget(tarjeta_usuario)

        zona_contenido = QWidget()
        zona_contenido.setObjectName("zonaContenido")

        layout_contenido = QVBoxLayout(zona_contenido)
        layout_contenido.setContentsMargins(28, 22, 28, 24)
        layout_contenido.setSpacing(18)

        cabecera = QFrame()
        cabecera.setObjectName("cabeceraContenido")

        cabecera_layout = QHBoxLayout(cabecera)
        cabecera_layout.setContentsMargins(0, 0, 0, 14)

        textos_cabecera = QVBoxLayout()
        textos_cabecera.setSpacing(5)

        self.titulo_modulo = QLabel("")
        self.titulo_modulo.setObjectName("tituloModulo")

        subtitulo = QLabel(
            "Administra la información y los procesos "
            "del centro hospitalario."
        )
        subtitulo.setObjectName("subtituloModulo")

        textos_cabecera.addWidget(self.titulo_modulo)
        textos_cabecera.addWidget(subtitulo)

        boton_cerrar_sesion = QPushButton("Cerrar sesión")
        boton_cerrar_sesion.setObjectName("botonCerrarSesion")
        boton_cerrar_sesion.setCursor(Qt.CursorShape.PointingHandCursor)
        boton_cerrar_sesion.clicked.connect(self.cerrar_sesion)

        cabecera_layout.addLayout(textos_cabecera)
        cabecera_layout.addStretch()
        cabecera_layout.addWidget(
            boton_cerrar_sesion,
            alignment=Qt.AlignmentFlag.AlignTop
        )

        # Los módulos van dentro de un área con desplazamiento: si la ventana
        # es baja, se puede bajar para ver la tabla completa (sin recortes).
        self.scroll_modulos = QScrollArea()
        self.scroll_modulos.setObjectName("scrollModulos")
        self.scroll_modulos.setWidgetResizable(True)
        self.scroll_modulos.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_modulos.setWidget(self.tabs)

        layout_contenido.addWidget(cabecera)
        layout_contenido.addWidget(self.scroll_modulos, 1)

        layout_general.addWidget(self.panel_lateral)
        layout_general.addWidget(zona_contenido, 1)

        self.tabs.currentChanged.connect(
            self.actualizar_cabecera_modulo
        )

        # Abrir el primer módulo permitido.
        if indices_permitidos:
            self.cambiar_modulo(indices_permitidos[0])
        else:
            self.titulo_modulo.setText("Sin módulos disponibles")

            QMessageBox.warning(
                self,
                "Acceso sin módulos",
                "El rol de esta cuenta no tiene módulos asignados."
            )

    def aplicar_placeholders(self):
        """Texto de ayuda y límites de longitud (según las columnas de la
        base de datos) en los campos donde el usuario escribe."""
        campos_texto = {
            # atributo: (texto de ayuda, longitud máxima)
            "nombre_especialidad": ("Ej. Medicina General", 100),
            "codigo_minsa": ("Ej. MINSA-0001", 20),
            "nombre_medico": ("Nombre y apellido. Ej. Carlos Mendoza", 100),
            "cedula_paciente": ("Ej. 001-010190-0001A", 16),
            "nombre_paciente": ("Nombre y apellido. Ej. María López", 100),
            "lugar_expediente": ("Ej. A-001", 5),
            "presion_consulta": ("Ej. 120/80", 10),
            "nombre_medicamento": ("Ej. Acetaminofén", 100),
            "presentacion_medicamento": ("Ej. Tabletas 500 mg", 100),
            "dosis_detalle": ("Ej. 1 tableta (500 mg)", 100),
            "frecuencia_detalle": ("Ej. Cada 8 horas", 100),
            "duracion_detalle": ("Ej. 7 días", 100),
        }

        for atributo, (ayuda, maximo) in campos_texto.items():
            campo = getattr(self, atributo, None)

            if campo is not None:
                campo.setPlaceholderText(ayuda)
                campo.setMaxLength(maximo)

        campos_multilinea = {
            "alergias_paciente": "Escribe las alergias conocidas (Ej. Penicilina) o Ninguna",
            "sintomas_consulta": "Describe los síntomas. Ej. Fiebre y tos seca desde hace tres días",
            "diagnostico_consulta": "Escribe el diagnóstico. Ej. Faringitis aguda",
        }

        for atributo, ayuda in campos_multilinea.items():
            campo = getattr(self, atributo, None)

            if campo is not None:
                campo.setPlaceholderText(ayuda)

        # Campos numéricos: no admiten placeholder, se indica la unidad.
        existencia = getattr(self, "existencia_medicamento", None)

        if existencia is not None:
            existencia.setSuffix(" unidades")
            existencia.setToolTip("Cantidad de unidades disponibles en inventario")

        peso = getattr(self, "peso_consulta", None)

        if peso is not None:
            peso.setToolTip("Peso del paciente en kilogramos. Ej. 62.50")

    def _crear_logo_pixmap(self, tamano=72):
        """Dibuja el logo de MediCore (cruz blanca sobre cuadro turquesa),
        el mismo que se ve en la esquina del menú lateral."""
        escala = 2
        pixmap = QPixmap(tamano * escala, tamano * escala)
        pixmap.fill(Qt.GlobalColor.transparent)
        pixmap.setDevicePixelRatio(escala)

        pintor = QPainter(pixmap)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pintor.setPen(Qt.PenStyle.NoPen)

        pintor.setBrush(QColor("#1EAA9B"))
        radio = tamano * 0.24
        pintor.drawRoundedRect(QRectF(0, 0, tamano, tamano), radio, radio)

        pintor.setBrush(QColor("#FFFFFF"))
        grosor = tamano * 0.20
        largo = tamano * 0.56
        centro = tamano / 2
        redondeo = grosor * 0.25

        pintor.drawRoundedRect(
            QRectF(centro - grosor / 2, centro - largo / 2, grosor, largo),
            redondeo, redondeo
        )
        pintor.drawRoundedRect(
            QRectF(centro - largo / 2, centro - grosor / 2, largo, grosor),
            redondeo, redondeo
        )
        pintor.end()

        return pixmap

    def _buscar_indice_tab(self, nombre):
        for indice in range(self.tabs.count()):
            if (
                self.tabs.tabText(indice).casefold()
                == nombre.casefold()
            ):
                return indice

        return -1

    def cambiar_modulo(self, indice):
        if indice < 0 or indice >= self.tabs.count():
            return

        # Evitar abrir módulos que no corresponden al rol.
        if self.tabs.isTabVisible(indice):
            self.tabs.setCurrentIndex(indice)
            self.actualizar_cabecera_modulo(indice)

            # Cada vez que se abre un módulo se recargan sus datos, para que
            # lo guardado en otros módulos aparezca sin reiniciar la app.
            self._refrescar_modulo(indice)

    def _refrescar_modulo(self, indice):
        metodos = {
            "Especialidades": "actualizar_especialidades",
            "Médicos": "actualizar_medicos",
            "Pacientes": "actualizar_pacientes",
            "Agenda Horarios": "actualizar_agenda",
            "Citas Médicas": "actualizar_citas",
            "Expedientes Clínicos": "actualizar_expedientes",
            "Consultas Historial": "actualizar_consultas",
            "Recetas Médicas": "actualizar_recetas",
            "Detalle Receta": "actualizar_detalle_receta",
            "Medicamentos": "actualizar_medicamentos",
            "Usuarios": "actualizar_usuarios",
        }

        nombre_metodo = metodos.get(self.tabs.tabText(indice))
        actualizar = getattr(self, nombre_metodo, None) if nombre_metodo else None

        if callable(actualizar):
            actualizar()

    def actualizar_cabecera_modulo(self, indice):
        if indice < 0 or indice >= self.tabs.count():
            return

        nombre = self.tabs.tabText(indice)
        self.titulo_modulo.setText(nombre)

        for boton in self.botones_navegacion:
            activo = boton.property("indiceTab") == indice
            boton.setChecked(activo)

    def _ruta_logo(self):
        return Path(__file__).resolve().parent / "recursos" / "logo_medicore.png"

    def mostrar_acerca_de(self):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Acerca de MediCore")
        dialogo.setModal(True)
        dialogo.setStyleSheet("QDialog { background: #F7FAFC; }")

        layout = QVBoxLayout(dialogo)
        layout.setContentsMargins(30, 24, 30, 22)
        layout.setSpacing(14)

        # Logo oficial; si el archivo no está, se usa el logo dibujado.
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pixmap = QPixmap(str(self._ruta_logo()))

        if pixmap.isNull():
            pixmap = self._crear_logo_pixmap(96)
        else:
            escala = dialogo.devicePixelRatioF()
            pixmap = pixmap.scaledToWidth(
                int(340 * escala),
                Qt.TransformationMode.SmoothTransformation
            )
            pixmap.setDevicePixelRatio(escala)

        logo.setPixmap(pixmap)
        layout.addWidget(logo)

        separador = QFrame()
        separador.setFixedHeight(1)
        separador.setStyleSheet("background: #D9E3EC; border: none;")
        layout.addWidget(separador)

        texto = QLabel(
            "<p style='font-size:13px; color:#334A5F;'>"
            "MediCore es una aplicación de escritorio diseñada "
            "para centralizar y organizar la información de un "
            "centro hospitalario. Facilita la gestión de "
            "especialidades médicas, médicos, pacientes, citas, "
            "expedientes clínicos, consultas y medicamentos "
            "desde una sola interfaz."
            "</p>"
            "<p style='font-size:12px; color:#334A5F;'>"
            "<b>Objetivo:</b> mejorar el orden, la consulta y "
            "el seguimiento de la información administrativa "
            "y clínica.</p>"
            "<p style='font-size:11px; color:#718397;'>"
            "Proyecto académico · MediCore</p>"
        )
        texto.setWordWrap(True)
        texto.setMinimumWidth(400)
        texto.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(texto)

        boton = QPushButton("Aceptar")
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.setDefault(True)
        boton.setStyleSheet(
            "QPushButton { background: #1EAA9B; color: #FFFFFF; "
            "border: none; border-radius: 8px; padding: 9px 34px; "
            "font-weight: 700; }"
            "QPushButton:hover { background: #17958A; }"
        )
        boton.clicked.connect(dialogo.accept)
        layout.addWidget(boton, alignment=Qt.AlignmentFlag.AlignCenter)

        dialogo.exec()

    def aplicar_ajustes_visuales(self):
        icono_calendario = _guardar_icono("calendario.png", _dibujar_calendario)
        icono_flecha = _guardar_icono("flecha_abajo.png", _dibujar_flecha)

        # Todos los campos de fecha abren el calendario con el botón.
        for campo in self.findChildren(QDateEdit):
            campo.setCalendarPopup(True)
            if not campo.toolTip():
                campo.setToolTip("Escribe la fecha o pulsa el botón del calendario para elegirla")

        css = f"""
        /* ---- Cuadros de mensaje más grandes ---- */
        QMessageBox QLabel {{
            color: #25364A;
            font-size: 11pt;
        }}

        QMessageBox QLabel#qt_msgbox_label,
        QMessageBox QLabel#qt_msgbox_informativelabel {{
            min-width: 480px;
            min-height: 48px;
        }}

        QMessageBox QPushButton {{
            min-width: 110px;
            min-height: 22px;
            padding: 8px 20px;
        }}

        /* ---- Botón de calendario visible ---- */
        QDateEdit::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: center right;
            width: 36px;
            border: none;
            border-left: 1px solid #94A3B8;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            background: #E6F4F1;
        }}

        QDateEdit::drop-down:hover {{
            background: #CDEBE4;
        }}

        QDateEdit::down-arrow {{
            image: url({icono_calendario});
            width: 20px;
            height: 20px;
        }}

        /* ---- Área de módulos y barras de desplazamiento ---- */
        QScrollArea#scrollModulos,
        QScrollArea#scrollModulos > QWidget#qt_scrollarea_viewport {{
            background: transparent;
            border: none;
        }}

        /* La barra vertical de las tablas empieza debajo del encabezado */
        QTableWidget QScrollBar:vertical {{
            margin: 50px 2px 2px 2px;
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
            border: none;
            background: none;
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
            border: none;
            background: none;
        }}

        QScrollBar::add-page, QScrollBar::sub-page {{
            background: none;
        }}

        /* ---- Flecha visible en listas desplegables ---- */
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: center right;
            width: 30px;
            border: none;
            border-left: 1px solid #CBD5E1;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
        }}

        QComboBox::down-arrow {{
            image: url({icono_flecha});
            width: 16px;
            height: 16px;
        }}
        """

        self.setStyleSheet(self.styleSheet() + css)

    def aplicar_estilos(self):
        self.setStyleSheet("""
        * {
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 10pt;
        }

        QMainWindow, QWidget#contenedorPrincipal {
            background: #F3F6FA;
            color: #25364A;
        }

        QFrame#panelLateral {
            background: #142D45;
            border: none;
        }

        QLabel#logoMarca {
            background: #1EAA9B;
            color: #FFFFFF;
            border-radius: 13px;
            font-size: 25pt;
            font-weight: 800;
        }

        QLabel#nombreMarca {
            color: #FFFFFF;
            font-size: 17pt;
            font-weight: 800;
            padding: 0px;
            margin: 0px;
        }

        QLabel#lemaMarca {
            color: #A9C2D5;
            font-size: 7pt;
            font-weight: 700;
            padding: 0px;
            margin: 0px;
        }

        QFrame#separadorLateral {
            background: #2B455B;
            border: none;
            margin-top: 12px;
            margin-bottom: 4px;
        }

        QLabel#etiquetaMenu, QLabel#etiquetaGrupo {
            color: #88A5BB;
            font-size: 8pt;
            font-weight: 700;
            padding-left: 8px;
        }

        QPushButton#botonNavegacion {
            text-align: left;
            color: #D5E2EC;
            background: transparent;
            border: 1px solid transparent;
            border-radius: 9px;
            padding: 12px;
            min-height: 20px;
            font-weight: 600;
        }

        QPushButton#botonNavegacion:hover {
            background: #203F58;
            color: #FFFFFF;
        }

        QPushButton#botonNavegacion:checked {
            background: #1EAA9B;
            color: #FFFFFF;
            border: 1px solid #35C4B4;
        }

        QScrollArea#scrollMenuLateral,
        QScrollArea#scrollMenuLateral > QWidget > QWidget,
        QWidget#contenidoMenuLateral {
            background: transparent;
            border: none;
        }

        QScrollArea#scrollMenuLateral QScrollBar:vertical {
            background: transparent;
            width: 6px;
            margin: 2px 0px;
            border-radius: 3px;
        }

        QScrollArea#scrollMenuLateral QScrollBar::handle:vertical {
            background: #3C5C75;
            min-height: 28px;
            border-radius: 3px;
        }

        QScrollArea#scrollMenuLateral QScrollBar::handle:vertical:hover {
            background: #5C8199;
        }

        QScrollArea#scrollMenuLateral QScrollBar::add-line:vertical,
        QScrollArea#scrollMenuLateral QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QFrame#tarjetaUsuario {
            background: #1B3A52;
            border: 1px solid #31536B;
            border-radius: 12px;
        }

        QLabel#usuarioTitulo {
            color: #FFFFFF;
            font-weight: 700;
        }

        QLabel#usuarioSubtitulo {
            color: #A9C2D5;
            font-size: 8pt;
        }

        QWidget#zonaContenido {
            background: #F3F6FA;
        }

        QFrame#cabeceraContenido {
            background: transparent;
            border: none;
            border-bottom: 1px solid #DCE5ED;
        }

        QLabel#tituloModulo {
            color: #183A53;
            font-size: 23pt;
            font-weight: 800;
        }

        QLabel#subtituloModulo {
            color: #788A9C;
            font-size: 9pt;
        }

        QPushButton#botonCerrarSesion {
            background: #FDECEA;
            color: #B23A2E;
            border: 1px solid #F5C6C0;
            border-radius: 12px;
            padding: 9px 18px;
            min-width: 110px;
            font-size: 9pt;
            font-weight: 700;
        }

        QPushButton#botonCerrarSesion:hover {
            background: #F9D6D2;
            border-color: #EBA9A1;
        }

        QPushButton#botonCerrarSesion:pressed {
            background: #F2BFB9;
        }

        QTabWidget#areaModulos::pane {
            background: #FFFFFF;
            border: 1px solid #E1E8EF;
            border-radius: 16px;
            top: 0;
        }

        QTabWidget#areaModulos > QWidget {
            background: #FFFFFF;
            border-radius: 16px;
        }

        /* CAMPOS DE TEXTO */
        QLineEdit {
            background-color: #FFFFFF;
            color: #1E293B;
            border: 1px solid #94A3B8;
            border-radius: 6px;
            padding: 8px 10px;
            min-height: 24px;
            min-width: 180px;
            selection-background-color: #0D9488;
            selection-color: #FFFFFF;
        }

        QLineEdit:hover {
            border: 1px solid #64748B;
        }

        QLineEdit:focus {
            background-color: #FFFFFF;
            color: #1E293B;
            border: 2px solid #0D9488;
        }

        QLineEdit:disabled {
            background-color: #E2E8F0;
            color: #64748B;
            border: 1px solid #CBD5E1;
        }

        /* COMBOS, FECHAS Y HORAS */
        QComboBox, QDateEdit, QTimeEdit, QDateTimeEdit,
        QSpinBox, QDoubleSpinBox {
            background-color: #FFFFFF;
            color: #1E293B;
            border: 1px solid #94A3B8;
            border-radius: 6px;
            padding: 8px 10px;
            min-height: 24px;
            min-width: 180px;
        }

        QComboBox:hover, QDateEdit:hover, QTimeEdit:hover,
        QDateTimeEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {
            border: 1px solid #64748B;
        }

        QComboBox:focus, QDateEdit:focus, QTimeEdit:focus,
        QDateTimeEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            background-color: #FFFFFF;
            border: 2px solid #0D9488;
        }

        QComboBox:disabled, QDateEdit:disabled, QTimeEdit:disabled,
        QDateTimeEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
            background-color: #E2E8F0;
            color: #64748B;
        }

        QComboBox::drop-down, QDateEdit::drop-down,
        QTimeEdit::drop-down, QDateTimeEdit::drop-down {
            border: none;
            width: 28px;
        }

        QComboBox QAbstractItemView {
            background-color: #FFFFFF;
            color: #1E293B;
            border: 1px solid #94A3B8;
            selection-background-color: #DDF5F0;
            selection-color: #164D4B;
            padding: 5px;
        }

        /* CAMPOS MULTILÍNEA */
        QTextEdit, QPlainTextEdit {
            background-color: #FFFFFF;
            color: #1E293B;
            border: 1px solid #94A3B8;
            border-radius: 6px;
            padding: 8px;
            min-height: 66px;
            selection-background-color: #0D9488;
            selection-color: #FFFFFF;
        }

        QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #0D9488;
        }

        /* ETIQUETAS DE LOS FORMULARIOS */
        QFormLayout QLabel {
            color: #26384B;
            min-width: 145px;
            padding: 2px 0px;
            font-size: 10pt;
            font-weight: 600;
        }

        /* BOTONES */
        QPushButton {
            background: #EAF0F5;
            color: #334A5F;
            border: 1px solid #D8E2EB;
            border-radius: 8px;
            padding: 10px 17px;
            min-width: 82px;
            font-weight: 700;
        }

        QPushButton:hover {
            background: #DCE9F1;
            border-color: #B8CBD8;
        }

        QPushButton:pressed {
            background: #C9DBE6;
        }

        QPushButton:focus {
            border: 1px solid #20A99B;
        }

        /* TABLAS */
        QTableWidget {
            background: #FFFFFF;
            alternate-background-color: #F7FAFC;
            color: #2A3D50;
            border: 1px solid #E1E8EF;
            border-radius: 10px;
            gridline-color: #EAF0F5;
            selection-background-color: #DDF5F0;
            selection-color: #164D4B;
            outline: none;
        }

        QTableWidget::item {
            padding: 8px;
            border: none;
        }

        QTableWidget::item:selected {
            background: #DDF5F0;
            color: #164D4B;
        }

        QHeaderView::section {
            background: #EDF3F7;
            color: #385168;
            border: none;
            border-bottom: 2px solid #D4E4EA;
            padding: 12px 8px;
            font-weight: 800;
        }

        /* BARRAS DE DESPLAZAMIENTO */
        QScrollBar:vertical {
            background: #F0F4F7;
            width: 11px;
            margin: 2px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical {
            background: #BDCEDA;
            min-height: 28px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical:hover {
            background: #8FAABB;
        }

        QScrollBar:horizontal {
            background: #F0F4F7;
            height: 11px;
            margin: 2px;
            border-radius: 5px;
        }

        QScrollBar::handle:horizontal {
            background: #BDCEDA;
            min-width: 28px;
            border-radius: 5px;
        }

        QMessageBox {
            background: #F7FAFC;
        }

        QMessageBox QLabel {
            color: #25364A;
        }

        QMessageBox QLabel#qt_msgbox_label {
            min-width: 250px;
        }

        QMessageBox QLabel#qt_msgboxex_icon_label {
            min-width: 0px;
            padding-right: 10px;
        }

        QMessageBox QPushButton {
            min-width: 80px;
        }

        QToolTip {
            background: #17344C;
            color: #FFFFFF;
            border: 1px solid #36566D;
            padding: 7px;
            border-radius: 5px;
        }
        """)

        self.aplicar_ajustes_visuales()

        for tabla in self.findChildren(QTableWidget):
            tabla.setAlternatingRowColors(True)
            tabla.setShowGrid(False)
            tabla.setWordWrap(False)

            tabla.setSelectionBehavior(
                QTableWidget.SelectionBehavior.SelectRows
            )
            tabla.setSelectionMode(
                QTableWidget.SelectionMode.SingleSelection
            )

            tabla.verticalHeader().setVisible(False)
            tabla.verticalHeader().setDefaultSectionSize(38)
            tabla.horizontalHeader().setMinimumSectionSize(90)

            tabla.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )
            tabla.horizontalHeader().setStretchLastSection(True)
            tabla.setMinimumHeight(220)

        for tab in self.findChildren(QWidget):
            if tab.layout() and isinstance(tab.layout(), QVBoxLayout):
                tab.layout().setContentsMargins(20, 20, 20, 20)
                tab.layout().setSpacing(14)