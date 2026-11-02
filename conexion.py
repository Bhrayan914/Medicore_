import os
import mysql.connector
from mysql.connector import Error


def obtener_conexion():
    """Abre una conexión a MediCore. Puede configurarse con variables de entorno."""
    try:
        conexion = mysql.connector.connect(
            host=os.getenv("MEDICORE_DB_HOST", "localhost"),
            port=int(os.getenv("MEDICORE_DB_PORT", "3306")),
            database=os.getenv("MEDICORE_DB_NAME", "MediCore"),
            user=os.getenv("MEDICORE_DB_USER", "root"),
            password=os.getenv("MEDICORE_DB_PASSWORD", "505168"),
            connection_timeout=5,
        )
        if conexion.is_connected():
            return conexion
        conexion.close()
        return None
    except (Error, ValueError) as error:
        print(f"Error al conectar con MySQL: {error}")
        return None
