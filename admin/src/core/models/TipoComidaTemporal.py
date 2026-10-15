"""TEMPORAL: reemplazar por el modelo TipoComida real."""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import BaseModel


class TipoComidaTemporal(BaseModel):
    __tablename__ = "TipoComida"

    idTipoComida: Mapped[int] = mapped_column(
            Integer,
            primary_key=True,
    )
    nombre: Mapped[str] = mapped_column(
            String,
            nullable=False,
    )