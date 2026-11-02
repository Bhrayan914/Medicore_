
from getpass import getpass

from conexion import obtener_conexion
from medicore.autenticacion import crear_hash


def crear_administrador():
    print("=" * 45)
    print("     MEDICORE - CREAR ADMINISTRADOR")
    print("=" * 45)

    nombre_usuario = input("Nombre de usuario: ").strip()
    nombre_completo = input("Nombre completo: ").strip()

    contrasena = getpass("Contraseña: ")
    confirmar = getpass("Confirmar contraseña: ")

    if not nombre_usuario or not nombre_completo:
        print("Error: todos los campos son obligatorios.")
        return

    if len(contrasena) < 5:
        print("Error: la contraseña debe tener al menos 5 caracteres.")
        return

    if contrasena != confirmar:
        print("Error: las contraseñas no coinciden.")
        return

    conexion = obtener_conexion()

    if conexion is None:
        print("Error: no se pudo conectar con la base de datos.")
        return

    cursor = None

    try:
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM Usuarios WHERE Rol = %s",
            ("Administrador",)
        )

        cantidad = cursor.fetchone()[0]

        if cantidad > 0:
            print("Ya existe una cuenta de administrador.")
            return

        contrasena_hash = crear_hash(contrasena)

        consulta = """
            INSERT INTO Usuarios (
                Nombre_Usuario,
                Contrasena_Hash,
                Nombre_Completo,
                Rol,
                ID_Medico,
                Estado
            )
            VALUES (%s, %s, %s, %s, NULL, %s)
        """

        valores = (
            nombre_usuario,
            contrasena_hash,
            nombre_completo,
            "Administrador",
            "Activo"
        )

        cursor.execute(consulta, valores)
        conexion.commit()

        print("\nCuenta de administrador creada correctamente.")
        print(f"Usuario: {nombre_usuario}")
        print("Ya puedes utilizar esta cuenta para iniciar sesión.")

    except Exception as error:
        conexion.rollback()
        print(f"Error al crear el administrador: {error}")

    finally:
        if cursor is not None:
            cursor.close()

        conexion.close()


if __name__ == "__main__":
    crear_administrador()
