"""Exportación de recetas médicas a PDF con ReportLab.

Se combinan las dos técnicas vistas en la Sesión 34:

* Lienzo directo (Canvas): dibuja lo que va FIJO en cada hoja, con
  coordenadas exactas: el logo, el título, los datos del paciente, las dos
  líneas de firma y sello, y el pie de página.
* Elementos de flujo (Flowables / SimpleDocTemplate): construyen el cuerpo
  de la receta. Los medicamentos son una lista de tamaño variable, así que
  ReportLab calcula solo los saltos de página si no caben en una hoja.

Instalación (una sola vez):  pip install reportlab
"""

from functools import partial
from pathlib import Path
from xml.sax.saxutils import escape

from PySide6.QtCore import QStandardPaths, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QMessageBox

try:
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer
    )

    REPORTLAB_DISPONIBLE = True
except ImportError:  # la app sigue funcionando; solo falla al exportar
    REPORTLAB_DISPONIBLE = False


# ----------------------------------------------------------------------
# Formato de la hoja: media carta (5.5 x 8.5 pulgadas), parecida a la hoja
# de una constancia. Para usar A5 cambia a 148.0 x 210.0.
# ----------------------------------------------------------------------
ANCHO_MM = 139.7
ALTO_MM = 215.9
MARGEN_MM = 12

# Espacio que el Canvas reserva arriba (encabezado) y abajo (firmas).
ALTO_ENCABEZADO_MM = 59
ALTO_FIRMAS_MM = 56

COLOR_TITULO = "#183A53"
COLOR_TEXTO = "#1E293B"
COLOR_SUAVE = "#62748A"
COLOR_ACENTO = "#1EAA9B"
COLOR_LINEA = "#DDE6EE"

RUTA_LOGO = Path(__file__).resolve().parent / "logo_medicore.png"


def _ajustar_texto(texto, fuente, tamano, ancho_maximo):
    """Recorta el texto con '...' si no cabe en el ancho disponible."""
    if stringWidth(texto, fuente, tamano) <= ancho_maximo:
        return texto

    while texto and stringWidth(texto + "...", fuente, tamano) > ancho_maximo:
        texto = texto[:-1]

    return texto.rstrip() + "..."


