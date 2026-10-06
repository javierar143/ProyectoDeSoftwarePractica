"""Modelo temporal de personal para pruebas del módulo de usuarios."""

from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class PersonalTemporal(BaseModel):
    """Representa temporalmente una persona para las pruebas de usuarios."""

    __tablename__ = "Personal"

    idPersonal: Mapped[int] = mapped_column(primary_key=True)
    dni: Mapped[str] = mapped_column(unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(nullable=False)
    apellido: Mapped[str] = mapped_column(nullable=False)