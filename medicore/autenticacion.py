
import hashlib
import hmac
import os

from conexion import obtener_conexion


def crear_hash(contrasena):
    salt = os.urandom(16)

    resultado = hashlib.pbkdf2_hmac(
        "sha256",
        contrasena.encode("utf-8"),
        salt,
        600000
    )

    return f"pbkdf2_sha256$600000${salt.hex()}${resultado.hex()}"


def verificar_contrasena(contrasena, hash_guardado):
    try:
        algoritmo, iteraciones, salt_hex, hash_hex = hash_guardado.split("$")

        if algoritmo != "pbkdf2_sha256":
            return False

        resultado = hashlib.pbkdf2_hmac(
            "sha256",
            contrasena.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iteraciones)
        )

        return hmac.compare_digest(resultado.hex(), hash_hex)

    except (ValueError, TypeError):
        return False


def autenticar_usuario(nombre_usuario, contrasena):
    conexion = obtener_conexion()

    if conexion is None:
        return None

    try:
        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT ID_Usuario, Nombre_Usuario, Contrasena_Hash,
                   Nombre_Completo, Rol, ID_Medico, Estado
            FROM Usuarios
            WHERE Nombre_Usuario = %s
            """,
            (nombre_usuario,)
        )

        usuario = cursor.fetchone()
        cursor.close()

        if not usuario:
            return None

        if usuario["Estado"] != "Activo":
            return None

        if not verificar_contrasena(
            contrasena,
            usuario["Contrasena_Hash"]
        ):
            return None

        usuario.pop("Contrasena_Hash", None)
        return usuario

    except Exception as error:
        print(f"Error al autenticar usuario: {error}")
        return None

    finally:
        conexion.close()
