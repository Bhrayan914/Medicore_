"""Validaciones de formularios de MediCore.

- Nombres (especialidad, médico, paciente, medicamento): solo letras y espacios.
- Código MINSA: estrictamente MINSA-0000 (el prefijo se escribe solo).
- Cédula: estrictamente 000-000000-0000A (los guiones se ponen solos).
- Presión arterial: estrictamente números con formato 120/80.
- Fechas de cita, consulta, expediente y receta: hoy o futuro.
- Hora de la cita: dentro del horario del médico en la Agenda.
"""
import re
import unicodedata
from datetime import timedelta

from PySide6.QtCore import QDate, QRegularExpression, QTime
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QMessageBox

DIAS_SEMANA = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

# (campo de fecha, tabla del módulo, columna de la fecha en la tabla)
CAMPOS_FECHA = [
    ("fecha_cita", "tabla_citas", 3),
    ("fecha_expediente", "tabla_expedientes", 2),
    ("fecha_receta", "tabla_recetas", 2),
]

# Intervalo mínimo entre dos citas (minutos) del mismo médico o del mismo paciente.
INTERVALO_MINIMO_CITAS = 15

# Turnos de los médicos, en minutos desde las 00:00 (el nocturno cruza la medianoche).
TURNOS = {
    "Matutino": [(7 * 60, 12 * 60)],
    "Vespertino": [(12 * 60, 20 * 60)],
    "Nocturno": [(0, 7 * 60), (20 * 60, 24 * 60)],
}
TEXTO_TURNOS = {
    "Matutino": "7:00 a 12:00",
    "Vespertino": "12:00 a 20:00",
    "Nocturno": "20:00 a 7:00",
}

# Familias de medicamentos para el aviso de alergias.
FAMILIAS_ALERGIA = {
    "penicilina": ["penicilina", "amoxicilina", "ampicilina", "dicloxacilina",
                   "cloxacilina", "piperacilina"],
    "sulfa": ["sulfa", "sulfametoxazol", "trimetoprim", "sulfadiazina"],
    "aspirina": ["aspirina", "acetilsalicilico"],
    "acetilsalicilico": ["aspirina", "acetilsalicilico"],
    "ibuprofeno": ["ibuprofeno"],
    "aine": ["ibuprofeno", "naproxeno", "diclofenaco", "ketorolaco", "aspirina",
             "acetilsalicilico"],
    "antiinflamatorio": ["ibuprofeno", "naproxeno", "diclofenaco", "ketorolaco",
                         "aspirina", "acetilsalicilico"],
    "paracetamol": ["paracetamol", "acetaminofen"],
    "acetaminofen": ["paracetamol", "acetaminofen"],
}


# ----------------------------------------------------------------------
# Funciones puras (no dependen de la interfaz)
# ----------------------------------------------------------------------
def _sin_tildes(texto):
    texto = unicodedata.normalize("NFD", str(texto or ""))
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").casefold()


def formatear_cedula(texto):
    """Deja solo el formato 000-000000-0000A mientras se escribe."""
    limpio = re.sub(r"[^0-9A-Za-z]", "", texto).upper()
    digitos, letra = "", ""
    for c in limpio:
        if len(digitos) < 13:
            if c.isdigit():
                digitos += c
        elif not letra and c.isascii() and c.isalpha():
            letra = c
    resultado = digitos[:3]
    if len(digitos) > 3:
        resultado += "-" + digitos[3:9]
    if len(digitos) > 9:
        resultado += "-" + digitos[9:13]
    return resultado + letra


def cedula_valida(texto):
    return re.fullmatch(r"\d{3}-\d{6}-\d{4}[A-Z]", texto.strip()) is not None


def formatear_minsa(texto):
    """Deja solo el formato MINSA-0000 mientras se escribe."""
    digitos = re.sub(r"\D", "", texto)[:4]
    if digitos:
        return "MINSA-" + digitos
    mayus = texto.upper()
    if mayus in ("", "MINSA"):          # borrando
        return ""
    if mayus.startswith("MINSA") or "MINSA-".startswith(mayus):
        return "MINSA-"
    return ""


def minsa_valido(texto):
    return re.fullmatch(r"MINSA-\d{4}", texto.strip()) is not None


