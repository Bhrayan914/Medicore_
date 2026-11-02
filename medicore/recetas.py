
from .common import *
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtWidgets import QSizePolicy

class RecetasMixin:
    def crear_recetas(self):
        pestaña = QWidget()
        layout = QVBoxLayout(pestaña)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(12)

        formulario = QFormLayout()
        formulario.setContentsMargins(5, 5, 5, 10)
        formulario.setHorizontalSpacing(18)
        formulario.setVerticalSpacing(12)
        formulario.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        formulario.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )

        etiqueta_consulta = QLabel("Consulta:")
        etiqueta_consulta.setStyleSheet("""
            QLabel {
                color: #222222;
                background-color: transparent;
                font-size: 13px;
                font-weight: bold;
            }
        """)

        self.consulta_receta = QComboBox()
        self.consulta_receta.addItem("Seleccionar consulta")
        self.consulta_receta.setMinimumHeight(38)
        self.consulta_receta.setMinimumWidth(250)
        self.consulta_receta.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        self.consulta_receta.setStyleSheet("estilo_campo")

        formulario.addRow(etiqueta_consulta, self.consulta_receta)

        etiqueta_fecha = QLabel("Fecha de emisión:")
        etiqueta_fecha.setStyleSheet("""
            QLabel {
                color: #222222;
                background-color: transparent;
                font-size: 13px;
                font-weight: bold;
            }
        """)

        self.fecha_receta = QDateEdit()
        self.fecha_receta.setCalendarPopup(True)
        self.fecha_receta.setDate(QDate.currentDate())
        self.fecha_receta.setDisplayFormat("dd/MM/yyyy")
        self.fecha_receta.setMinimumHeight(38)
        self.fecha_receta.setMinimumWidth(200)
        self.fecha_receta.setStyleSheet("estilo_campo")

        formulario.addRow(etiqueta_fecha, self.fecha_receta)

        layout.addLayout(formulario)

        botones = QHBoxLayout()
        botones.setSpacing(8)

        btn_guardar = QPushButton("Guardar")
        btn_editar = QPushButton("Editar")
        btn_eliminar = QPushButton("Eliminar")
        btn_limpiar = QPushButton("Limpiar")

        btn_guardar.clicked.connect(self.guardar_receta)
        btn_editar.clicked.connect(self.editar_receta)
        btn_eliminar.clicked.connect(self.eliminar_receta)
        btn_limpiar.clicked.connect(self.limpiar_receta)

        for boton in (
            btn_guardar,
            btn_editar,
            btn_eliminar,
            btn_limpiar
        ):
            boton.setMinimumHeight(36)
            botones.addWidget(boton)

        layout.addLayout(botones)

        self.tabla_recetas = QTableWidget()
        self.tabla_recetas.setColumnCount(3)
        self.tabla_recetas.setHorizontalHeaderLabels([
            "ID Receta",
            "Consulta",
            "Fecha emisión"
        ])

        self.tabla_recetas.setAlternatingRowColors(True)
        self.tabla_recetas.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tabla_recetas.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tabla_recetas.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.tabla_recetas.cellClicked.connect(
            self.seleccionar_receta
        )

        layout.addWidget(self.tabla_recetas)

        self.tabs.addTab(pestaña, "Recetas Médicas")

    def limpiar_receta(self):
        self.consulta_receta.setCurrentIndex(0)
        self.fecha_receta.setDate(QDate.currentDate())
        self.tabla_recetas.clearSelection()
