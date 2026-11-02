from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)
from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPointF,
    QPropertyAnimation,
    Qt,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPixmap,
)

from .autenticacion import autenticar_usuario


ESTILOS_LOGIN = """
    * {
        font-family: "Segoe UI", Arial, sans-serif;
    }

    QDialog {
        background: #EEF3F7;
    }

    /* ---------- Panel de marca (izquierda) ---------- */
    QFrame#tarjetaLogo {
        background: #FFFFFF;
        border-radius: 20px;
    }

    QLabel#marcaTitulo {
        color: #FFFFFF;
        font-size: 30px;
        font-weight: 800;
    }

    QLabel#marcaTexto {
        color: #B9CEDD;
        font-size: 15px;
    }

    QLabel#marcaItem {
        color: #E1EBF2;
        font-size: 14px;
    }

    QLabel#marcaCheck {
        color: #FFFFFF;
        background: #1EAA9B;
        border-radius: 11px;
        font-size: 12px;
        font-weight: 700;
    }

    QLabel#marcaPie {
        color: #86A2B8;
        font-size: 12px;
    }

    /* ---------- Panel del formulario (derecha) ---------- */
    QFrame#panelFormulario {
        background: #EEF3F7;
    }

    QFrame#tarjetaFormulario {
        background: #FFFFFF;
        border-radius: 22px;
    }

    QLabel#fechaLogin {
        color: #7A8CA0;
        font-size: 12px;
    }

    QLabel#sobretitulo {
        color: #168575;
        font-size: 12px;
        font-weight: 700;
    }

    QLabel#tituloLogin {
        color: #183A53;
        font-size: 32px;
        font-weight: 800;
    }

    QLabel#subtituloLogin {
        color: #62748A;
        font-size: 14px;
    }

    QLabel#etiquetaCampo {
        color: #25364A;
        font-size: 13px;
        font-weight: 600;
    }

    QLineEdit {
        background: #F7FAFC;
        border: 1px solid #D5DFE8;
        border-radius: 10px;
        padding: 12px 14px;
        font-size: 15px;
        color: #1E293B;
    }

    QLineEdit:hover {
        border: 1px solid #A9BBCB;
    }

    QLineEdit:focus {
        background: #FFFFFF;
        border: 2px solid #1EAA9B;
        padding: 11px 13px;
    }

    /* Campo marcado como erróneo */
    QLineEdit[error="true"] {
        background: #FFF8F7;
        border: 2px solid #F04438;
        padding: 11px 13px;
    }

    QCheckBox {
        color: #4A5C70;
        font-size: 13px;
        spacing: 8px;
    }

    QLabel#errorLogin {
        color: #B42318;
        background: #FEF3F2;
        border: 1px solid #FDA29B;
        border-left: 5px solid #F04438;
        border-radius: 10px;
        padding: 11px 14px;
        font-size: 13px;
        font-weight: 600;
    }

    QPushButton#botonIngresar {
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 0,
            stop: 0 #1EAA9B, stop: 1 #168575
        );
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 14px;
        font-size: 15px;
        font-weight: 700;
    }

    QPushButton#botonIngresar:hover {
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 0,
            stop: 0 #17958A, stop: 1 #127D73
        );
    }

    QPushButton#botonIngresar:pressed {
        background: #0F6A62;
    }

    QPushButton#botonIngresar:disabled {
        background: #9FD6CF;
    }

    QLabel#pieLogin {
        color: #8896A6;
        font-size: 12px;
    }
"""


