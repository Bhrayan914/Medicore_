"""Configuración de SQLAlchemy (ORM) para MediCore.

Usa las mismas variables de entorno que conexion.py, así que apunta a la
misma base de datos MySQL.
"""
import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Clase base de todos los modelos ORM."""


def _url_conexion():
    usuario = quote_plus(os.getenv("MEDICORE_DB_USER", "root"))
    clave = quote_plus(os.getenv("MEDICORE_DB_PASSWORD", "505168"))
    host = os.getenv("MEDICORE_DB_HOST", "localhost")
    puerto = os.getenv("MEDICORE_DB_PORT", "3306")
    base = os.getenv("MEDICORE_DB_NAME", "MediCore")
    return f"mysql+mysqlconnector://{usuario}:{clave}@{host}:{puerto}/{base}"


engine = create_engine(_url_conexion(), pool_pre_ping=True, echo=True)
Session = sessionmaker(bind=engine)


def obtener_sesion():
    """Devuelve una sesión del ORM. Úsala con `with obtener_sesion() as s:`."""
    return Session()