
from conexion import obtener_conexion


conexion = obtener_conexion()

if conexion and conexion.is_connected():
    print("Conexión a MediCore establecida correctamente.")

    cursor = conexion.cursor()
    cursor.execute("SELECT DATABASE(), VERSION()")
    resultado = cursor.fetchone()

    print("Base de datos:", resultado[0])
    print("Versión de MySQL:", resultado[1])

    cursor.close()
    conexion.close()
    print("Conexión cerrada correctamente.")
else:
    print("No se pudo establecer la conexión.")
    print("Revisa la contraseña, el servidor y que MySQL esté iniciado.")