def formatear_lugar(texto):
    """Deja solo el formato A-000 (una letra, guion y 3 números) mientras se escribe."""
    limpio = re.sub(r"[^0-9A-Za-z]", "", texto).upper()
    letra, digitos = "", ""
    for c in limpio:
        if not letra:
            if c.isascii() and c.isalpha():
                letra = c
        elif c.isdigit() and len(digitos) < 3:
            digitos += c
    if not letra:
        return ""
    return letra + ("-" + digitos if digitos else "")


def lugar_valido(texto):
    return re.fullmatch(r"[A-Z]-\d{3}", texto.strip()) is not None


def edad_en_anios(nacimiento, hoy):
    """Años cumplidos entre dos QDate."""
    anios = hoy.year() - nacimiento.year()
    if (hoy.month(), hoy.day()) < (nacimiento.month(), nacimiento.day()):
        anios -= 1
    return anios


def nombre_valido(texto, palabras_minimas=1):
    """Solo letras (con tildes y ñ) separadas por un espacio."""
    texto = texto.strip()
    if re.fullmatch(r"[^\W\d_]+(?: [^\W\d_]+)*", texto) is None:
        return False
    return len(texto.split(" ")) >= palabras_minimas


def presion_valida(texto):
    """Devuelve (ok, mensaje). Formato 120/80, sistólica mayor que diastólica."""
    texto = texto.strip()
    if re.fullmatch(r"\d{2,3}/\d{2,3}", texto) is None:
        return False, "La presión arterial debe tener el formato 120/80 (solo números)."
    sistolica, diastolica = (int(n) for n in texto.split("/"))
    if sistolica <= diastolica:
        return False, "En la presión arterial, el primer número (sistólica) debe ser mayor que el segundo (diastólica)."
    return True, ""


def bloque_en_turno(turno, inicio_min, fin_min):
    """True si el bloque (en minutos) cabe completo dentro del turno."""
    for desde, hasta in TURNOS.get(turno, []):
        if desde <= inicio_min and fin_min <= hasta:
            return True
    return False


def rangos_se_solapan(a_inicio, a_fin, b_inicio, b_fin):
    return a_inicio < b_fin and b_inicio < a_fin


def minutos(valor):
    """Minutos desde las 00:00 de un QTime o del TIME de MySQL."""
    t = a_qtime(valor) if not hasattr(valor, "hour") else valor
    return t.hour() * 60 + t.minute()


def alergia_coincidente(medicamento, alergias):
    """Devuelve el texto de la alergia que coincide con el medicamento, o None."""
    if not alergias:
        return None
    med = _sin_tildes(medicamento)
    for parte in re.split(r"[,;/\n]|\sy\s|\se\s", str(alergias)):
        original = parte.strip()
        token = _sin_tildes(original)
        if len(token) < 4 or token in ("ninguna", "ninguno", "sin alergias", "no tiene"):
            continue
        if token in med or med in token:
            return original
        for clave, medicinas in FAMILIAS_ALERGIA.items():
            if clave in token and any(m in med for m in medicinas):
                return original
    return None


