from .common import *
from conexion import obtener_conexion
from sqlalchemy import select
from .Modelos import Especialidad
from .orm import obtener_sesion


class PersistenciaMixin:
    """Capa de persistencia SQL y autorización por rol para MediCore."""

    PERMISOS = {
        "Administrador": {"*": {"crear", "editar", "eliminar", "leer"}},
        "Administrativo": {
            "Pacientes": {"crear", "editar", "leer"},
            "Agenda": {"crear", "editar", "eliminar", "leer"},
            "Citas": {"crear", "editar", "eliminar", "leer"},
        },
        "Medico": {
            "Pacientes": {"leer"}, "Agenda": {"leer"}, "Citas": {"leer", "editar"},
            "Expedientes": {"leer"}, "Consultas": {"crear", "editar", "leer"},
            "Recetas": {"crear", "editar", "leer"}, "Detalle": {"crear", "editar", "eliminar", "leer"},
            "Medicamentos": {"leer"},
        },
    }

    def _db(self):
        conexion = obtener_conexion()
        if conexion is None:
            raise RuntimeError("No se pudo conectar con la base de datos MediCore.")
        return conexion

    def _permitir(self, modulo, accion):
        rol = (getattr(self, "usuario_actual", {}) or {}).get("Rol", "")
        permisos = self.PERMISOS.get(rol, {})
        if accion in permisos.get("*", set()) or accion in permisos.get(modulo, set()):
            return True
        QMessageBox.warning(self, "Acceso denegado", f"Tu rol ({rol or 'desconocido'}) no puede {accion} en {modulo.lower()}.")
        return False

    def _confirmar(self, titulo, mensaje, texto_si):
        """Cuadro de confirmación Sí/Cancelar. Por seguridad, el botón
        predeterminado (Enter o cerrar con Esc) es Cancelar."""
        cuadro = QMessageBox(self)
        cuadro.setIcon(QMessageBox.Icon.Question)
        cuadro.setWindowTitle(titulo)
        cuadro.setText(mensaje)
        boton_si = cuadro.addButton(texto_si, QMessageBox.ButtonRole.YesRole)
        boton_no = cuadro.addButton("Cancelar", QMessageBox.ButtonRole.NoRole)
        cuadro.setDefaultButton(boton_no)
        cuadro.setEscapeButton(boton_no)
        cuadro.exec()
        return cuadro.clickedButton() is boton_si

    def _confirmar_edicion(self, objeto):
        return self._confirmar(
            "Confirmar cambios",
            f"¿Estás seguro de que deseas guardar los cambios realizados en {objeto}?",
            "Sí, guardar cambios",
        )

    def _confirmar_eliminacion(self, objeto):
        return self._confirmar(
            "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar {objeto}?\n\nEsta acción no se puede deshacer.",
            "Sí, eliminar",
        )

    def _mensaje_error(self, titulo, error):
        QMessageBox.critical(self, titulo, str(error))

    @staticmethod
    def _item(tabla, fila, columna):
        item = tabla.item(fila, columna)
        return item.text() if item else ""

    @staticmethod
    def _cargar_tabla(tabla, filas):
        tabla.setRowCount(0)
        for registro in filas:
            fila = tabla.rowCount()
            tabla.insertRow(fila)
            for col, valor in enumerate(registro):
                tabla.setItem(fila, col, QTableWidgetItem("" if valor is None else str(valor)))

    @staticmethod
    def _id_seleccionado(tabla):
        fila = tabla.currentRow()
        if fila < 0:
            return None
        item = tabla.item(fila, 0)
        try:
            return int(item.text()) if item else None
        except (ValueError, AttributeError):
            return None

    # Pestaña -> nombre del módulo en PERMISOS
    MODULOS_PESTANAS = {
        "Especialidades": "Especialidades",
        "Médicos": "Médicos",
        "Pacientes": "Pacientes",
        "Agenda Horarios": "Agenda",
        "Citas Médicas": "Citas",
        "Expedientes Clínicos": "Expedientes",
        "Consultas Historial": "Consultas",
        "Recetas Médicas": "Recetas",
        "Medicamentos": "Medicamentos",
        "Detalle Receta": "Detalle",
        "Usuarios": "Usuarios",
    }

    # Texto del botón -> acción que necesita
    ACCIONES_BOTONES = {
        "Guardar": "crear",
        "Editar": "editar",
        "Eliminar": "eliminar",
    }

    @classmethod
    def _ocultar_layout(cls, layout):
        for posicion in range(layout.count()):
            item = layout.itemAt(posicion)
            widget = item.widget()

            if widget is not None:
                widget.hide()

            sublayout = item.layout()

            if sublayout is not None:
                cls._ocultar_layout(sublayout)

    def aplicar_permisos_interfaz(self):
        """Muestra en cada módulo solo lo que el rol puede usar:
        - Si el rol solo puede consultar, se oculta el formulario y los
          botones y queda únicamente la tabla con la información.
        - Si puede hacer algunas acciones, se ocultan solo los botones
          (Guardar / Editar / Eliminar) que no tiene permitidos."""
        rol = (getattr(self, "usuario_actual", {}) or {}).get("Rol", "")
        permisos = self.PERMISOS.get(rol, {})

        def permitido(modulo, accion):
            return (
                accion in permisos.get("*", set())
                or accion in permisos.get(modulo, set())
            )

        for indice in range(self.tabs.count()):
            modulo = self.MODULOS_PESTANAS.get(self.tabs.tabText(indice))
            pagina = self.tabs.widget(indice)
            layout = pagina.layout() if pagina is not None else None

            if modulo is None or layout is None:
                continue

            formulario = None
            botones = None

            for posicion in range(layout.count()):
                sublayout = layout.itemAt(posicion).layout()

                if sublayout is None:
                    continue

                if isinstance(sublayout, QHBoxLayout):
                    botones = sublayout
                else:
                    formulario = sublayout

            solo_lectura = not any(
                permitido(modulo, accion)
                for accion in ("crear", "editar", "eliminar")
            )

            if solo_lectura:
                for sublayout in (formulario, botones):
                    if sublayout is not None:
                        self._ocultar_layout(sublayout)
                continue

            if botones is None:
                continue

            for posicion in range(botones.count()):
                boton = botones.itemAt(posicion).widget()

                if boton is None:
                    continue

                accion = self.ACCIONES_BOTONES.get(boton.text())

                if accion and not permitido(modulo, accion):
                    boton.hide()

    def crear_interfaz(self):
        super().crear_interfaz()
        self.aplicar_permisos_interfaz()
        # Cargar la información desde MySQL después de crear todos los widgets.
        for metodo in (
            "actualizar_especialidades", "actualizar_medicos", "actualizar_pacientes",
            "actualizar_agenda", "actualizar_citas", "actualizar_expedientes",
            "actualizar_consultas", "actualizar_recetas", "actualizar_medicamentos",
            "actualizar_detalle_receta", "actualizar_usuarios",
        ):
            funcion = getattr(self, metodo, None)
            if callable(funcion):
                try:
                    funcion()
                except Exception as error:
                    print(f"Aviso al cargar {metodo}: {error}")

    # ---------------- ESPECIALIDADES (ORM - SQLAlchemy) ----------------
    def actualizar_especialidades(self):
        if not hasattr(self, "tabla_especialidades"):
            return
        try:
            with obtener_sesion() as sesion:
                especialidades = sesion.scalars(
                    select(Especialidad).order_by(Especialidad.id)
                ).all()
                self._cargar_tabla(
                    self.tabla_especialidades,
                    [(e.id, e.nombre) for e in especialidades],
                )
                if hasattr(self, "especialidad_medico"):
                    actual = self.especialidad_medico.currentData()
                    self.especialidad_medico.clear()
                    self.especialidad_medico.addItem("Seleccionar especialidad", None)
                    por_nombre = sesion.scalars(
                        select(Especialidad).order_by(Especialidad.nombre)
                    ).all()
                    for e in por_nombre:
                        self.especialidad_medico.addItem(e.nombre, e.id)
                    idx = self.especialidad_medico.findData(actual)
                    if idx >= 0:
                        self.especialidad_medico.setCurrentIndex(idx)
        except Exception as e:
            self._mensaje_error("Especialidades", e)

    def guardar_especialidad(self):
        if not self._permitir("Especialidades", "crear"): return
        nombre = self.nombre_especialidad.text().strip()
        if not nombre: QMessageBox.warning(self, "Validación", "Escribe el nombre de la especialidad."); return
        try:
            with obtener_sesion() as sesion:
                sesion.add(Especialidad(nombre=nombre))
                sesion.commit()
            self.limpiar_especialidad(); self.actualizar_especialidades(); self.actualizar_medicos()
        except Exception as e:
            self._mensaje_error("No se pudo guardar la especialidad", e)

    def editar_especialidad(self):
        if not self._permitir("Especialidades", "editar"): return
        ident = self._id_seleccionado(self.tabla_especialidades); nombre = self.nombre_especialidad.text().strip()
        if not ident or not nombre: QMessageBox.warning(self, "Validación", "Selecciona una especialidad y escribe el nombre."); return
        try:
            if not self._confirmar_edicion("la especialidad"): return
            with obtener_sesion() as sesion:
                especialidad = sesion.get(Especialidad, ident)
                if especialidad is None:
                    QMessageBox.warning(self, "Especialidades", "La especialidad ya no existe."); return
                especialidad.nombre = nombre
                sesion.commit()
            self.actualizar_especialidades(); self.actualizar_medicos()
        except Exception as e:
            self._mensaje_error("No se pudo editar la especialidad", e)

    def eliminar_especialidad(self):
        if not self._permitir("Especialidades", "eliminar"): return
        ident = self._id_seleccionado(self.tabla_especialidades)
        if not ident: QMessageBox.warning(self, "Seleccionar", "Selecciona una especialidad."); return
        if not self._confirmar_eliminacion("la especialidad seleccionada"): return
        try:
            with obtener_sesion() as sesion:
                especialidad = sesion.get(Especialidad, ident)
                if especialidad is not None:
                    sesion.delete(especialidad)
                    sesion.commit()
            self.actualizar_especialidades()
        except Exception as e:
            self._mensaje_error("No se pudo eliminar. Puede tener médicos asociados", e)

    # ---------------- MÉDICOS ----------------
    def actualizar_medicos(self):
        if not hasattr(self, "tabla_medicos"): return
        con = None
        try:
            con = self._db(); cur = con.cursor()
            cur.execute("SELECT m.ID_Medico,m.Codigo_MINSA,m.Nombre,e.Nombre_Especialidad,m.Turno FROM Medicos m JOIN Especialidades_Medicas e ON e.ID_Especialidad=m.ID_Especialidad ORDER BY m.ID_Medico")
            self._cargar_tabla(self.tabla_medicos, cur.fetchall())
            for attr in ("medico_agenda", "medico_cita", "medico_consulta"):
                combo = getattr(self, attr, None)
                if combo is None: continue
                keep = combo.currentData(); combo.clear(); combo.addItem("Seleccionar médico", None)
                cur.execute("SELECT ID_Medico, Nombre FROM Medicos ORDER BY Nombre")
                for ident, nombre in cur.fetchall():
                    if self.usuario_actual.get("Rol") == "Medico" and self.usuario_actual.get("ID_Medico") and ident != self.usuario_actual.get("ID_Medico"):
                        continue
                    combo.addItem(nombre, ident)
                idx = combo.findData(keep)
                if idx >= 0: combo.setCurrentIndex(idx)
            self.actualizar_especialidades()
        except Exception as e: self._mensaje_error("Médicos", e)
        finally:
            if con: con.close()

    def guardar_medico(self):
        if not self._permitir("Médicos", "crear"): return
        codigo=self.codigo_minsa.text().strip(); nombre=self.nombre_medico.text().strip(); esp=self.especialidad_medico.currentData(); turno=self.turno_medico.currentText()
        if not codigo or not nombre or esp is None: QMessageBox.warning(self,"Validación","Completa código, nombre y especialidad."); return
        con=None
        try:
            con=self._db(); cur=con.cursor(); cur.execute("INSERT INTO Medicos (Codigo_MINSA,Nombre,ID_Especialidad,Turno) VALUES (%s,%s,%s,%s)",(codigo,nombre,esp,turno)); con.commit(); self.limpiar_medico(); self.actualizar_medicos(); self.actualizar_agenda(); self.actualizar_citas()
        except Exception as e:
            if con: con.rollback()
            self._mensaje_error("No se pudo guardar el médico",e)
        finally:
            if con: con.close()

    def editar_medico(self):
        if not self._permitir("Médicos", "editar"): return
        ident=self._id_seleccionado(self.tabla_medicos); codigo=self.codigo_minsa.text().strip(); nombre=self.nombre_medico.text().strip(); esp=self.especialidad_medico.currentData()
        if not ident or not codigo or not nombre or esp is None: QMessageBox.warning(self,"Validación","Selecciona un médico y completa los campos."); return
        con=None
        try:
            if not self._confirmar_edicion("el médico"): return
            con=self._db(); cur=con.cursor(); cur.execute("UPDATE Medicos SET Codigo_MINSA=%s,Nombre=%s,ID_Especialidad=%s,Turno=%s WHERE ID_Medico=%s",(codigo,nombre,esp,self.turno_medico.currentText(),ident)); con.commit(); self.actualizar_medicos(); self.actualizar_agenda(); self.actualizar_citas()
        except Exception as e:
            if con: con.rollback()
            self._mensaje_error("No se pudo editar el médico",e)
        finally:
            if con: con.close()

    def eliminar_medico(self):
        if not self._permitir("Médicos", "eliminar"): return
        ident=self._id_seleccionado(self.tabla_medicos)
        if not ident: QMessageBox.warning(self,"Seleccionar","Selecciona un médico."); return
        if not self._confirmar_eliminacion("el médico seleccionado"): return
        con=None
        try:
            con=self._db(); cur=con.cursor(); cur.execute("DELETE FROM Medicos WHERE ID_Medico=%s",(ident,)); con.commit(); self.actualizar_medicos()
        except Exception as e:
            if con: con.rollback()
            self._mensaje_error("No se pudo eliminar el médico; verifica si tiene registros relacionados",e)
        finally:
            if con: con.close()

    # ---------------- PACIENTES ----------------
    def actualizar_pacientes(self):
        if not hasattr(self,"tabla_pacientes"): return
        con=None
        try:
            con=self._db(); cur=con.cursor(); cur.execute("SELECT ID_Paciente,COALESCE(Cedula,'Sin cédula'),Nombre,Fecha_Nacimiento,COALESCE(Sexo,'Sin definir'),Tipo_Sangre,COALESCE(Alergias,'Ninguna') FROM Pacientes ORDER BY ID_Paciente")
            filas=cur.fetchall(); self._cargar_tabla(self.tabla_pacientes,filas)
            for attr in ("paciente_cita","paciente_expediente"):
                combo=getattr(self,attr,None)
                if combo is None: continue
                keep=combo.currentData(); combo.clear(); combo.addItem("Seleccionar paciente",None)
                for r in filas: combo.addItem(r[2],r[0])
                idx=combo.findData(keep)
                if idx>=0: combo.setCurrentIndex(idx)
        except Exception as e:self._mensaje_error("Pacientes",e)
        finally:
            if con:con.close()

    def guardar_paciente(self):
        if not self._permitir("Pacientes","crear"):return
        ced=self.cedula_paciente.text().strip() or None; nom=self.nombre_paciente.text().strip(); fecha=self.fecha_nacimiento.date().toString("yyyy-MM-dd"); sexo=self.sexo_paciente.currentText(); sangre=self.tipo_sangre.currentText(); alergias=self.alergias_paciente.toPlainText().strip() or "Ninguna"
        if not nom:QMessageBox.warning(self,"Validación","Completa el nombre del paciente.");return
        con=None
        try:
            con=self._db();cur=con.cursor();cur.execute("INSERT INTO Pacientes(Cedula,Nombre,Fecha_Nacimiento,Sexo,Tipo_Sangre,Alergias) VALUES(%s,%s,%s,%s,%s,%s)",(ced,nom,fecha,sexo,sangre,alergias));con.commit();self.limpiar_paciente();self.actualizar_pacientes()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("No se pudo guardar el paciente",e)
        finally:
            if con:con.close()

    def editar_paciente(self):
        if not self._permitir("Pacientes","editar"):return
        ident=self._id_seleccionado(self.tabla_pacientes);ced=self.cedula_paciente.text().strip() or None;nom=self.nombre_paciente.text().strip();fecha=self.fecha_nacimiento.date().toString("yyyy-MM-dd");sexo=self.sexo_paciente.currentText();sangre=self.tipo_sangre.currentText();alergias=self.alergias_paciente.toPlainText().strip() or "Ninguna"
        if not ident or not nom:QMessageBox.warning(self,"Validación","Selecciona un paciente y completa los campos.");return
        con=None
        try:
            if not self._confirmar_edicion("el paciente"): return
            con=self._db();cur=con.cursor();cur.execute("UPDATE Pacientes SET Cedula=%s,Nombre=%s,Fecha_Nacimiento=%s,Sexo=%s,Tipo_Sangre=%s,Alergias=%s WHERE ID_Paciente=%s",(ced,nom,fecha,sexo,sangre,alergias,ident));con.commit();self.actualizar_pacientes();self.actualizar_expedientes();self.actualizar_citas()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("No se pudo editar el paciente",e)
        finally:
            if con:con.close()

    def eliminar_paciente(self):
        if not self._permitir("Pacientes","eliminar"):return
        ident=self._id_seleccionado(self.tabla_pacientes)
        if not ident:QMessageBox.warning(self,"Seleccionar","Selecciona un paciente.");return
        if not self._confirmar_eliminacion("el paciente seleccionado"): return
        con=None
        try:
            con=self._db();cur=con.cursor();cur.execute("DELETE FROM Pacientes WHERE ID_Paciente=%s",(ident,));con.commit();self.actualizar_pacientes()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("No se pudo eliminar; el paciente puede tener citas o expediente",e)
        finally:
            if con:con.close()

    # ---------------- AGENDA ----------------
    def actualizar_agenda(self):
        if not hasattr(self,"tabla_agenda"):return
        con=None
        try:
            con=self._db();cur=con.cursor();sql="SELECT a.ID_Agenda,m.Nombre,a.Dia_Semana,LEFT(CAST(a.Hora_Inicio AS CHAR),5),LEFT(CAST(a.Hora_Fin AS CHAR),5),IF(a.Horario_Especial=1,'Especial','Regular') FROM Agenda_Horarios a JOIN Medicos m ON m.ID_Medico=a.ID_Medico"; vals=()
            if self.usuario_actual.get("Rol")=="Medico": sql += " WHERE a.ID_Medico=%s"; vals=(self.usuario_actual.get("ID_Medico"),)
            sql += " ORDER BY a.ID_Agenda";cur.execute(sql,vals);self._cargar_tabla(self.tabla_agenda,cur.fetchall())
            if hasattr(self,"medico_agenda"):
                keep=self.medico_agenda.currentData();self.medico_agenda.clear();self.medico_agenda.addItem("Seleccionar médico",None);cur.execute("SELECT ID_Medico,Nombre FROM Medicos ORDER BY Nombre")
                for i,n in cur.fetchall():
                    if self.usuario_actual.get("Rol")!="Medico" or i==self.usuario_actual.get("ID_Medico"):self.medico_agenda.addItem(n,i)
                idx=self.medico_agenda.findData(keep)
                if idx>=0:self.medico_agenda.setCurrentIndex(idx)
        except Exception as e:self._mensaje_error("Agenda",e)
        finally:
            if con:con.close()

    def guardar_agenda(self):
        if not self._permitir("Agenda","crear"):return
        medico=self.medico_agenda.currentData();ini=self.hora_inicio_agenda.time();fin=self.hora_fin_agenda.time()
        if medico is None or ini>=fin:QMessageBox.warning(self,"Validación","Selecciona médico y comprueba las horas.");return
        if self.usuario_actual.get("Rol")=="Medico" and medico!=self.usuario_actual.get("ID_Medico"):QMessageBox.warning(self,"Permiso","Solo puedes gestionar tu agenda.");return
        con=None
        try:
            con=self._db();cur=con.cursor();cur.execute("INSERT INTO Agenda_Horarios(ID_Medico,Dia_Semana,Hora_Inicio,Hora_Fin,Horario_Especial) VALUES(%s,%s,%s,%s,%s)",(medico,self.dia_agenda.currentText(),ini.toString("HH:mm:ss"),fin.toString("HH:mm:ss"),1 if self.horario_especial.isChecked() else 0));con.commit();self.actualizar_agenda()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("Agenda",e)
        finally:
            if con:con.close()

    def editar_agenda(self):
        if not self._permitir("Agenda","editar"):return
        ident=self._id_seleccionado(self.tabla_agenda);medico=self.medico_agenda.currentData();ini=self.hora_inicio_agenda.time();fin=self.hora_fin_agenda.time()
        if not ident or medico is None or ini>=fin:QMessageBox.warning(self,"Validación","Selecciona un horario válido.");return
        con=None
        try:
            if not self._confirmar_edicion("el horario"): return
            con=self._db();cur=con.cursor();cur.execute("UPDATE Agenda_Horarios SET ID_Medico=%s,Dia_Semana=%s,Hora_Inicio=%s,Hora_Fin=%s,Horario_Especial=%s WHERE ID_Agenda=%s",(medico,self.dia_agenda.currentText(),ini.toString("HH:mm:ss"),fin.toString("HH:mm:ss"),1 if self.horario_especial.isChecked() else 0,ident));con.commit();self.actualizar_agenda()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("Agenda",e)
        finally:
            if con:con.close()

    def eliminar_agenda(self):
        if not self._permitir("Agenda","eliminar"):return
        ident=self._id_seleccionado(self.tabla_agenda)
        if not ident:return
        con=None
        try:
            if not self._confirmar_eliminacion("este horario"): return
            con=self._db();cur=con.cursor();cur.execute("DELETE FROM Agenda_Horarios WHERE ID_Agenda=%s",(ident,));con.commit();self.actualizar_agenda()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("Agenda",e)
        finally:
            if con:con.close()

    # ---------------- MEDICAMENTOS ----------------
    def actualizar_medicamentos(self):
        if not hasattr(self,"tabla_medicamentos"):return
        con=None
        try:
            con=self._db();cur=con.cursor();cur.execute("SELECT ID_Medicamento,Nombre_Medicamento,Presentacion,Existencia FROM Medicamentos_Catalogo ORDER BY ID_Medicamento");self._cargar_tabla(self.tabla_medicamentos,cur.fetchall())
            if hasattr(self,"medicamento_detalle"):
                keep=self.medicamento_detalle.currentData();self.medicamento_detalle.clear();self.medicamento_detalle.addItem("Seleccionar medicamento",None);cur.execute("SELECT ID_Medicamento,Nombre_Medicamento FROM Medicamentos_Catalogo ORDER BY Nombre_Medicamento")
                for i,n in cur.fetchall():self.medicamento_detalle.addItem(n,i)
                idx=self.medicamento_detalle.findData(keep)
                if idx>=0:self.medicamento_detalle.setCurrentIndex(idx)
        except Exception as e:self._mensaje_error("Medicamentos",e)
        finally:
            if con:con.close()

    def guardar_medicamento(self):
        if not self._permitir("Medicamentos","crear"):return
        n=self.nombre_medicamento.text().strip();p=self.presentacion_medicamento.text().strip();ex=self.existencia_medicamento.value()
        if not n or not p:QMessageBox.warning(self,"Validación","Completa nombre y presentación.");return
        con=None
        try:
            con=self._db();cur=con.cursor();cur.execute("INSERT INTO Medicamentos_Catalogo(Nombre_Medicamento,Presentacion,Existencia) VALUES(%s,%s,%s)",(n,p,ex));con.commit();self.limpiar_medicamento();self.actualizar_medicamentos();self.actualizar_detalle_receta()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("Medicamentos",e)
        finally:
            if con:con.close()

    def editar_medicamento(self):
        if not self._permitir("Medicamentos","editar"):return
        i=self._id_seleccionado(self.tabla_medicamentos);n=self.nombre_medicamento.text().strip();p=self.presentacion_medicamento.text().strip();ex=self.existencia_medicamento.value()
        if not i or not n or not p:QMessageBox.warning(self,"Validación","Selecciona un medicamento y completa los campos.");return
        con=None
        try:
            if not self._confirmar_edicion("el medicamento"): return
            con=self._db();cur=con.cursor();cur.execute("UPDATE Medicamentos_Catalogo SET Nombre_Medicamento=%s,Presentacion=%s,Existencia=%s WHERE ID_Medicamento=%s",(n,p,ex,i));con.commit();self.actualizar_medicamentos();self.actualizar_detalle_receta()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("Medicamentos",e)
        finally:
            if con:con.close()

    def eliminar_medicamento(self):
        if not self._permitir("Medicamentos","eliminar"):return
        i=self._id_seleccionado(self.tabla_medicamentos)
        if not i:return
        con=None
        try:
            if not self._confirmar_eliminacion("este medicamento"): return
            con=self._db();cur=con.cursor();cur.execute("DELETE FROM Medicamentos_Catalogo WHERE ID_Medicamento=%s",(i,));con.commit();self.actualizar_medicamentos()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("No se pudo eliminar el medicamento; puede estar en una receta",e)
        finally:
            if con:con.close()

    # ---------------- CONSULTAS CLÍNICAS ----------------
    def actualizar_consultas(self):
        if not hasattr(self,"tabla_consultas"):return
        con=None
        try:
            con=self._db();cur=con.cursor();sql="""SELECT c.ID_Consulta, CONCAT('Exp. ',e.ID_Expediente,' - ',p.Nombre),m.Nombre,c.ID_Cita,c.Fecha_Consulta,c.Presion_Arterial,c.Peso,c.Sintomas,c.Diagnostico FROM Consultas_Historial c JOIN Expedientes_Clinicos e ON e.ID_Expediente=c.ID_Expediente JOIN Pacientes p ON p.ID_Paciente=e.ID_Paciente JOIN Medicos m ON m.ID_Medico=c.ID_Medico""";params=()
            if self.usuario_actual.get("Rol")=="Medico":sql+=" WHERE c.ID_Medico=%s";params=(self.usuario_actual.get("ID_Medico"),)
            sql+=" ORDER BY c.ID_Consulta DESC";cur.execute(sql,params);self._cargar_tabla(self.tabla_consultas,cur.fetchall())
            self.expediente_consulta.clear();self.expediente_consulta.addItem("Seleccionar expediente",None)
            cur.execute("SELECT e.ID_Expediente,p.Nombre FROM Expedientes_Clinicos e JOIN Pacientes p ON p.ID_Paciente=e.ID_Paciente ORDER BY p.Nombre")
            for i,n in cur.fetchall():self.expediente_consulta.addItem(f"{n} (Exp. {i})",i)
            self.medico_consulta.clear();self.medico_consulta.addItem("Seleccionar médico",None)
            cur.execute("SELECT ID_Medico,Nombre FROM Medicos ORDER BY Nombre")
            for i,n in cur.fetchall():
                if self.usuario_actual.get("Rol")!="Medico" or i==self.usuario_actual.get("ID_Medico"):self.medico_consulta.addItem(n,i)
            self.cita_consulta.clear();self.cita_consulta.addItem("Seleccionar cita",None)
            sql="SELECT c.ID_Cita,p.Nombre,c.Fecha,c.Hora FROM Citas_Medicas c JOIN Pacientes p ON p.ID_Paciente=c.ID_Paciente WHERE c.Estado='Asistio' AND NOT EXISTS (SELECT 1 FROM Consultas_Historial h WHERE h.ID_Cita=c.ID_Cita)";vals=()
            if self.usuario_actual.get("Rol")=="Medico":sql+=" AND c.ID_Medico=%s";vals=(self.usuario_actual.get("ID_Medico"),)
            sql+=" ORDER BY c.Fecha DESC,c.Hora DESC";cur.execute(sql,vals)
            for i,n,f,h in cur.fetchall():self.cita_consulta.addItem(f"#{i} - {n} - {f} {h}",i)
        except Exception as e:self._mensaje_error("Consultas clínicas",e)
        finally:
            if con:con.close()

    def guardar_consulta(self):
        if not self._permitir("Consultas","crear"):return
        exp=self.expediente_consulta.currentData();med=self.medico_consulta.currentData();cita=self.cita_consulta.currentData();pres=self.presion_consulta.text().strip();peso=self.peso_consulta.value();sint=self.sintomas_consulta.toPlainText().strip();diag=self.diagnostico_consulta.toPlainText().strip();fecha=self.fecha_consulta.date().toString("yyyy-MM-dd")
        if None in (exp,med,cita) or not pres or not sint or not diag:QMessageBox.warning(self,"Validación","Completa expediente, médico, cita, presión, síntomas y diagnóstico.");return
        if self.usuario_actual.get("Rol")=="Medico" and med!=self.usuario_actual.get("ID_Medico"):QMessageBox.warning(self,"Permiso","Solo puedes registrar consultas con tu usuario médico.");return
        con=None
        try:
            con=self._db();cur=con.cursor();cur.execute("INSERT INTO Consultas_Historial(ID_Expediente,ID_Medico,ID_Cita,Fecha_Consulta,Presion_Arterial,Peso,Sintomas,Diagnostico) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(exp,med,cita,fecha,pres,peso,sint,diag));con.commit();self.limpiar_consulta();self.actualizar_consultas();self.actualizar_recetas()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("No se pudo guardar la consulta",e)
        finally:
            if con:con.close()

    def editar_consulta(self):
        if not self._permitir("Consultas","editar"):return
        i=self._id_seleccionado(self.tabla_consultas);exp=self.expediente_consulta.currentData();med=self.medico_consulta.currentData();cita=self.cita_consulta.currentData();pres=self.presion_consulta.text().strip();peso=self.peso_consulta.value();sint=self.sintomas_consulta.toPlainText().strip();diag=self.diagnostico_consulta.toPlainText().strip();fecha=self.fecha_consulta.date().toString("yyyy-MM-dd")
        if not i or None in (exp,med,cita) or not pres or not sint or not diag:QMessageBox.warning(self,"Validación","Selecciona una consulta y completa todos los campos.");return
        if self.usuario_actual.get("Rol")=="Medico":
            con0=None
            try:
                con0=self._db();c0=con0.cursor();c0.execute("SELECT ID_Medico FROM Consultas_Historial WHERE ID_Consulta=%s",(i,));r=c0.fetchone()
                if not r or r[0]!=self.usuario_actual.get("ID_Medico"):QMessageBox.warning(self,"Permiso","Solo puedes editar tus consultas.");return
            finally:
                if con0:con0.close()
        con=None
        try:
            if not self._confirmar_edicion("la consulta"): return
            con=self._db();cur=con.cursor();cur.execute("UPDATE Consultas_Historial SET ID_Expediente=%s,ID_Medico=%s,ID_Cita=%s,Fecha_Consulta=%s,Presion_Arterial=%s,Peso=%s,Sintomas=%s,Diagnostico=%s WHERE ID_Consulta=%s",(exp,med,cita,fecha,pres,peso,sint,diag,i));con.commit();self.actualizar_consultas()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("No se pudo editar la consulta",e)
        finally:
            if con:con.close()

    def eliminar_consulta(self):
        if not self._permitir("Consultas","eliminar"):return
        i=self._id_seleccionado(self.tabla_consultas)
        if not i:return
        con=None
        try:
            con=self._db();cur=con.cursor()
            if self.usuario_actual.get("Rol")=="Medico":
                cur.execute("SELECT ID_Medico FROM Consultas_Historial WHERE ID_Consulta=%s",(i,));r=cur.fetchone()
                if not r or r[0]!=self.usuario_actual.get("ID_Medico"):QMessageBox.warning(self,"Permiso","Solo puedes eliminar tus consultas.");return
            if not self._confirmar_eliminacion("esta consulta"): return
            cur.execute("DELETE FROM Consultas_Historial WHERE ID_Consulta=%s",(i,));con.commit();self.actualizar_consultas()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("No se pudo eliminar la consulta; puede tener una receta relacionada",e)
        finally:
            if con:con.close()

    # ---------------- RECETAS ----------------
    def actualizar_recetas(self):
        if not hasattr(self,"tabla_recetas"):return
        con=None
        try:
            con=self._db();cur=con.cursor();sql="SELECT r.ID_Receta,CONCAT('Consulta #',c.ID_Consulta,' - ',p.Nombre),r.Fecha_Emision FROM Recetas_Medicas r JOIN Consultas_Historial c ON c.ID_Consulta=r.ID_Consulta JOIN Expedientes_Clinicos e ON e.ID_Expediente=c.ID_Expediente JOIN Pacientes p ON p.ID_Paciente=e.ID_Paciente";vals=()
            if self.usuario_actual.get("Rol")=="Medico":sql+=" WHERE c.ID_Medico=%s";vals=(self.usuario_actual.get("ID_Medico"),)
            sql+=" ORDER BY r.ID_Receta DESC";cur.execute(sql,vals);self._cargar_tabla(self.tabla_recetas,cur.fetchall())
            keep=self.consulta_receta.currentData();self.consulta_receta.clear();self.consulta_receta.addItem("Seleccionar consulta",None)
            sql="SELECT c.ID_Consulta,p.Nombre,c.Fecha_Consulta FROM Consultas_Historial c JOIN Expedientes_Clinicos e ON e.ID_Expediente=c.ID_Expediente JOIN Pacientes p ON p.ID_Paciente=e.ID_Paciente WHERE NOT EXISTS(SELECT 1 FROM Recetas_Medicas r WHERE r.ID_Consulta=c.ID_Consulta)";vals=()
            if self.usuario_actual.get("Rol")=="Medico":sql+=" AND c.ID_Medico=%s";vals=(self.usuario_actual.get("ID_Medico"),)
            sql+=" ORDER BY c.Fecha_Consulta DESC";cur.execute(sql,vals)
            for i,n,f in cur.fetchall():self.consulta_receta.addItem(f"Consulta #{i} - {n} ({f})",i)
            idx=self.consulta_receta.findData(keep)
            if idx>=0:self.consulta_receta.setCurrentIndex(idx)
        except Exception as e:self._mensaje_error("Recetas",e)
        finally:
            if con:con.close()

    def guardar_receta(self):
        if not self._permitir("Recetas","crear"):return
        consulta=self.consulta_receta.currentData();fecha=self.fecha_receta.date().toString("yyyy-MM-dd")
        if consulta is None:QMessageBox.warning(self,"Validación","Selecciona una consulta.");return
        con=None
        try:
            con=self._db();cur=con.cursor()
            if self.usuario_actual.get("Rol")=="Medico":
                cur.execute("SELECT ID_Medico FROM Consultas_Historial WHERE ID_Consulta=%s",(consulta,));r=cur.fetchone()
                if not r or r[0]!=self.usuario_actual.get("ID_Medico"):QMessageBox.warning(self,"Permiso","Solo puedes emitir recetas para tus consultas.");return
            cur.execute("INSERT INTO Recetas_Medicas(ID_Consulta,Fecha_Emision) VALUES(%s,%s)",(consulta,fecha));con.commit();self.limpiar_receta();self.actualizar_recetas();self.actualizar_detalle_receta()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("No se pudo guardar la receta",e)
        finally:
            if con:con.close()

    def editar_receta(self):
        if not self._permitir("Recetas","editar"):return
        i=self._id_seleccionado(self.tabla_recetas);consulta=self.consulta_receta.currentData();fecha=self.fecha_receta.date().toString("yyyy-MM-dd")
        if not i or consulta is None:QMessageBox.warning(self,"Validación","Selecciona una receta y una consulta.");return
        con=None
        try:
            con=self._db();cur=con.cursor()
            if self.usuario_actual.get("Rol")=="Medico":
                cur.execute("SELECT c.ID_Medico FROM Recetas_Medicas r JOIN Consultas_Historial c ON c.ID_Consulta=r.ID_Consulta WHERE r.ID_Receta=%s",(i,));r=cur.fetchone()
                if not r or r[0]!=self.usuario_actual.get("ID_Medico"):QMessageBox.warning(self,"Permiso","Solo puedes editar tus recetas.");return
            if not self._confirmar_edicion("la receta"): return
            cur.execute("UPDATE Recetas_Medicas SET ID_Consulta=%s,Fecha_Emision=%s WHERE ID_Receta=%s",(consulta,fecha,i));con.commit();self.actualizar_recetas()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("No se pudo editar la receta",e)
        finally:
            if con:con.close()

    def eliminar_receta(self):
        if not self._permitir("Recetas","eliminar"):return
        i=self._id_seleccionado(self.tabla_recetas)
        if not i:return
        con=None
        try:
            con=self._db();cur=con.cursor()
            if self.usuario_actual.get("Rol")=="Medico":
                cur.execute("SELECT c.ID_Medico FROM Recetas_Medicas r JOIN Consultas_Historial c ON c.ID_Consulta=r.ID_Consulta WHERE r.ID_Receta=%s",(i,));r=cur.fetchone()
                if not r or r[0]!=self.usuario_actual.get("ID_Medico"):QMessageBox.warning(self,"Permiso","Solo puedes eliminar tus recetas.");return
            if not self._confirmar_eliminacion("esta receta"): return
            # Al borrar la receta se devuelve al stock lo que se había recetado.
            cur.execute("UPDATE Medicamentos_Catalogo mc JOIN Detalle_Receta d ON d.ID_Medicamento=mc.ID_Medicamento SET mc.Existencia=mc.Existencia+d.Cantidad WHERE d.ID_Receta=%s",(i,))
            cur.execute("DELETE FROM Recetas_Medicas WHERE ID_Receta=%s",(i,));con.commit();self.actualizar_recetas();self.actualizar_detalle_receta();self.actualizar_medicamentos()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("No se pudo eliminar la receta",e)
        finally:
            if con:con.close()

    # ---------------- DETALLE DE RECETA ----------------
    def actualizar_detalle_receta(self):
        if not hasattr(self,"tabla_detalle_receta"):return
        con=None
        try:
            con=self._db();cur=con.cursor();sql="SELECT d.ID_Receta,d.ID_Medicamento,d.Dosis_Indicada,d.Frecuencia,d.Duracion,d.Cantidad,p.Nombre,mc.Nombre_Medicamento FROM Detalle_Receta d JOIN Recetas_Medicas r ON r.ID_Receta=d.ID_Receta JOIN Consultas_Historial c ON c.ID_Consulta=r.ID_Consulta JOIN Expedientes_Clinicos e ON e.ID_Expediente=c.ID_Expediente JOIN Pacientes p ON p.ID_Paciente=e.ID_Paciente JOIN Medicamentos_Catalogo mc ON mc.ID_Medicamento=d.ID_Medicamento";vals=()
            if self.usuario_actual.get("Rol")=="Medico":sql+=" WHERE c.ID_Medico=%s";vals=(self.usuario_actual.get("ID_Medico"),)
            sql+=" ORDER BY d.ID_Receta,d.ID_Medicamento";cur.execute(sql,vals);filas=cur.fetchall();self._cargar_tabla(self.tabla_detalle_receta,[(f[0],f[1],f[2],f[3],f[4],f[5]) for f in filas])
            # Paciente y medicamento: no se ven en la tabla, pero el buscador los encuentra.
            for pos,f in enumerate(filas):
                it_receta=self.tabla_detalle_receta.item(pos,0);it_med=self.tabla_detalle_receta.item(pos,1)
                if it_receta:it_receta.setData(Qt.ItemDataRole.UserRole+50,f[6]);it_receta.setToolTip(f"Paciente: {f[6]}")
                if it_med:it_med.setData(Qt.ItemDataRole.UserRole+50,f[7]);it_med.setToolTip(f"Medicamento: {f[7]}")
            receta_actual=self.receta_detalle.currentData();self.receta_detalle.clear();self.receta_detalle.addItem("Seleccionar receta",None)
            sql="SELECT r.ID_Receta,p.Nombre FROM Recetas_Medicas r JOIN Consultas_Historial c ON c.ID_Consulta=r.ID_Consulta JOIN Expedientes_Clinicos e ON e.ID_Expediente=c.ID_Expediente JOIN Pacientes p ON p.ID_Paciente=e.ID_Paciente";vals=()
            if self.usuario_actual.get("Rol")=="Medico":sql+=" WHERE c.ID_Medico=%s";vals=(self.usuario_actual.get("ID_Medico"),)
            sql+=" ORDER BY r.ID_Receta DESC";cur.execute(sql,vals)
            for i,n in cur.fetchall():self.receta_detalle.addItem(f"Receta #{i} - {n}",i)
            idx_receta=self.receta_detalle.findData(receta_actual)
            if idx_receta>=0:self.receta_detalle.setCurrentIndex(idx_receta)
            keep=self.medicamento_detalle.currentData();self.medicamento_detalle.clear();self.medicamento_detalle.addItem("Seleccionar medicamento",None);cur.execute("SELECT ID_Medicamento,Nombre_Medicamento,Existencia FROM Medicamentos_Catalogo ORDER BY Nombre_Medicamento")
            for i,n,ex in cur.fetchall():self.medicamento_detalle.addItem(f"{n} ({ex} disponibles)",i)
            idx=self.medicamento_detalle.findData(keep)
            if idx>=0:self.medicamento_detalle.setCurrentIndex(idx)
        except Exception as e:self._mensaje_error("Detalle de receta",e)
        finally:
            if con:con.close()

    # ----- Control de existencias (stock) al recetar -----
    def _stock_medicamento(self, cur, med):
        """Bloquea la fila del medicamento y devuelve (nombre, existencia)."""
        cur.execute("SELECT Nombre_Medicamento,Existencia FROM Medicamentos_Catalogo WHERE ID_Medicamento=%s FOR UPDATE",(med,))
        return cur.fetchone()

    def _aviso_sin_stock(self, nombre, disponible, pedido):
        QMessageBox.warning(self,"Existencia insuficiente",
            f"No hay suficiente existencia de {nombre}.\n\n"
            f"Disponible: {disponible} unidades\n"
            f"Cantidad solicitada: {pedido} unidades")

    def guardar_detalle_receta(self):
        if not self._permitir("Detalle","crear"):return
        rec=self.receta_detalle.currentData();med=self.medicamento_detalle.currentData();dosis=self.dosis_detalle.text().strip();frec=self.frecuencia_detalle.text().strip();dur=self.duracion_detalle.text().strip();cant=self.cantidad_detalle.value()
        if None in (rec,med) or not dosis or not frec or not dur:QMessageBox.warning(self,"Validación","Selecciona receta y medicamento y completa dosis, frecuencia y duración.");return
        if cant<=0:QMessageBox.warning(self,"Validación","La cantidad debe ser mayor que 0.");return
        con=None
        try:
            con=self._db();cur=con.cursor()
            if self.usuario_actual.get("Rol")=="Medico":
                cur.execute("SELECT c.ID_Medico FROM Recetas_Medicas r JOIN Consultas_Historial c ON c.ID_Consulta=r.ID_Consulta WHERE r.ID_Receta=%s",(rec,));r=cur.fetchone()
                if not r or r[0]!=self.usuario_actual.get("ID_Medico"):QMessageBox.warning(self,"Permiso","Solo puedes editar el detalle de tus recetas.");return
            stock=self._stock_medicamento(cur,med)
            if stock is None:con.rollback();QMessageBox.warning(self,"Medicamento","El medicamento seleccionado ya no existe.");return
            if stock[1]<cant:con.rollback();self._aviso_sin_stock(stock[0],stock[1],cant);return
            cur.execute("INSERT INTO Detalle_Receta(ID_Receta,ID_Medicamento,Dosis_Indicada,Frecuencia,Duracion,Cantidad) VALUES(%s,%s,%s,%s,%s,%s)",(rec,med,dosis,frec,dur,cant))
            cur.execute("UPDATE Medicamentos_Catalogo SET Existencia=Existencia-%s WHERE ID_Medicamento=%s",(cant,med))
            con.commit();self.actualizar_detalle_receta();self.actualizar_medicamentos()
            self.medicamento_detalle.setCurrentIndex(0);self.dosis_detalle.clear();self.frecuencia_detalle.clear();self.duracion_detalle.clear();self.cantidad_detalle.setValue(1)
        except Exception as e:
            if con:con.rollback()
            if getattr(e,"errno",None)==1062:
                QMessageBox.warning(self,"Medicamento repetido","Ese medicamento ya está en esta receta.\nPara cambiar su dosis, frecuencia, duración o cantidad, selecciónalo en la tabla y usa Editar.")
            else:
                self._mensaje_error("No se pudo guardar el detalle",e)
        finally:
            if con:con.close()

    def editar_detalle_receta(self):
        if not self._permitir("Detalle","editar"):return
        fila=self.tabla_detalle_receta.currentRow();rec=self.receta_detalle.currentData();med=self.medicamento_detalle.currentData();dosis=self.dosis_detalle.text().strip();frec=self.frecuencia_detalle.text().strip();dur=self.duracion_detalle.text().strip();cant=self.cantidad_detalle.value()
        if fila<0 or rec is None or med is None or not dosis or not frec or not dur:QMessageBox.warning(self,"Validación","Selecciona un detalle y completa los campos.");return
        if cant<=0:QMessageBox.warning(self,"Validación","La cantidad debe ser mayor que 0.");return
        oldrec=int(self._item(self.tabla_detalle_receta,fila,0));oldmed=int(self._item(self.tabla_detalle_receta,fila,1));con=None
        try:
            con=self._db();cur=con.cursor()
            if self.usuario_actual.get("Rol")=="Medico":
                cur.execute("SELECT c.ID_Medico FROM Recetas_Medicas r JOIN Consultas_Historial c ON c.ID_Consulta=r.ID_Consulta WHERE r.ID_Receta=%s",(oldrec,));r=cur.fetchone()
                if not r or r[0]!=self.usuario_actual.get("ID_Medico"):QMessageBox.warning(self,"Permiso","No puedes modificar una receta ajena.");return
            if not self._confirmar_edicion("el detalle de la receta"): return
            cur.execute("SELECT Cantidad FROM Detalle_Receta WHERE ID_Receta=%s AND ID_Medicamento=%s FOR UPDATE",(oldrec,oldmed));previo=cur.fetchone()
            if previo is None:
                con.rollback();QMessageBox.warning(self,"Registro no encontrado","El detalle ya no existe.");self.actualizar_detalle_receta();return
            # Primero se devuelve al stock lo que tenía la línea anterior...
            cur.execute("UPDATE Medicamentos_Catalogo SET Existencia=Existencia+%s WHERE ID_Medicamento=%s",(previo[0],oldmed))
            # ...y luego se descuenta lo nuevo (si no alcanza, se cancela todo).
            stock=self._stock_medicamento(cur,med)
            if stock is None:con.rollback();QMessageBox.warning(self,"Medicamento","El medicamento seleccionado ya no existe.");return
            if stock[1]<cant:con.rollback();self._aviso_sin_stock(stock[0],stock[1],cant);return
            cur.execute("DELETE FROM Detalle_Receta WHERE ID_Receta=%s AND ID_Medicamento=%s",(oldrec,oldmed))
            cur.execute("INSERT INTO Detalle_Receta(ID_Receta,ID_Medicamento,Dosis_Indicada,Frecuencia,Duracion,Cantidad) VALUES(%s,%s,%s,%s,%s,%s)",(rec,med,dosis,frec,dur,cant))
            cur.execute("UPDATE Medicamentos_Catalogo SET Existencia=Existencia-%s WHERE ID_Medicamento=%s",(cant,med))
            con.commit();self.actualizar_detalle_receta();self.actualizar_medicamentos()
        except Exception as e:
            if con:con.rollback()
            if getattr(e,"errno",None)==1062:
                QMessageBox.warning(self,"Medicamento repetido","Ese medicamento ya está en esa receta.")
            else:
                self._mensaje_error("No se pudo editar el detalle",e)
        finally:
            if con:con.close()

    def eliminar_detalle_receta(self):
        if not self._permitir("Detalle","eliminar"):return
        fila=self.tabla_detalle_receta.currentRow()
        if fila<0:return
        rec=int(self._item(self.tabla_detalle_receta,fila,0));med=int(self._item(self.tabla_detalle_receta,fila,1));con=None
        try:
            con=self._db();cur=con.cursor()
            if self.usuario_actual.get("Rol")=="Medico":
                cur.execute("SELECT c.ID_Medico FROM Recetas_Medicas r JOIN Consultas_Historial c ON c.ID_Consulta=r.ID_Consulta WHERE r.ID_Receta=%s",(rec,));r=cur.fetchone()
                if not r or r[0]!=self.usuario_actual.get("ID_Medico"):QMessageBox.warning(self,"Permiso","No puedes eliminar un detalle ajeno.");return
            if not self._confirmar_eliminacion("este detalle de la receta"): return
            cur.execute("SELECT Cantidad FROM Detalle_Receta WHERE ID_Receta=%s AND ID_Medicamento=%s FOR UPDATE",(rec,med));previo=cur.fetchone()
            if previo is None:
                con.rollback();QMessageBox.warning(self,"Registro no encontrado","El detalle ya no existe.");self.actualizar_detalle_receta();return
            cur.execute("DELETE FROM Detalle_Receta WHERE ID_Receta=%s AND ID_Medicamento=%s",(rec,med))
            # Al quitar el medicamento de la receta, vuelve al stock.
            cur.execute("UPDATE Medicamentos_Catalogo SET Existencia=Existencia+%s WHERE ID_Medicamento=%s",(previo[0],med))
            con.commit();self.actualizar_detalle_receta();self.actualizar_medicamentos()
        except Exception as e:
            if con:con.rollback()
            self._mensaje_error("Detalle de receta",e)
        finally:
            if con:con.close()

    # Los módulos de citas y expedientes ya tenían SQL; estos wrappers añaden
    # comprobaciones de rol antes de permitir operaciones de escritura.
    def guardar_cita(self):
        if self._permitir("Citas", "crear"):
            return super().guardar_cita()

    def editar_cita(self):
        if self._permitir("Citas", "editar"):
            return super().editar_cita()

    def eliminar_cita(self):
        if self._permitir("Citas", "eliminar"):
            return super().eliminar_cita()

    def guardar_expediente(self):
        if self._permitir("Expedientes", "crear"):
            return super().guardar_expediente()

    def editar_expediente(self):
        if self._permitir("Expedientes", "editar"):
            return super().editar_expediente()

    def eliminar_expediente(self):
        if self._permitir("Expedientes", "eliminar"):
            return super().eliminar_expediente()

    def actualizar_expedientes(self):
        if not hasattr(self, "tabla_expedientes"):
            return
        con = None
        try:
            con = self._db(); cur = con.cursor()
            rol = self.usuario_actual.get("Rol")
            if rol == "Medico":
                cur.execute("""SELECT DISTINCT e.ID_Expediente,p.Nombre,e.Fecha_Creacion,COALESCE(e.Lugar_Expediente,'Sin asignar'),'Activo'
                    FROM Expedientes_Clinicos e JOIN Pacientes p ON p.ID_Paciente=e.ID_Paciente
                    JOIN Citas_Medicas c ON c.ID_Paciente=p.ID_Paciente
                    WHERE c.ID_Medico=%s ORDER BY e.ID_Expediente DESC""",
                    (self.usuario_actual.get("ID_Medico"),))
            else:
                cur.execute("""SELECT e.ID_Expediente,p.Nombre,e.Fecha_Creacion,COALESCE(e.Lugar_Expediente,'Sin asignar'),'Activo'
                    FROM Expedientes_Clinicos e JOIN Pacientes p ON p.ID_Paciente=e.ID_Paciente
                    ORDER BY e.ID_Expediente DESC""")
            self._cargar_tabla(self.tabla_expedientes, cur.fetchall())
            if hasattr(self, "paciente_expediente"):
                keep = self.paciente_expediente.currentData()
                self.paciente_expediente.clear(); self.paciente_expediente.addItem("Seleccionar paciente", None)
                if rol != "Medico":
                    cur.execute("SELECT ID_Paciente,Nombre FROM Pacientes ORDER BY Nombre")
                    for ident, nombre in cur.fetchall(): self.paciente_expediente.addItem(nombre, ident)
                idx = self.paciente_expediente.findData(keep)
                if idx >= 0: self.paciente_expediente.setCurrentIndex(idx)
        except Exception as e:
            self._mensaje_error("Expedientes clínicos", e)
        finally:
            if con: con.close()

    def seleccionar_consulta(self, fila, columna):
        try:
            def seleccionar_data(combo, dato):
                idx = combo.findData(dato)
                if idx >= 0: combo.setCurrentIndex(idx)
            seleccionar_data(self.expediente_consulta, int(self._item(self.tabla_consultas, fila, 1).split("Exp. ")[-1].split(" ")[0]))
            medico_nombre = self._item(self.tabla_consultas, fila, 2)
            idx = self.medico_consulta.findText(medico_nombre)
            if idx >= 0: self.medico_consulta.setCurrentIndex(idx)
            seleccionar_data(self.cita_consulta, int(self._item(self.tabla_consultas, fila, 3)))
            self.fecha_consulta.setDate(QDate.fromString(self._item(self.tabla_consultas, fila, 4), "yyyy-MM-dd"))
            self.presion_consulta.setText(self._item(self.tabla_consultas, fila, 5))
            self.peso_consulta.setValue(float(self._item(self.tabla_consultas, fila, 6)))
            self.sintomas_consulta.setPlainText(self._item(self.tabla_consultas, fila, 7))
            self.diagnostico_consulta.setPlainText(self._item(self.tabla_consultas, fila, 8))
        except Exception as e:
            self._mensaje_error("Seleccionar consulta", e)

    def seleccionar_receta(self, fila, columna):
        try:
            texto = self._item(self.tabla_recetas, fila, 1)
            idx = self.consulta_receta.findText(texto)
            if idx >= 0: self.consulta_receta.setCurrentIndex(idx)
            fecha = QDate.fromString(self._item(self.tabla_recetas, fila, 2), "yyyy-MM-dd")
            if fecha.isValid(): self.fecha_receta.setDate(fecha)
        except Exception as e:
            self._mensaje_error("Seleccionar receta", e)

    def seleccionar_detalle_receta(self, fila, columna):
        try:
            idx = self.receta_detalle.findData(int(self._item(self.tabla_detalle_receta, fila, 0)))
            if idx >= 0: self.receta_detalle.setCurrentIndex(idx)
            idx = self.medicamento_detalle.findData(int(self._item(self.tabla_detalle_receta, fila, 1)))
            if idx >= 0: self.medicamento_detalle.setCurrentIndex(idx)
            self.dosis_detalle.setText(self._item(self.tabla_detalle_receta, fila, 2))
            self.frecuencia_detalle.setText(self._item(self.tabla_detalle_receta, fila, 3))
            self.duracion_detalle.setText(self._item(self.tabla_detalle_receta, fila, 4))
            self.cantidad_detalle.setValue(int(self._item(self.tabla_detalle_receta, fila, 5) or 1))
        except Exception as e:
            self._mensaje_error("Seleccionar detalle", e)