"""Modelo de sector o servicio del hospital."""

from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class Sector(BaseModel):
    """Sector o servicio del hospital al que pertenecen personal y Jefes de Servicio."""

    __tablename__ = "Sector"

    idSector: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    isActive: Mapped[bool] = mapped_column(default=True)
    inserted_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)