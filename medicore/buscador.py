import unicodedata

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton
)

# Rol de datos extra (texto buscable que no se ve en la celda).
ROL_TEXTO_BUSQUEDA = Qt.ItemDataRole.UserRole + 50

TODOS = "Todos los campos"

# (nombre de la pestaña, atributo de la tabla, texto de ayuda del buscador)
MODULOS_BUSCABLES = [
    ("Especialidades", "tabla_especialidades", "Buscar especialidad..."),
    ("Médicos", "tabla_medicos", "Buscar por nombre del médico, código MINSA o especialidad..."),
    ("Pacientes", "tabla_pacientes", "Buscar por nombre o cédula del paciente..."),
    ("Agenda Horarios", "tabla_agenda", "Buscar por nombre del médico o día..."),
    ("Citas Médicas", "tabla_citas", "Buscar por nombre del paciente o del médico..."),
    ("Consultas Historial", "tabla_consultas", "Buscar por paciente, médico o diagnóstico..."),
    ("Expedientes Clínicos", "tabla_expedientes", "Buscar por nombre del paciente..."),
    ("Recetas Médicas", "tabla_recetas", "Buscar por nombre del paciente..."),
    ("Medicamentos", "tabla_medicamentos", "Buscar por nombre del medicamento..."),
    ("Detalle Receta", "tabla_detalle_receta", "Buscar por paciente, medicamento o número de receta..."),
]

ESTILO_BARRA = """
    QFrame#barraBusqueda {
        background: #F3F8FA;
        border: 1px solid #D5E3EA;
        border-radius: 10px;
    }
    QFrame#barraBusqueda QLineEdit {
        min-width: 260px;
        min-height: 22px;
        padding: 6px 10px;
        border: 1px solid #B6C9D6;
        border-radius: 8px;
        background: #FFFFFF;
    }
    QFrame#barraBusqueda QLineEdit:focus { border: 2px solid #1EAA9B; }
    QFrame#barraBusqueda QComboBox {
        min-width: 150px;
        min-height: 22px;
        padding: 6px 10px;
        border-radius: 8px;
    }
    QFrame#barraBusqueda QPushButton { padding: 8px 14px; min-width: 70px; }
    QFrame#barraBusqueda QPushButton#botonBuscar {
        background: #1EAA9B; color: #FFFFFF; border: 1px solid #17958A;
    }
    QFrame#barraBusqueda QPushButton#botonBuscar:hover { background: #17958A; }
    QFrame#barraBusqueda QLabel {
        background: transparent; color: #4F6A7F; font-weight: 600;
    }
    QFrame#barraBusqueda QLabel#contadorBusqueda { min-width: 110px; }
"""


def normalizar(texto):
    """Minúsculas y sin tildes para comparar textos."""
    texto = unicodedata.normalize("NFD", str(texto or ""))
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.casefold()