if REPORTLAB_DISPONIBLE:

    class LienzoReceta(canvas.Canvas):
        """Canvas que dibuja los elementos fijos de cada hoja.

        Guarda las páginas y las termina al final (en save) porque así
        se conoce el total de hojas para escribir "Página 1 de 2" y
        se puede poner la firma solo en la última.
        """

        def __init__(self, *args, cabecera=None, ruta_logo=None, **kwargs):
            super().__init__(*args, **kwargs)
            self._paginas_guardadas = []
            self.cabecera = cabecera or {}
            self.ruta_logo = ruta_logo

        def showPage(self):
            self._paginas_guardadas.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._paginas_guardadas)

            for numero, estado in enumerate(self._paginas_guardadas, start=1):
                self.__dict__.update(estado)
                self._dibujar_encabezado()

                if numero == total:
                    self._dibujar_firmas()

                self._dibujar_pie(numero, total)
                super().showPage()

            super().save()

        # -------------------------- encabezado --------------------------
        def _dibujar_encabezado(self):
            ancho, alto = self._pagesize
            x0 = MARGEN_MM * mm
            x1 = ancho - x0

            # Logo centrado (coordenadas medidas desde abajo a la izquierda).
            alto_logo = 22 * mm
            y_logo = alto - 10 * mm - alto_logo

            try:
                lector = ImageReader(str(self.ruta_logo))
                ancho_img, alto_img = lector.getSize()
                ancho_logo = alto_logo * ancho_img / alto_img
                self.drawImage(
                    lector, (ancho - ancho_logo) / 2, y_logo,
                    width=ancho_logo, height=alto_logo, mask="auto"
                )
            except Exception:
                self.setFillColor(colors.HexColor(COLOR_TITULO))
                self.setFont("Helvetica-Bold", 24)
                self.drawCentredString(ancho / 2, y_logo + 7 * mm, "MediCore")

            # Título.
            self.setFillColor(colors.HexColor(COLOR_TITULO))
            self.setFont("Helvetica-Bold", 13)
            self.drawCentredString(
                ancho / 2, alto - 40 * mm,
                f"RECETA MÉDICA N.º {self.cabecera.get('id', '')}"
            )

            # Línea de acento.
            self.setStrokeColor(colors.HexColor(COLOR_ACENTO))
            self.setLineWidth(1.4)
            self.line(x0, alto - 43 * mm, x1, alto - 43 * mm)

            # Paciente (izquierda) y fecha (derecha).
            y_datos = alto - 50.2 * mm
            fecha = f"Fecha: {self.cabecera.get('fecha', '')}"
            ancho_fecha = stringWidth(fecha, "Helvetica-Bold", 10.5)
            paciente = _ajustar_texto(
                f"Paciente: {self.cabecera.get('paciente', '')}",
                "Helvetica-Bold", 10.5,
                (x1 - x0) - ancho_fecha - 6 * mm
            )

            self.setFillColor(colors.HexColor(COLOR_TEXTO))
            self.setFont("Helvetica-Bold", 10.5)
            self.drawString(x0, y_datos, paciente)
            self.drawRightString(x1, y_datos, fecha)

            self.setStrokeColor(colors.HexColor(COLOR_LINEA))
            self.setLineWidth(0.7)
            self.line(x0, alto - 54 * mm, x1, alto - 54 * mm)

        # ------------------------- firma y sello ------------------------
        def _dibujar_firmas(self):
            ancho, _ = self._pagesize
            x0 = MARGEN_MM * mm
            x1 = ancho - x0
            ancho_linea = 52 * mm
            y_linea = 30 * mm

            self.setStrokeColor(colors.HexColor(COLOR_TEXTO))
            self.setLineWidth(0.8)
            self.line(x0, y_linea, x0 + ancho_linea, y_linea)
            self.line(x1 - ancho_linea, y_linea, x1, y_linea)

            centro_firma = x0 + ancho_linea / 2
            centro_sello = x1 - ancho_linea / 2

            self.setFillColor(colors.HexColor(COLOR_SUAVE))
            self.setFont("Helvetica", 8.5)
            self.drawCentredString(centro_firma, y_linea - 4.5 * mm, "Firma del médico")
            self.drawCentredString(centro_sello, y_linea - 4.5 * mm, "Sello")

            medico = _ajustar_texto(
                f"Dr(a). {self.cabecera.get('medico', '')}",
                "Helvetica-Bold", 9, ancho_linea
            )
            self.setFillColor(colors.HexColor(COLOR_TEXTO))
            self.setFont("Helvetica-Bold", 9)
            self.drawCentredString(centro_firma, y_linea - 9 * mm, medico)

            codigo = _ajustar_texto(
                f"Cód. MINSA: {self.cabecera.get('codigo', '')}",
                "Helvetica", 8, ancho_linea
            )
            self.setFillColor(colors.HexColor(COLOR_SUAVE))
            self.setFont("Helvetica", 8)
            self.drawCentredString(centro_firma, y_linea - 13 * mm, codigo)

        # ----------------------------- pie ------------------------------
        def _dibujar_pie(self, numero, total):
            ancho, _ = self._pagesize
            texto = "Válida únicamente con firma y sello del médico · MediCore"

            if total > 1:
                texto += f" · Página {numero} de {total}"

            self.setFillColor(colors.HexColor(COLOR_SUAVE))
            self.setFont("Helvetica", 7.5)
            self.drawCentredString(ancho / 2, 8.5 * mm, texto)


