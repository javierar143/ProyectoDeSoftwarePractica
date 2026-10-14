"""TEMPORAL: reemplazar por el modelo Sector real."""

from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class SectorTemporal(BaseModel):
    __tablename__ = "Sector"

    idSector: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(nullable=False)
    isActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)