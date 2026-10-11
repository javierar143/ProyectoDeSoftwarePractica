"""TEMPORAL: reemplazar por el modelo TipoComida real."""

from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel



class TipoComidaTemporal(BaseModel):
    __tablename__ = "TipoComida"

    idTipoComida: Mapped[int] = mapped_column(primary_key=True)