def a_qtime(valor):
    """Convierte el TIME de MySQL (timedelta o texto) a QTime."""
    if isinstance(valor, timedelta):
        segundos = int(valor.total_seconds())
        return QTime(segundos // 3600 % 24, segundos // 60 % 60, segundos % 60)
    partes = [int(p) for p in str(valor).split(":")]
    partes += [0] * (3 - len(partes))
    return QTime(*partes[:3])


def leer_fecha(texto):
    for formato in ("yyyy-MM-dd", "dd/MM/yyyy"):
        fecha = QDate.fromString(texto.strip()[:10], formato)
        if fecha.isValid():
            return fecha
    return QDate()


# ----------------------------------------------------------------------
# Mixin
# ----------------------------------------------------------------------
class ValidacionesMixin:

    def crear_interfaz(self):
        super().crear_interfaz()
        self._instalar_validaciones()

    # ---------------- instalación ----------------
    def _instalar_validaciones(self):
        # Solo letras y espacios
        regex_letras = QRegularExpression(r"[\p{L} ]*")
        for atributo in ("nombre_especialidad", "nombre_medico",
                         "nombre_paciente", "nombre_medicamento"):
            campo = getattr(self, atributo, None)
            if campo is not None:
                campo.setValidator(QRegularExpressionValidator(regex_letras, campo))

        # Código MINSA y cédula: se formatean mientras se escribe
        self._enlazar_formato("codigo_minsa", formatear_minsa)
        self._enlazar_formato("cedula_paciente", formatear_cedula)
        self._enlazar_formato("lugar_expediente", formatear_lugar)

        # Presión arterial: solo números y una "/"
        presion = getattr(self, "presion_consulta", None)
        if presion is not None:
            presion.setValidator(QRegularExpressionValidator(
                QRegularExpression(r"\d{0,3}(/\d{0,3})?"), presion))

        # Consultas: la fecha, el médico y el expediente salen de la cita elegida
        if hasattr(self, "cita_consulta") and hasattr(self, "fecha_consulta"):
            self.fecha_consulta.setEnabled(False)
            self.fecha_consulta.setToolTip("La fecha se toma automáticamente de la cita seleccionada")
            self.cita_consulta.currentIndexChanged.connect(self._sincronizar_cita_consulta)

        # Fechas: desde hoy en adelante
        hoy = QDate.currentDate()
        for atributo, tabla_attr, columna in CAMPOS_FECHA:
            widget = getattr(self, atributo, None)
            tabla = getattr(self, tabla_attr, None)
            if widget is None:
                continue
            widget.setMinimumDate(hoy)
            widget.setDate(hoy)
            if tabla is not None:
                # Al elegir un registro viejo se permite mostrar su fecha original
                # (así se puede editar, por ejemplo, el estado de una cita pasada).
                tabla.cellClicked.connect(
                    lambda fila, col, w=widget, t=tabla, c=columna:
                    self._ajustar_fecha_seleccion(w, t, c, fila)
                )

    def _enlazar_formato(self, atributo, funcion):
        campo = getattr(self, atributo, None)
        if campo is None:
            return

        def alterar(texto):
            nuevo = funcion(texto)
            if nuevo != texto:
                campo.setText(nuevo)

        campo.textEdited.connect(alterar)

    def _ajustar_fecha_seleccion(self, widget, tabla, columna, fila):
        item = tabla.item(fila, columna)
        hoy = QDate.currentDate()
        fecha = leer_fecha(item.text()) if item else QDate()
        if fecha.isValid() and fecha < hoy:
            widget.setMinimumDate(fecha)
            widget.setDate(fecha)
        else:
            widget.setMinimumDate(hoy)

    def _reiniciar_fecha(self, atributo):
        widget = getattr(self, atributo, None)
        if widget is not None:
            hoy = QDate.currentDate()
            widget.setMinimumDate(hoy)
            widget.setDate(hoy)

    # ---------------- utilidades ----------------
    def _val_aviso(self, titulo, mensaje, campo=None):
        QMessageBox.warning(self, titulo, mensaje)
        if campo is not None:
            campo.setFocus()
        return False

    def _val_nombre(self, campo, etiqueta, palabras=1):
        if nombre_valido(campo.text(), palabras):
            return True
        if palabras > 1:
            mensaje = f"{etiqueta}: escribe nombre y apellido, solo letras y un espacio entre palabras."
        else:
            mensaje = f"{etiqueta}: escribe solo letras (sin números ni símbolos)."
        return self._val_aviso("Dato inválido", mensaje, campo)

    def _val_fecha_futura(self, atributo, tabla_attr, columna, etiqueta, editando):
        widget = getattr(self, atributo)
        hoy = QDate.currentDate()
        fecha = widget.date()
        if fecha >= hoy:
            return True
        if editando:
            tabla = getattr(self, tabla_attr)
            item = tabla.item(tabla.currentRow(), columna)
            if item is not None and leer_fecha(item.text()) == fecha:
                return True  # no se cambió la fecha del registro
        return self._val_aviso(
            "Fecha inválida",
            f"{etiqueta} no puede ser anterior a hoy ({hoy.toString('dd/MM/yyyy')}).",
            widget,
        )

    # ---------------- Especialidades ----------------
    def _val_especialidad(self):
        return self._val_nombre(self.nombre_especialidad, "Especialidad")

    def guardar_especialidad(self):
        if self._val_especialidad():
            return super().guardar_especialidad()

    def editar_especialidad(self):
        if self._val_especialidad():
            return super().editar_especialidad()

    # ---------------- Médicos ----------------
    def _val_medico(self):
        if not minsa_valido(self.codigo_minsa.text()):
            return self._val_aviso(
                "Dato inválido",
                "Código MINSA: usa el formato MINSA-0001 (MINSA- y 4 números).",
                self.codigo_minsa)
        return self._val_nombre(self.nombre_medico, "Nombre del médico", 2)

    def guardar_medico(self):
        if self._val_medico():
            return super().guardar_medico()

    def editar_medico(self):
        if self._val_medico():
            return super().editar_medico()

    # ---------------- Pacientes ----------------
    def _val_paciente(self):
        hoy = QDate.currentDate()
        nacimiento = self.fecha_nacimiento.date()
        cedula = self.cedula_paciente.text().strip()

        if nacimiento > hoy:
            return self._val_aviso(
                "Fecha inválida",
                "La fecha de nacimiento no puede ser futura.",
                self.fecha_nacimiento)

        if edad_en_anios(nacimiento, hoy) > 120:
            return self._val_aviso(
                "Fecha inválida",
                "La fecha de nacimiento no es válida (más de 120 años).",
                self.fecha_nacimiento)

        if cedula:
            if not cedula_valida(cedula):
                return self._val_aviso(
                    "Dato inválido",
                    "Cédula: usa el formato 001-010190-0001A (13 números y una letra al final).",
                    self.cedula_paciente)
        elif edad_en_anios(nacimiento, hoy) >= 18:
            # Solo los menores de edad pueden registrarse sin cédula.
            return self._val_aviso(
                "Cédula requerida",
                "Los pacientes de 18 años o más necesitan cédula.\n"
                "Solo los menores de edad pueden registrarse sin cédula.\n\n"
                "Si el paciente es menor, revisa la fecha de nacimiento.",
                self.cedula_paciente)

        if not self._val_nombre(self.nombre_paciente, "Nombre del paciente", 2):
            return False

        if self.sexo_paciente.currentIndex() == 0:
            return self._val_aviso(
                "Sexo requerido",
                "Selecciona el sexo del paciente (Masculino o Femenino).",
                self.sexo_paciente)

        return True

    def guardar_paciente(self):
        if self._val_paciente():
            return super().guardar_paciente()

    def editar_paciente(self):
        if self._val_paciente():
            return super().editar_paciente()

    # ---------------- Medicamentos ----------------
    def _val_medicamento(self):
        return self._val_nombre(self.nombre_medicamento, "Nombre del medicamento")

    def _val_existencia(self):
        if self.existencia_medicamento.value() > 0:
            return True
        return self._val_aviso(
            "Existencia inválida",
            "La existencia debe ser mayor que 0 para agregar el medicamento.",
            self.existencia_medicamento)

    def guardar_medicamento(self):
        if self._val_medicamento() and self._val_existencia():
            return super().guardar_medicamento()

    def editar_medicamento(self):
        if self._val_medicamento():
            return super().editar_medicamento()

    # ---------------- Citas médicas ----------------
    def _val_horario_medico(self):
        """La fecha y hora de la cita deben caer dentro de la agenda del médico."""
        medico_id = self.medico_cita.currentData()
        fecha = self.fecha_cita.date()
        hora = self.hora_cita.time()
        dia = DIAS_SEMANA[fecha.dayOfWeek() - 1]
        nombre = self.medico_cita.currentText()

        con = None
        try:
            con = self._db()
            cur = con.cursor()
            cur.execute(
                "SELECT Dia_Semana, Hora_Inicio, Hora_Fin FROM Agenda_Horarios "
                "WHERE ID_Medico = %s ORDER BY Hora_Inicio", (medico_id,))
            filas = cur.fetchall()
            cur.close()
        except Exception as error:
            return self._val_aviso("Agenda", f"No se pudo consultar el horario del médico:\n{error}")
        finally:
            if con:
                con.close()

        if not filas:
            return self._val_aviso(
                "Horario del médico",
                f"{nombre} no tiene horarios registrados en la Agenda.\n"
                "Registra su horario antes de programar citas.",
                self.medico_cita)

        bloques = [(a_qtime(i), a_qtime(f)) for d, i, f in filas
                   if _sin_tildes(d) == _sin_tildes(dia)]

        if not bloques:
            dias = sorted({d for d, _, _ in filas},
                          key=lambda d: DIAS_SEMANA.index(d) if d in DIAS_SEMANA else 99)
            return self._val_aviso(
                "Horario del médico",
                f"{nombre} no atiende los {dia}.\nDías con horario: {', '.join(dias)}.",
                self.fecha_cita)

        if any(inicio <= hora < fin for inicio, fin in bloques):
            return True

        rangos = ", ".join(f"{i.toString('HH:mm')} a {f.toString('HH:mm')}" for i, f in bloques)
        return self._val_aviso(
            "Horario del médico",
            f"{nombre} atiende los {dia} de {rangos}.\n"
            f"La hora elegida ({hora.toString('HH:mm')}) está fuera de ese horario.",
            self.hora_cita)

    def _val_asistio_futuro(self):
        """No se puede marcar 'Asistió' una cita con fecha futura."""
        if (self.estado_cita.currentText() == "Asistio"
                and self.fecha_cita.date() > QDate.currentDate()):
            return self._val_aviso(
                "Estado inválido",
                "No puedes marcar como «Asistió» una cita con fecha futura.\n"
                "Déjala como «Programada» hasta el día de la cita.",
                self.estado_cita)
        return True

    def _val_conflictos_cita(self, excluir_id):
        """Mismo médico o mismo paciente: mínimo 15 minutos entre citas."""
        paciente = self.paciente_cita.currentData()
        medico = self.medico_cita.currentData()
        fecha = self.fecha_cita.date().toString("yyyy-MM-dd")
        hora = self.hora_cita.time()

        con = None
        try:
            con = self._db()
            cur = con.cursor()
            cur.execute(
                "SELECT c.ID_Medico, c.ID_Paciente, c.Hora, p.Nombre, m.Nombre "
                "FROM Citas_Medicas c "
                "JOIN Pacientes p ON p.ID_Paciente = c.ID_Paciente "
                "JOIN Medicos m ON m.ID_Medico = c.ID_Medico "
                "WHERE c.Fecha = %s AND c.Estado <> 'Cancelada' AND c.ID_Cita <> %s "
                "AND (c.ID_Medico = %s OR c.ID_Paciente = %s) "
                "AND ABS(TIME_TO_SEC(c.Hora) - TIME_TO_SEC(%s)) < %s "
                "ORDER BY c.Hora",
                (fecha, excluir_id, medico, paciente,
                 hora.toString("HH:mm:ss"), INTERVALO_MINIMO_CITAS * 60))
            filas = cur.fetchall()
            cur.close()
        except Exception as error:
            return self._val_aviso("Citas", f"No se pudo comprobar la disponibilidad:\n{error}")
        finally:
            if con:
                con.close()

        if not filas:
            return True

        regla = f"Debe haber al menos {INTERVALO_MINIMO_CITAS} minutos entre citas."
        for id_medico, _, hora_cita, nom_paciente, nom_medico in filas:
            if id_medico == medico:
                return self._val_aviso(
                    "Horario ocupado",
                    f"{nom_medico} ya tiene una cita ese día a las "
                    f"{a_qtime(hora_cita).toString('HH:mm')} (paciente: {nom_paciente}).\n"
                    f"{regla}",
                    self.hora_cita)
        id_medico, _, hora_cita, nom_paciente, nom_medico = filas[0]
        return self._val_aviso(
            "Paciente ocupado",
            f"{nom_paciente} ya tiene una cita ese día a las "
            f"{a_qtime(hora_cita).toString('HH:mm')} con {nom_medico}.\n{regla}",
            self.hora_cita)

    def guardar_cita(self):
        if self.paciente_cita.currentData() is None or self.medico_cita.currentData() is None:
            return super().guardar_cita()  # el módulo ya avisa qué falta
        if self.estado_cita.currentText() == "Cancelada":
            return super().guardar_cita()
        if (self._val_fecha_futura("fecha_cita", "tabla_citas", 3, "La fecha de la cita", False)
                and self._val_asistio_futuro()
                and self._val_horario_medico()
                and self._val_conflictos_cita(0)):
            return super().guardar_cita()

    def editar_cita(self):
        if self.paciente_cita.currentData() is None or self.medico_cita.currentData() is None:
            return super().editar_cita()

        fila = self.tabla_citas.currentRow()

        def celda(columna):
            item = self.tabla_citas.item(fila, columna)
            return item.text() if item else ""

        nuevo_estado = self.estado_cita.currentText()
        if nuevo_estado == "Cancelada":
            return super().editar_cita()
        if not self._val_asistio_futuro():
            return

        # Si no se tocó paciente, médico, fecha ni hora (p. ej. solo se cambia el
        # estado de una cita pasada) no se vuelve a validar el horario.
        agenda_igual = (
            fila >= 0
            and celda(1) == self.paciente_cita.currentText()
            and celda(2) == self.medico_cita.currentText()
            and leer_fecha(celda(3)) == self.fecha_cita.date()
            and celda(4)[:5] == self.hora_cita.time().toString("HH:mm")
        )
        reactivando = celda(5) == "Cancelada"
        if agenda_igual and not reactivando:
            return super().editar_cita()

        id_cita = int(celda(0)) if celda(0).isdigit() else 0
        if (self._val_fecha_futura("fecha_cita", "tabla_citas", 3, "La fecha de la cita", True)
                and self._val_horario_medico()
                and self._val_conflictos_cita(id_cita)):
            return super().editar_cita()

    def limpiar_cita(self):
        super().limpiar_cita()
        self._reiniciar_fecha("fecha_cita")

    # ---------------- Consultas ----------------
    def _datos_cita(self, cita_id):
        """(ID_Paciente, nombre paciente, ID_Medico, nombre médico, fecha) de una cita."""
        con = None
        try:
            con = self._db()
            cur = con.cursor()
            cur.execute(
                "SELECT c.ID_Paciente, p.Nombre, c.ID_Medico, m.Nombre, c.Fecha "
                "FROM Citas_Medicas c "
                "JOIN Pacientes p ON p.ID_Paciente = c.ID_Paciente "
                "JOIN Medicos m ON m.ID_Medico = c.ID_Medico "
                "WHERE c.ID_Cita = %s", (cita_id,))
            fila = cur.fetchone()
            cur.close()
            return fila
        except Exception:
            return None
        finally:
            if con:
                con.close()

    def _datos_expediente(self, expediente_id):
        """(ID_Paciente, nombre paciente) de un expediente."""
        con = None
        try:
            con = self._db()
            cur = con.cursor()
            cur.execute(
                "SELECT e.ID_Paciente, p.Nombre FROM Expedientes_Clinicos e "
                "JOIN Pacientes p ON p.ID_Paciente = e.ID_Paciente "
                "WHERE e.ID_Expediente = %s", (expediente_id,))
            fila = cur.fetchone()
            cur.close()
            return fila
        except Exception:
            return None
        finally:
            if con:
                con.close()

    def _sincronizar_cita_consulta(self, *_):
        """Al elegir la cita se rellenan solos la fecha, el médico y el expediente."""
        cita = self.cita_consulta.currentData()
        if cita is None:
            return
        datos = self._datos_cita(cita)
        if datos is None:
            return
        id_paciente, nom_paciente, id_medico, _nom_medico, fecha = datos

        self.fecha_consulta.setDate(QDate(fecha.year, fecha.month, fecha.day))

        indice = self.medico_consulta.findData(id_medico)
        if indice >= 0:
            self.medico_consulta.setCurrentIndex(indice)

        con = None
        id_expediente = None
        try:
            con = self._db()
            cur = con.cursor()
            cur.execute("SELECT ID_Expediente FROM Expedientes_Clinicos WHERE ID_Paciente = %s",
                        (id_paciente,))
            fila = cur.fetchone()
            cur.close()
            id_expediente = fila[0] if fila else None
        except Exception:
            id_expediente = None
        finally:
            if con:
                con.close()

        indice = self.expediente_consulta.findData(id_expediente)
        if indice >= 0:
            self.expediente_consulta.setCurrentIndex(indice)
        else:
            self.expediente_consulta.setCurrentIndex(0)
            self._val_aviso(
                "Expediente no encontrado",
                f"{nom_paciente} no tiene expediente clínico.\n"
                "Créalo primero en el módulo Expedientes Clínicos.")

    def _val_cita_coherente(self):
        """La cita debe ser del paciente del expediente y del médico elegido."""
        expediente = self.expediente_consulta.currentData()
        medico = self.medico_consulta.currentData()
        cita = self.cita_consulta.currentData()
        if expediente is None or medico is None or cita is None:
            return True  # el módulo ya avisa qué falta

        datos_cita = self._datos_cita(cita)
        datos_exp = self._datos_expediente(expediente)
        if datos_cita is None or datos_exp is None:
            return self._val_aviso("Consulta", "No se pudo comprobar la cita o el expediente.")

        id_pac_cita, nom_pac_cita, id_med_cita, nom_med_cita, fecha = datos_cita
        id_pac_exp, nom_pac_exp = datos_exp

        if id_pac_cita != id_pac_exp:
            return self._val_aviso(
                "Datos incoherentes",
                f"La cita seleccionada es de {nom_pac_cita}, pero el expediente es de {nom_pac_exp}.\n"
                "Elige la cita y el expediente del mismo paciente.",
                self.cita_consulta)
        if id_med_cita != medico:
            return self._val_aviso(
                "Datos incoherentes",
                f"La cita seleccionada fue programada con {nom_med_cita}.\n"
                "El médico de la consulta debe ser el mismo de la cita.",
                self.medico_consulta)

        # La fecha de la consulta es siempre la fecha de la cita.
        self.fecha_consulta.setDate(QDate(fecha.year, fecha.month, fecha.day))
        return True

    def _val_consulta(self, editando):
        texto = self.presion_consulta.text().strip()
        if texto:  # si está vacío, el módulo ya avisa que falta
            ok, mensaje = presion_valida(texto)
            if not ok:
                return self._val_aviso("Presión arterial", mensaje, self.presion_consulta)
        return self._val_cita_coherente()

    def guardar_consulta(self):
        if self._val_consulta(False):
            return super().guardar_consulta()

    def editar_consulta(self):
        if self._val_consulta(True):
            return super().editar_consulta()

    # ---------------- Agenda de horarios ----------------
    def _val_agenda(self, editando):
        medico = self.medico_agenda.currentData()
        inicio = self.hora_inicio_agenda.time()
        fin = self.hora_fin_agenda.time()
        if medico is None or inicio >= fin:
            return True  # el módulo ya avisa qué falta

        ini_min, fin_min = minutos(inicio), minutos(fin)
        dia = self.dia_agenda.currentText()
        nombre = self.medico_agenda.currentText()
        excluir = (self._id_seleccionado(self.tabla_agenda) or 0) if editando else 0

        con = None
        try:
            con = self._db()
            cur = con.cursor()
            cur.execute("SELECT Turno FROM Medicos WHERE ID_Medico = %s", (medico,))
            fila = cur.fetchone()
            turno = fila[0] if fila else None
            cur.execute(
                "SELECT Hora_Inicio, Hora_Fin FROM Agenda_Horarios "
                "WHERE ID_Medico = %s AND Dia_Semana = %s AND ID_Agenda <> %s",
                (medico, dia, excluir))
            otros = cur.fetchall()
            cur.close()
        except Exception as error:
            return self._val_aviso("Agenda", f"No se pudo validar el horario:\n{error}")
        finally:
            if con:
                con.close()

        # 1) Dentro del turno del médico (salvo horario especial)
        if turno and not self.horario_especial.isChecked():
            if not bloque_en_turno(turno, ini_min, fin_min):
                ayuda = ""
                if turno == "Nocturno":
                    ayuda = ("\n\nEl turno nocturno cruza la medianoche: registra dos bloques "
                             "por día (por ejemplo 20:00 a 23:59 y 00:00 a 7:00).")
                return self._val_aviso(
                    "Fuera del turno",
                    f"{nombre} tiene turno {turno} ({TEXTO_TURNOS[turno]}).\n"
                    "Este horario queda fuera de su turno.\n\n"
                    "Si es una excepción, marca la casilla «Horario especial»." + ayuda,
                    self.hora_inicio_agenda)

        # 2) Sin cruzarse con otros horarios del mismo médico y día
        for otro_ini, otro_fin in otros:
            if rangos_se_solapan(ini_min, fin_min, minutos(otro_ini), minutos(otro_fin)):
                return self._val_aviso(
                    "Horario duplicado",
                    f"Este horario se cruza con otro ya registrado para {nombre} el {dia} "
                    f"({a_qtime(otro_ini).toString('HH:mm')} a {a_qtime(otro_fin).toString('HH:mm')}).",
                    self.hora_inicio_agenda)
        return True

    def guardar_agenda(self):
        if self._val_agenda(False):
            return super().guardar_agenda()

    def editar_agenda(self):
        if self._val_agenda(True):
            return super().editar_agenda()

    # ---------------- Detalle de receta: aviso de alergias ----------------
    def _val_alergia(self, editando):
        receta = self.receta_detalle.currentData()
        medicamento = self.medicamento_detalle.currentData()
        if receta is None or medicamento is None:
            return True  # el módulo ya avisa qué falta

        if editando:
            fila = self.tabla_detalle_receta.currentRow()
            item_rec = self.tabla_detalle_receta.item(fila, 0)
            item_med = self.tabla_detalle_receta.item(fila, 1)
            if (item_rec is not None and item_med is not None
                    and item_rec.text() == str(receta) and item_med.text() == str(medicamento)):
                return True  # el medicamento no cambió

        con = None
        try:
            con = self._db()
            cur = con.cursor()
            cur.execute(
                "SELECT p.Nombre, p.Alergias, mc.Nombre_Medicamento "
                "FROM Recetas_Medicas r "
                "JOIN Consultas_Historial c ON c.ID_Consulta = r.ID_Consulta "
                "JOIN Expedientes_Clinicos e ON e.ID_Expediente = c.ID_Expediente "
                "JOIN Pacientes p ON p.ID_Paciente = e.ID_Paciente "
                "JOIN Medicamentos_Catalogo mc ON mc.ID_Medicamento = %s "
                "WHERE r.ID_Receta = %s", (medicamento, receta))
            fila = cur.fetchone()
            cur.close()
        except Exception:
            return True  # si no se puede comprobar, no se bloquea el trabajo del médico
        finally:
            if con:
                con.close()

        if not fila:
            return True
        paciente, alergias, nombre_med = fila
        coincidencia = alergia_coincidente(nombre_med, alergias)
        if coincidencia is None:
            return True
        return self._confirmar(
            "Posible alergia",
            f"{paciente} tiene registrada una alergia a «{coincidencia}».\n\n"
            f"{nombre_med} podría estar relacionado con esa alergia.\n\n"
            "¿Deseas recetarlo de todos modos?",
            "Sí, recetar")

    def guardar_detalle_receta(self):
        if self._val_alergia(False):
            return super().guardar_detalle_receta()

    def editar_detalle_receta(self):
        if self._val_alergia(True):
            return super().editar_detalle_receta()

    # ---------------- Expedientes ----------------
    def _val_lugar_expediente(self):
        if lugar_valido(self.lugar_expediente.text()):
            return True
        return self._val_aviso(
            "Lugar del expediente",
            "Escribe el lugar físico del expediente con el formato A-001\n"
            "(una letra, un guion y 3 números).",
            self.lugar_expediente)

    def _val_lugar_unico(self, editando):
        """Cada código de lugar solo puede pertenecer a un expediente."""
        lugar = self.lugar_expediente.text().strip().upper()
        excluir = 0
        if editando:
            item = self.tabla_expedientes.item(self.tabla_expedientes.currentRow(), 0)
            excluir = int(item.text()) if item and item.text().isdigit() else 0

        con = None
        try:
            con = self._db()
            cur = con.cursor()
            cur.execute(
                "SELECT e.ID_Expediente, p.Nombre FROM Expedientes_Clinicos e "
                "JOIN Pacientes p ON p.ID_Paciente = e.ID_Paciente "
                "WHERE e.Lugar_Expediente = %s AND e.ID_Expediente <> %s LIMIT 1",
                (lugar, excluir))
            fila = cur.fetchone()
            cur.close()
        except Exception as error:
            return self._val_aviso(
                "Lugar del expediente",
                f"No se pudo comprobar el lugar del expediente:\n{error}")
        finally:
            if con:
                con.close()

        if fila is None:
            return True
        return self._val_aviso(
            "Lugar ya asignado",
            f"El lugar {lugar} ya está asignado al expediente #{fila[0]} ({fila[1]}).\n"
            "Cada código solo puede usarse en un expediente.",
            self.lugar_expediente)

    def guardar_expediente(self):
        if (self._val_lugar_expediente()
                and self._val_lugar_unico(False)
                and self._val_fecha_futura("fecha_expediente", "tabla_expedientes", 2,
                                           "La fecha de creación", False)):
            return super().guardar_expediente()

    def editar_expediente(self):
        if (self._val_lugar_expediente()
                and self._val_lugar_unico(True)
                and self._val_fecha_futura("fecha_expediente", "tabla_expedientes", 2,
                                           "La fecha de creación", True)):
            return super().editar_expediente()

    def limpiar_expediente(self):
        super().limpiar_expediente()
        self._reiniciar_fecha("fecha_expediente")

    # ---------------- Recetas ----------------
    def guardar_receta(self):
        if self._val_fecha_futura("fecha_receta", "tabla_recetas", 2,
                                  "La fecha de emisión", False):
            return super().guardar_receta()

    def editar_receta(self):
        if self._val_fecha_futura("fecha_receta", "tabla_recetas", 2,
                                  "La fecha de emisión", True):
            return super().editar_receta()

    def limpiar_receta(self):
        super().limpiar_receta()
        self._reiniciar_fecha("fecha_receta")