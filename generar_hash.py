from getpass import getpass
from medicore.autenticacion import crear_hash

contrasena = getpass("Escribe la contraseña para el médico: ")
print("\nHash generado:")
print(crear_hash(contrasena))