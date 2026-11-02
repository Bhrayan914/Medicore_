from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
import sys

from .persistencia import PersistenciaMixin
from .buscador import BuscadorMixin
from .validaciones import ValidacionesMixin
from .interfaz import InterfazMixin
from .especialidades import EspecialidadesMixin
from .medicos import MedicosMixin
from .pacientes import PacientesMixin
from .agenda import AgendaMixin
from .citas import CitasMixin
from .expedientes import ExpedientesMixin
from .consultas import ConsultasMixin
from .recetas import RecetasMixin
from .medicamentos import MedicamentosMixin
from .detalle_receta import DetalleRecetaMixin
from .exportar_pdf import ExportarPDFMixin
from .usuarios import UsuariosMixin
from .login import LoginWindow


class MediCore(
    QMainWindow,
    BuscadorMixin,
    ValidacionesMixin,
    PersistenciaMixin,
    InterfazMixin,
    EspecialidadesMixin,
    MedicosMixin,
    PacientesMixin,
    AgendaMixin,
    CitasMixin,
    ExpedientesMixin,
    ConsultasMixin,
    RecetasMixin,
    MedicamentosMixin,
    DetalleRecetaMixin,
    ExportarPDFMixin,
    UsuariosMixin
):
    def __init__(self, usuario):
        super().__init__()

        self.usuario_actual = usuario

        self.setWindowTitle("MediCore")
        self.resize(1100, 700)

        self.cerrar_sesion_solicitada = False

        self.crear_interfaz()
        self.aplicar_estilos()

    def cerrar_sesion(self):
        if not self._confirmar(
            "Cerrar sesión",
            "¿Deseas cerrar la sesión actual y volver al inicio de sesión?",
            "Sí, cerrar sesión",
        ):
            return

        self.cerrar_sesion_solicitada = True
        self.close()


def main():
    app = QApplication(sys.argv)

    while True:
        login = LoginWindow()

        if login.exec() != LoginWindow.DialogCode.Accepted:
            break

        usuario = login.usuario_autenticado

        if not usuario:
            QMessageBox.critical(
                None,
                "Error",
                "No se pudo obtener la información del usuario."
            )
            break

        ventana = MediCore(usuario)
        ventana.show()
        app.exec()

        # Si se cerró con el botón "Cerrar sesión", vuelve al login.
        if not ventana.cerrar_sesion_solicitada:
            break

        ventana.deleteLater()

    sys.exit(0)


if __name__ == "__main__":
    main()