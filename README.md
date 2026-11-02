\# MediCore – Sistema de Gestión Hospitalaria



Aplicación de escritorio para administrar pacientes, citas médicas, expedientes clínicos, consultas, recetas y medicamentos de un hospital. Fue desarrollada como Proyecto Integrador II (UNAN-León) con Python, PySide6 y MySQL.



\## Propósito



MediCore centraliza en una sola aplicación la información que normalmente se maneja en papel: quién es el paciente, con qué médico tiene cita, qué se encontró en la consulta y qué medicamentos se recetaron. Busca reducir los tiempos de atención y evitar datos inconsistentes mediante validaciones y restricciones en la base de datos.



\## Funcionalidades



\- Inicio de sesión con contraseñas cifradas (PBKDF2-SHA256) y tres roles: Administrador, Administrativo y Médico.

\- Cada rol ve solo los módulos que le corresponden.

\- Administración: usuarios y cuentas, especialidades médicas, médicos y catálogo de medicamentos con existencias.

\- Pacientes: cédula (obligatoria desde los 18 años), sexo, tipo de sangre y alergias.

\- Agenda y citas: horarios por médico sin traslapes, citas dentro de la agenda y separadas al menos 15 minutos.

\- Expedientes y consultas: un expediente por paciente; la consulta se registra desde la cita, con presión arterial validada.

\- Recetas: detalle de medicamentos con descuento automático de existencias y advertencia de alergias.

\- Reporte: exportación de la receta médica a PDF (media carta) con ReportLab.



\## Tecnologías



| Componente | Tecnología |

|---|---|

| Lenguaje | Python 3.10 o superior |

| Interfaz gráfica | PySide6 (Qt for Python) |

| Base de datos | MySQL 8.0.16 o superior (usa restricciones CHECK) |

| Conexión a MySQL | mysql-connector-python (consultas parametrizadas) |

| ORM | SQLAlchemy (solo para especialidades médicas) |

| Reportes PDF | ReportLab |



\## Requisitos previos



\- Python 3.10 o superior, con pip.

\- Servidor MySQL 8.0.16 o superior en ejecución (MySQL Workbench es opcional, pero útil para importar el script).

\- Un usuario de MySQL con permiso para crear bases de datos.



\## Estructura del proyecto



```text

.

├── main.py                  # Punto de entrada de la aplicación

├── conexion.py              # Conexión a MySQL (lee variables de entorno)

├── prueba\_conexion.py       # Comprueba que la conexión funciona

├── crear\_administrador.py   # Crea la primera cuenta de administrador

├── generar\_hash.py          # Genera el hash de una contraseña

├── Medicore\_Final\_Ya.sql    # Script de la base de datos y datos de ejemplo

├── requirements.txt         # Dependencias de Python

└── medicore/                # Paquete con los módulos de la aplicación

&#x20;   ├── main.py, login.py, interfaz.py, autenticacion.py

&#x20;   ├── persistencia.py, validaciones.py, buscador.py, common.py

&#x20;   ├── orm.py, Modelos.py

&#x20;   ├── especialidades.py, medicos.py, pacientes.py, usuarios.py

&#x20;   ├── agenda.py, citas.py, expedientes.py, consultas.py

&#x20;   ├── recetas.py, detalle\_receta.py, medicamentos.py

&#x20;   ├── exportar\_pdf.py

&#x20;   └── logo\_medicore.png

```



\## Instalación



\### 1. Obtener el código



```bash

git clone <URL-DEL-REPOSITORIO>

cd <carpeta-del-proyecto>

```



\### 2. Crear un entorno virtual e instalar las dependencias



```bash

python -m venv venv

```



\*\*Windows:\*\*



```bash

venv\\Scripts\\activate

```



\*\*Linux / macOS:\*\*



```bash

source venv/bin/activate

```



Instalar dependencias:



```bash

pip install -r requirements.txt

```



Contenido de `requirements.txt`:



```text

PySide6

mysql-connector-python

SQLAlchemy

reportlab

```



\### 3. Crear la base de datos



