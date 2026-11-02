from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QFormLayout, QGridLayout, QTabWidget, QLabel, QLineEdit, QPushButton, QComboBox,
    QDateEdit, QTimeEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QDoubleSpinBox, QSpinBox, QHeaderView, QScrollArea
)
from PySide6.QtCore import QDate, QTime, Qt



class FormularioCompacto(QGridLayout):
    """Formulario en dos columnas de campos para reducir el espacio vertical."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._indice_campo = 0
        self._fila_actual = 0
        self.setContentsMargins(0, 0, 0, 8)
        self.setHorizontalSpacing(14)
        self.setVerticalSpacing(8)
        self.setColumnStretch(1, 1)
        self.setColumnStretch(3, 1)

    # Compatibilidad con las llamadas usadas anteriormente con QFormLayout.
    def setLabelAlignment(self, *args):
        pass

    def setFieldGrowthPolicy(self, *args):
        pass

    def addRow(self, etiqueta, campo=None):
        if campo is None:
            self.addWidget(etiqueta, self._fila_actual, 0, 1, 4)
            self._fila_actual += 1
            self._indice_campo = 0
            return

        texto = QLabel(etiqueta) if isinstance(etiqueta, str) else etiqueta
        if isinstance(texto, QLabel):
            texto.setStyleSheet(
                "QLabel { color: #25364A; font-size: 9pt; "
                "font-weight: 600; background: transparent; }"
            )
            texto.setMinimumHeight(22)

        estilo_control = """
            QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox {
                color: #26384B; background: #FFFFFF; border: 1px solid #D5DFE8;
                border-radius: 7px; padding: 4px 8px; min-height: 24px; font-size: 10pt;
            }
            QTextEdit {
                color: #26384B; background: #FFFFFF; border: 1px solid #D5DFE8;
                border-radius: 7px; padding: 5px 8px; min-height: 42px; max-height: 64px;
                font-size: 10pt;
            }
        """
        campo.setStyleSheet(estilo_control)
        campo.setMinimumWidth(100)
        if isinstance(campo, (QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox)):
            campo.setMinimumHeight(34)
        elif isinstance(campo, QTextEdit):
            campo.setMinimumHeight(44)
            campo.setMaximumHeight(64)

        # Los campos de texto multilínea ocupan una fila completa.
        if isinstance(campo, QTextEdit):
            if self._indice_campo == 1:
                self._fila_actual += 1
                self._indice_campo = 0
            self.addWidget(texto, self._fila_actual, 0)
            self.addWidget(campo, self._fila_actual, 1, 1, 3)
            self._fila_actual += 1
            self._indice_campo = 0
            return

        columna = 0 if self._indice_campo == 0 else 2
        self.addWidget(texto, self._fila_actual, columna)
        self.addWidget(campo, self._fila_actual, columna + 1)
        self._indice_campo += 1
        if self._indice_campo == 2:
            self._fila_actual += 1
            self._indice_campo = 0


def estilizar_formulario(formulario, layout):
    """Aplica estilos legibles y compactos a formularios en dos columnas."""
    layout.setContentsMargins(18, 14, 18, 14)
    layout.setSpacing(10)
    formulario.setContentsMargins(0, 0, 0, 6)
    formulario.setHorizontalSpacing(14)
    formulario.setVerticalSpacing(8)

    estilo_campo = """
        QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox {
            color: #26384B;
            background-color: #FFFFFF;
            border: 1px solid #D5DFE8;
            border-radius: 7px;
            padding: 4px 8px;
            min-height: 24px;
            font-size: 10pt;
        }
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus,
        QSpinBox:focus, QDoubleSpinBox:focus {
            border: 1px solid #1EAA9B;
        }
        QTextEdit {
            color: #26384B;
            background-color: #FFFFFF;
            border: 1px solid #D5DFE8;
            border-radius: 7px;
            padding: 5px 8px;
            min-height: 42px;
            max-height: 64px;
            font-size: 10pt;
        }
        QTextEdit:focus { border: 1px solid #1EAA9B; }
    """
    for etiqueta in formulario.parentWidget().findChildren(QLabel) if formulario.parentWidget() else []:
        if formulario.indexOf(etiqueta) >= 0:
            etiqueta.setStyleSheet(
                "QLabel { color: #25364A; font-size: 9pt; "
                "font-weight: 600; background: transparent; }"
            )
            etiqueta.setMinimumHeight(22)

    for tipo in (QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox, QTextEdit):
        # Solo controles contenidos en el formulario actual.
        for campo in formulario.parentWidget().findChildren(tipo) if formulario.parentWidget() else []:
            if formulario.indexOf(campo) >= 0:
                campo.setStyleSheet(estilo_campo)
                campo.setMinimumWidth(100)
                if isinstance(campo, (QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox)):
                    campo.setMinimumHeight(34)
                elif isinstance(campo, QTextEdit):
                    campo.setMinimumHeight(44)