def generar_pdf_receta(ruta, cabecera, medicamentos, ruta_logo=RUTA_LOGO):
    """Crea el PDF de una receta.

    cabecera: dict con id, fecha, paciente, medico, codigo.
    medicamentos: lista de dicts con nombre, presentacion, dosis,
                  frecuencia y duracion.
    """
    if not REPORTLAB_DISPONIBLE:
        raise RuntimeError(
            "Falta la librería ReportLab. Instálala con:\n"
            "pip install reportlab"
        )

    # Estilos tipográficos del cuerpo (Paragraph).
    estilo_nombre = ParagraphStyle(
        "MedicamentoNombre",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor(COLOR_TITULO),
    )
    estilo_detalle = ParagraphStyle(
        "MedicamentoDetalle",
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        leftIndent=14,
        textColor=colors.HexColor(COLOR_TEXTO),
    )

    # Lista de elementos de flujo: ReportLab decide dónde cae cada uno
    # y crea las hojas que hagan falta.
    historia = []

    for numero, med in enumerate(medicamentos, start=1):
        nombre = escape(str(med["nombre"]))
        presentacion = escape(str(med["presentacion"]))
        dosis = escape(str(med["dosis"]))
        frecuencia = escape(str(med["frecuencia"]))
        duracion = escape(str(med["duracion"]))

        # KeepTogether evita partir un medicamento entre dos hojas.
        historia.append(KeepTogether([
            Paragraph(
                f"{numero}. {nombre}"
                f"<font name='Helvetica' size='9' color='{COLOR_SUAVE}'>"
                f"&nbsp;&nbsp;&nbsp;{presentacion}</font>",
                estilo_nombre
            ),
            Paragraph(f"<b>Dosis:</b> {dosis}", estilo_detalle),
            Paragraph(
                f"<b>Frecuencia:</b> {frecuencia} &nbsp;·&nbsp; "
                f"<b>Duración:</b> {duracion}",
                estilo_detalle
            ),
            Spacer(1, 3),
            HRFlowable(
                width="100%", thickness=0.6,
                color=colors.HexColor(COLOR_LINEA), spaceAfter=7
            ),
        ]))

    # El marco de ReportLab agrega 6 pt de relleno por lado; se descuentan
    # para que el cuerpo quede alineado con el encabezado dibujado en Canvas.
    relleno_marco = 6

    documento = SimpleDocTemplate(
        str(ruta),
        pagesize=(ANCHO_MM * mm, ALTO_MM * mm),
        leftMargin=MARGEN_MM * mm - relleno_marco,
        rightMargin=MARGEN_MM * mm - relleno_marco,
        topMargin=ALTO_ENCABEZADO_MM * mm,
        bottomMargin=ALTO_FIRMAS_MM * mm,
        title=f"Receta médica N.º {cabecera.get('id', '')}",
        author="MediCore",
    )

    documento.build(
        historia,
        canvasmaker=partial(
            LienzoReceta, cabecera=cabecera, ruta_logo=ruta_logo
        ),
    )