Importe el script `Medicore\_Final\_Ya.sql`. Crea la base MediCore, las 11 tablas y datos de ejemplo.



\*\*Desde MySQL Workbench:\*\* File → Open SQL Script y ejecute todo el archivo.



\*\*Desde la terminal:\*\*



```bash

mysql -u root -p < Medicore\_Final\_Ya.sql

```



\### 4. Configurar la conexión



`conexion.py` y `medicore/orm.py` leen estas variables de entorno. Si no existen, usan los valores por defecto entre paréntesis.



| Variable | Descripción |

|---|---|

| MEDICORE\_DB\_HOST | Servidor (localhost) |

| MEDICORE\_DB\_PORT | Puerto (3306) |

| MEDICORE\_DB\_NAME | Nombre de la base (MediCore) |

| MEDICORE\_DB\_USER | Usuario de MySQL (root) |

| MEDICORE\_DB\_PASSWORD | Contraseña de MySQL |



Defina al menos la contraseña antes de ejecutar:



\*\*Windows (PowerShell):\*\*



```powershell

$env:MEDICORE\_DB\_PASSWORD = "su\_contraseña"

```



\*\*Windows (cmd):\*\*



```cmd

set MEDICORE\_DB\_PASSWORD=su\_contraseña

```



\*\*Linux / macOS:\*\*



```bash

export MEDICORE\_DB\_PASSWORD="su\_contraseña"

```



No suba contraseñas al repositorio. Mantenga las credenciales solo en variables de entorno.



\### 5. Verificar la conexión



```bash

python prueba\_conexion.py

```



Debe mostrar «Conexión a MediCore establecida correctamente», el nombre de la base y la versión de MySQL.



\### 6. Crear la cuenta de administrador



```bash

python crear\_administrador.py

```



Pide nombre de usuario, nombre completo y contraseña (mínimo 5 caracteres). Solo permite crear una cuenta de administrador.



\## Ejecución



```bash

python main.py

```



Se abre la ventana de inicio de sesión. Entre con la cuenta de administrador y, desde el módulo de usuarios, cree las demás.



El script SQL también inserta dos usuarios de prueba: CarlosM (rol Médico) y Secretaria1 (rol Administrativo).



Para usarlos necesita conocer la contraseña con la que se generó su hash; si no la tiene, genere un hash nuevo con `python generar\_hash.py` y reemplace el valor de `Contrasena\_Hash` en la tabla Usuarios.



\## Roles y permisos



| Rol | Puede hacer |

|---|---|

| Administrador | Acceso total a todos los módulos |

| Administrativo | Pacientes (crear, editar, consultar), agenda y citas (crear, editar, eliminar, consultar) |

| Médico | Consultar pacientes, agenda y expedientes; editar citas (marcar asistencia); crear y editar consultas, recetas y detalle de receta; exportar sus recetas a PDF |



\## Solución de problemas



\- \*\*ModuleNotFoundError:\*\* active el entorno virtual y ejecute `pip install -r requirements.txt`.

\- \*\*«No se pudo conectar con la base de datos»:\*\* compruebe que MySQL esté en ejecución, que la base MediCore exista y que las variables `MEDICORE\_DB\_\*` sean correctas.

\- \*\*Error en las restricciones CHECK al importar el script:\*\* use MySQL 8.0.16 o superior.

\- \*\*El PDF no se genera:\*\* instale ReportLab con `pip install reportlab`.



\## Enlaces del proyecto



\- \*\*Repositorio GitHub:\*\* \[MediCore – Sistema de Gestión Hospitalaria](https://github.com/Bhrayan914/Medicore\_.git)

\- \*\*Google Drive:\*\* \[Carpeta de documentación y archivos del proyecto](https://drive.google.com/drive/folders/1Yf5TIrjocyacHIiShftJSG0S5cKIUEGh?usp=sharing)



\## Autores



\- Tamara José Martinez Medina.

\- José Armando Cortez Flores.

\- Bhrayan Marcelo Mendez Barberena.



\*\*Proyecto Integrador II\*\* – Universidad Nacional Autónoma de Nicaragua, León (UNAN-León).