class BarraBusqueda(QFrame):
    """Barra de búsqueda enlazada a un QTableWidget."""

    def __init__(self, tabla, ayuda, parent=None):
        super().__init__(parent)
        self.tabla = tabla
        self.setObjectName("barraBusqueda")
        self.setStyleSheet(ESTILO_BARRA)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        layout.addWidget(QLabel("🔍"))

        self.campo = QLineEdit()
        self.campo.setPlaceholderText(ayuda)
        self.campo.setClearButtonEnabled(True)
        layout.addWidget(self.campo, 1)

        layout.addWidget(QLabel("Buscar en:"))

        self.combo_columna = QComboBox()
        self.combo_columna.addItem(TODOS, -1)
        for columna in range(tabla.columnCount()):
            item = tabla.horizontalHeaderItem(columna)
            if item is not None:
                self.combo_columna.addItem(item.text(), columna)
        layout.addWidget(self.combo_columna)

        self.boton_buscar = QPushButton("Buscar")
        self.boton_buscar.setObjectName("botonBuscar")
        self.boton_buscar.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.boton_buscar)

        self.boton_limpiar = QPushButton("Limpiar")
        self.boton_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.boton_limpiar)

        self.contador = QLabel("")
        self.contador.setObjectName("contadorBusqueda")
        layout.addWidget(self.contador)

        # Reaplicar el filtro cuando la tabla se recarga.
        self._temporizador = QTimer(self)
        self._temporizador.setSingleShot(True)
        self._temporizador.setInterval(0)
        self._temporizador.timeout.connect(self.filtrar)

        def reprogramar(*_):
            self._temporizador.start()

        modelo = tabla.model()
        modelo.rowsInserted.connect(reprogramar)
        modelo.rowsRemoved.connect(reprogramar)
        modelo.modelReset.connect(reprogramar)

        self.campo.textChanged.connect(self.filtrar)
        self.campo.returnPressed.connect(self.filtrar)
        self.combo_columna.currentIndexChanged.connect(self.filtrar)
        self.boton_buscar.clicked.connect(self.filtrar)
        self.boton_limpiar.clicked.connect(self.limpiar)

    def limpiar(self):
        self.campo.clear()
        self.combo_columna.setCurrentIndex(0)
        self.filtrar()
        self.campo.setFocus()

    def _texto_celda(self, fila, columna):
        item = self.tabla.item(fila, columna)
        if item is None:
            return ""
        extra = item.data(ROL_TEXTO_BUSQUEDA)
        return f"{item.text()} {extra}" if extra else item.text()

    def filtrar(self, *_):
        terminos = normalizar(self.campo.text()).split()
        columna = self.combo_columna.currentData()
        total = self.tabla.rowCount()
        visibles = 0

        for fila in range(total):
            if not terminos:
                coincide = True
            else:
                if columna is None or columna < 0:
                    columnas = range(self.tabla.columnCount())
                else:
                    columnas = (columna,)
                texto = normalizar(
                    " ".join(self._texto_celda(fila, c) for c in columnas)
                )
                coincide = all(t in texto for t in terminos)

            self.tabla.setRowHidden(fila, not coincide)
            visibles += 1 if coincide else 0

        if not terminos:
            self.contador.setText(f"{total} registros")
            self.contador.setStyleSheet("")
        elif visibles == 0:
            self.contador.setText("Sin resultados")
            self.contador.setStyleSheet("color: #C0392B;")
        else:
            self.contador.setText(f"{visibles} de {total}")
            self.contador.setStyleSheet("")


class BuscadorMixin:
    """Instala una barra de búsqueda en cada módulo con tabla."""

    def crear_interfaz(self):
        super().crear_interfaz()
        self._instalar_buscadores()

    def _instalar_buscadores(self):
        self.barras_busqueda = {}

        for nombre_tab, atributo, ayuda in MODULOS_BUSCABLES:
            tabla = getattr(self, atributo, None)
            indice = self._buscar_indice_tab(nombre_tab)
            if tabla is None or indice < 0:
                continue

            pagina = self.tabs.widget(indice)
            layout = pagina.layout() if pagina is not None else None
            if layout is None:
                continue

            posicion = layout.indexOf(tabla)
            if posicion < 0:
                continue

            barra = BarraBusqueda(tabla, ayuda)
            layout.insertWidget(posicion, barra)
            self.barras_busqueda[nombre_tab] = barra
            barra.filtrar()

        # Ctrl+F enfoca el buscador del módulo abierto.
        self._atajo_buscar = QShortcut(QKeySequence("Ctrl+F"), self)
        self._atajo_buscar.activated.connect(self._enfocar_buscador)

    def _enfocar_buscador(self):
        nombre = self.tabs.tabText(self.tabs.currentIndex())
        barra = getattr(self, "barras_busqueda", {}).get(nombre)
        if barra is not None:
            barra.campo.setFocus()
            barra.campo.selectAll()