class ExportarPDFMixin:
    """Botón "Exportar PDF" del módulo Detalle Receta."""

    def exportar_receta_pdf(self):
        if not self._permitir("Detalle", "leer"):
            return

        if not REPORTLAB_DISPONIBLE:
            QMessageBox.warning(
                self,
                "Falta ReportLab",
                "Para exportar a PDF instala la librería ReportLab.\n\n"
                "En la terminal ejecuta:\npip install reportlab"
            )
            return

        id_receta = self.receta_detalle.currentData()

        if id_receta is None:
            fila = self.tabla_detalle_receta.currentRow()

            if fila >= 0:
                try:
                    id_receta = int(
                        self._item(self.tabla_detalle_receta, fila, 0)
                    )
                except ValueError:
                    id_receta = None

        if id_receta is None:
            QMessageBox.warning(
                self,
                "Exportar receta",
                "Selecciona una receta (o una fila de la tabla) "
                "para exportarla a PDF."
            )
            return

        try:
            datos = self._datos_receta_pdf(int(id_receta))
        except Exception as error:
            self._mensaje_error("No se pudo leer la receta", error)
            return

        if datos is None:
            QMessageBox.warning(
                self,
                "Exportar receta",
                "No se encontró la receta o no tienes acceso a ella."
            )
            return

        cabecera, medicamentos = datos

        if not medicamentos:
            QMessageBox.warning(
                self,
                "Exportar receta",
                f"La receta N.º {cabecera['id']} todavía no tiene "
                "medicamentos. Agrega al menos uno antes de exportarla."
            )
            return

        carpeta = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DocumentsLocation
        )
        nombre_seguro = "".join(
            caracter if caracter.isalnum() else "_"
            for caracter in cabecera["paciente"]
        ).strip("_")
        sugerido = str(
            Path(carpeta) / f"Receta_{cabecera['id']}_{nombre_seguro}.pdf"
        )

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar receta a PDF",
            sugerido,
            "Archivos PDF (*.pdf)"
        )

        if not ruta:
            return

        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"

        try:
            generar_pdf_receta(ruta, cabecera, medicamentos)
        except Exception as error:
            self._mensaje_error("No se pudo generar el PDF", error)
            return

        cuadro = QMessageBox(self)
        cuadro.setIcon(QMessageBox.Icon.Information)
        cuadro.setWindowTitle("Receta exportada")
        cuadro.setText(f"La receta se guardó correctamente en:\n{ruta}")
        boton_abrir = cuadro.addButton(
            "Abrir para imprimir", QMessageBox.ButtonRole.AcceptRole
        )
        cuadro.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
        cuadro.exec()

        if cuadro.clickedButton() is boton_abrir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))

    # ------------------------------------------------------------------
    # Datos desde MySQL
    # ------------------------------------------------------------------
    def _datos_receta_pdf(self, id_receta):
        con = None

        try:
            con = self._db()
            cur = con.cursor()

            sql = (
                "SELECT r.ID_Receta, r.Fecha_Emision, p.Nombre, "
                "m.Nombre, m.Codigo_MINSA, esp.Nombre_Especialidad "
                "FROM Recetas_Medicas r "
                "JOIN Consultas_Historial c ON c.ID_Consulta = r.ID_Consulta "
                "JOIN Expedientes_Clinicos e ON e.ID_Expediente = c.ID_Expediente "
                "JOIN Pacientes p ON p.ID_Paciente = e.ID_Paciente "
                "JOIN Medicos m ON m.ID_Medico = c.ID_Medico "
                "JOIN Especialidades_Medicas esp "
                "     ON esp.ID_Especialidad = m.ID_Especialidad "
                "WHERE r.ID_Receta = %s"
            )
            valores = [id_receta]

            # Un médico solo puede exportar las recetas de sus consultas.
            if self.usuario_actual.get("Rol") == "Medico":
                sql += " AND c.ID_Medico = %s"
                valores.append(self.usuario_actual.get("ID_Medico"))

            cur.execute(sql, tuple(valores))
            fila = cur.fetchone()

            if fila is None:
                return None

            fecha = fila[1]

            if hasattr(fecha, "strftime"):
                fecha = fecha.strftime("%d/%m/%Y")

            cabecera = {
                "id": fila[0],
                "fecha": str(fecha),
                "paciente": fila[2],
                "medico": fila[3],
                "codigo": fila[4],
                "especialidad": fila[5],
            }

            cur.execute(
                "SELECT mc.Nombre_Medicamento, mc.Presentacion, "
                "d.Dosis_Indicada, d.Frecuencia, d.Duracion "
                "FROM Detalle_Receta d "
                "JOIN Medicamentos_Catalogo mc "
                "     ON mc.ID_Medicamento = d.ID_Medicamento "
                "WHERE d.ID_Receta = %s "
                "ORDER BY mc.Nombre_Medicamento",
                (id_receta,)
            )

            medicamentos = [
                {
                    "nombre": f[0],
                    "presentacion": f[1],
                    "dosis": f[2],
                    "frecuencia": f[3],
                    "duracion": f[4],
                }
                for f in cur.fetchall()
            ]

            return cabecera, medicamentos

        finally:
            if con:
                con.close()