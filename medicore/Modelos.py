"""Modelos ORM de MediCore (SQLAlchemy).

Por ahora solo está mapeada la tabla Especialidades_Medicas.
"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .orm import Base


class Especialidad(Base):
    __tablename__ = "Especialidades_Medicas"

    id: Mapped[int] = mapped_column("ID_Especialidad", Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column("Nombre_Especialidad", String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"Especialidad(id={self.id!r}, nombre={self.nombre!r})"