class PanelMarca(QFrame):
    """Panel izquierdo con degradado y círculos decorativos."""

    def paintEvent(self, evento):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)

        ancho = self.width()
        alto = self.height()

        degradado = QLinearGradient(0, 0, ancho, alto)
        degradado.setColorAt(0.0, QColor("#0F2438"))
        degradado.setColorAt(0.55, QColor("#17445C"))
        degradado.setColorAt(1.0, QColor("#1B6A74"))
        pintor.fillRect(self.rect(), QBrush(degradado))

        pintor.setPen(Qt.PenStyle.NoPen)

        # Círculos translúcidos de adorno.
        pintor.setBrush(QColor(255, 255, 255, 14))
        pintor.drawEllipse(QPointF(ancho * 0.95, alto * 0.08), 190, 190)

        pintor.setBrush(QColor(30, 170, 155, 38))
        pintor.drawEllipse(QPointF(ancho * 0.05, alto * 0.92), 240, 240)

        pintor.setBrush(QColor(255, 255, 255, 10))
        pintor.drawEllipse(QPointF(ancho * 0.85, alto * 0.78), 120, 120)

        pintor.end()


class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.usuario_autenticado = None
        self._animacion = None

        self.setWindowTitle("MediCore - Inicio de sesión")
        self.setMinimumSize(980, 620)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setStyleSheet(ESTILOS_LOGIN)

        self.crear_interfaz()

        # El login ocupa toda la pantalla disponible.
        self.setWindowState(Qt.WindowState.WindowMaximized)

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def crear_interfaz(self):
        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        raiz.addWidget(self._crear_panel_marca(), 5)
        raiz.addWidget(self._crear_panel_formulario(), 6)

        self.campo_usuario.setFocus()

    def _ruta_logo(self):
        return Path(__file__).resolve().parent / "logo_medicore.png"

    def _crear_panel_marca(self):
        panel = PanelMarca()
        panel.setMinimumWidth(420)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(70, 50, 70, 34)
        layout.setSpacing(0)

        # Tarjeta blanca con el logo (el logo tiene texto azul oscuro,
        # por eso necesita un fondo claro).
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaLogo")
        tarjeta.setMaximumWidth(400)

        sombra = QGraphicsDropShadowEffect(tarjeta)
        sombra.setBlurRadius(40)
        sombra.setOffset(0, 10)
        sombra.setColor(QColor(0, 0, 0, 90))
        tarjeta.setGraphicsEffect(sombra)

        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(24, 26, 24, 26)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pixmap = QPixmap(str(self._ruta_logo()))

        if pixmap.isNull():
            logo.setText("MediCore")
            logo.setStyleSheet(
                "color: #183A53; font-size: 34px; font-weight: 800;"
            )
        else:
            escala = self.devicePixelRatioF()
            pixmap = pixmap.scaledToWidth(
                int(330 * escala),
                Qt.TransformationMode.SmoothTransformation
            )
            pixmap.setDevicePixelRatio(escala)
            logo.setPixmap(pixmap)

        layout_tarjeta.addWidget(logo)

        titulo = QLabel("Gestión clínica en un solo lugar")
        titulo.setObjectName("marcaTitulo")
        titulo.setWordWrap(True)

        texto = QLabel(
            "Pacientes, citas, expedientes, consultas y recetas "
            "organizados de forma segura y centralizada."
        )
        texto.setObjectName("marcaTexto")
        texto.setWordWrap(True)

        layout.addStretch(2)
        layout.addWidget(tarjeta, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addSpacing(40)
        layout.addWidget(titulo)
        layout.addSpacing(12)
        layout.addWidget(texto)
        layout.addSpacing(26)

        for beneficio in (
            "Acceso según el rol de cada usuario",
            "Información médica centralizada",
            "Seguimiento clínico ordenado",
            "Recetas exportables en PDF",
        ):
            fila = QHBoxLayout()
            fila.setSpacing(12)

            marca = QLabel("✓")
            marca.setObjectName("marcaCheck")
            marca.setFixedSize(22, 22)
            marca.setAlignment(Qt.AlignmentFlag.AlignCenter)

            item = QLabel(beneficio)
            item.setObjectName("marcaItem")

            fila.addWidget(marca)
            fila.addWidget(item, 1)

            layout.addLayout(fila)
            layout.addSpacing(10)

        layout.addStretch(3)

        pie = QLabel("© 2026 MediCore · Proyecto académico")
        pie.setObjectName("marcaPie")
        layout.addWidget(pie)

        return panel

    def _saludo(self):
        hora = datetime.now().hour

        if hora < 12:
            return "BUENOS DÍAS"
        if hora < 19:
            return "BUENAS TARDES"
        return "BUENAS NOCHES"

    def _fecha_texto(self):
        dias = (
            "lunes", "martes", "miércoles", "jueves",
            "viernes", "sábado", "domingo"
        )
        meses = (
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre",
            "diciembre"
        )
        hoy = datetime.now()

        return (
            f"{dias[hoy.weekday()].capitalize()}, {hoy.day} de "
            f"{meses[hoy.month - 1]} de {hoy.year}"
        )

    def _crear_panel_formulario(self):
        panel = QFrame()
        panel.setObjectName("panelFormulario")

        externo = QVBoxLayout(panel)
        externo.setContentsMargins(30, 30, 30, 24)
        externo.setSpacing(0)

        fecha = QLabel(self._fecha_texto())
        fecha.setObjectName("fechaLogin")
        fecha.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Tarjeta blanca centrada que contiene el formulario.
        self.tarjeta_formulario = QFrame()
        self.tarjeta_formulario.setObjectName("tarjetaFormulario")
        self.tarjeta_formulario.setFixedWidth(470)

        sombra = QGraphicsDropShadowEffect(self.tarjeta_formulario)
        sombra.setBlurRadius(50)
        sombra.setOffset(0, 12)
        sombra.setColor(QColor(24, 58, 83, 45))
        self.tarjeta_formulario.setGraphicsEffect(sombra)

        layout = QVBoxLayout(self.tarjeta_formulario)
        layout.setContentsMargins(44, 42, 44, 36)
        layout.setSpacing(0)

        sobretitulo = QLabel(self._saludo())
        sobretitulo.setObjectName("sobretitulo")

        titulo = QLabel("Iniciar sesión")
        titulo.setObjectName("tituloLogin")

        subtitulo = QLabel("Ingresa tus credenciales para continuar.")
        subtitulo.setObjectName("subtituloLogin")

        etiqueta_usuario = QLabel("Nombre de usuario")
        etiqueta_usuario.setObjectName("etiquetaCampo")

        self.campo_usuario = QLineEdit()
        self.campo_usuario.setPlaceholderText("Introduce tu usuario")

        etiqueta_contrasena = QLabel("Contraseña")
        etiqueta_contrasena.setObjectName("etiquetaCampo")

        self.campo_contrasena = QLineEdit()
        self.campo_contrasena.setPlaceholderText("Introduce tu contraseña")
        self.campo_contrasena.setEchoMode(QLineEdit.EchoMode.Password)

        self.mostrar_contrasena = QCheckBox("Mostrar contraseña")
        self.mostrar_contrasena.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mostrar_contrasena.toggled.connect(self._alternar_contrasena)

        self.etiqueta_error = QLabel("")
        self.etiqueta_error.setObjectName("errorLogin")
        self.etiqueta_error.setWordWrap(True)
        self.etiqueta_error.hide()

        self.boton_ingresar = QPushButton("Ingresar")
        self.boton_ingresar.setObjectName("botonIngresar")
        self.boton_ingresar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_ingresar.setDefault(True)
        self.boton_ingresar.clicked.connect(self.iniciar_sesion)

        self.campo_usuario.returnPressed.connect(
            self.campo_contrasena.setFocus
        )
        self.campo_contrasena.returnPressed.connect(self.iniciar_sesion)

        # Al volver a escribir se limpia el mensaje de error.
        self.campo_usuario.textChanged.connect(self._ocultar_error)
        self.campo_contrasena.textChanged.connect(self._ocultar_error)

        pie = QLabel("🔒  Acceso autorizado al sistema")
        pie.setObjectName("pieLogin")
        pie.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(sobretitulo)
        layout.addSpacing(4)
        layout.addWidget(titulo)
        layout.addSpacing(6)
        layout.addWidget(subtitulo)
        layout.addSpacing(28)
        layout.addWidget(etiqueta_usuario)
        layout.addSpacing(6)
        layout.addWidget(self.campo_usuario)
        layout.addSpacing(16)
        layout.addWidget(etiqueta_contrasena)
        layout.addSpacing(6)
        layout.addWidget(self.campo_contrasena)
        layout.addSpacing(12)
        layout.addWidget(self.mostrar_contrasena)
        layout.addSpacing(14)
        layout.addWidget(self.etiqueta_error)
        layout.addSpacing(14)
        layout.addWidget(self.boton_ingresar)
        layout.addSpacing(22)
        layout.addWidget(pie)

        externo.addWidget(fecha)
        externo.addStretch(1)
        externo.addWidget(
            self.tarjeta_formulario, 0, Qt.AlignmentFlag.AlignHCenter
        )
        externo.addStretch(1)

        return panel

    # ------------------------------------------------------------------
    # Comportamiento
    # ------------------------------------------------------------------
    def _alternar_contrasena(self, visible):
        self.campo_contrasena.setEchoMode(
            QLineEdit.EchoMode.Normal
            if visible
            else QLineEdit.EchoMode.Password
        )

    def _marcar_campo(self, campo, con_error):
        campo.setProperty("error", "true" if con_error else "false")
        campo.style().unpolish(campo)
        campo.style().polish(campo)

    def _mostrar_error(self, mensaje, campos=()):
        self.etiqueta_error.setText("⚠  " + mensaje)
        self.etiqueta_error.show()

        for campo in campos:
            self._marcar_campo(campo, True)

        self._animar_sacudida()

    def _ocultar_error(self, *_):
        # Se oculta siempre, sin depender de isVisible(), para que el
        # mensaje desaparezca en cuanto el usuario vuelve a escribir.
        self.etiqueta_error.hide()
        self._marcar_campo(self.campo_usuario, False)
        self._marcar_campo(self.campo_contrasena, False)

    def _animar_sacudida(self):
        """Pequeña sacudida horizontal de la tarjeta al fallar el acceso."""
        tarjeta = self.tarjeta_formulario
        origen = tarjeta.pos()

        animacion = QPropertyAnimation(tarjeta, b"pos", self)
        animacion.setDuration(380)
        animacion.setKeyValueAt(0.0, origen)
        animacion.setKeyValueAt(0.15, origen + QPoint(-12, 0))
        animacion.setKeyValueAt(0.35, origen + QPoint(10, 0))
        animacion.setKeyValueAt(0.55, origen + QPoint(-7, 0))
        animacion.setKeyValueAt(0.75, origen + QPoint(4, 0))
        animacion.setKeyValueAt(1.0, origen)
        animacion.setEasingCurve(QEasingCurve.Type.OutQuad)
        animacion.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

        self._animacion = animacion

    def iniciar_sesion(self):
        nombre_usuario = self.campo_usuario.text().strip()
        contrasena = self.campo_contrasena.text()

        if not nombre_usuario or not contrasena:
            campos_vacios = []

            if not nombre_usuario:
                campos_vacios.append(self.campo_usuario)
            if not contrasena:
                campos_vacios.append(self.campo_contrasena)

            self._mostrar_error(
                "Introduce tu usuario y contraseña.",
                campos_vacios
            )
            campos_vacios[0].setFocus()
            return

        self._ocultar_error()
        self.boton_ingresar.setEnabled(False)
        self.boton_ingresar.setText("Verificando...")
        QApplication.processEvents()

        try:
            usuario = autenticar_usuario(
                nombre_usuario,
                contrasena
            )

            if usuario is None:
                # Primero se limpia la contraseña (esto dispara
                # textChanged y oculta errores) y DESPUÉS se muestra el
                # mensaje, para que no desaparezca al instante.
                self.campo_contrasena.clear()
                self.campo_contrasena.setFocus()

                self._mostrar_error(
                    "Usuario o contraseña incorrectos, "
                    "o la cuenta está inactiva.",
                    (self.campo_usuario, self.campo_contrasena)
                )
                return

            self.usuario_autenticado = usuario
            self.accept()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo iniciar sesión:\n{error}"
            )

        finally:
            self.boton_ingresar.setEnabled(True)
            self.boton_ingresar.setText("Ingresar")
