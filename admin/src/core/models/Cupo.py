"""Modelo de cupo de comensales por sector y tipo de comida."""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class Cupo(BaseModel):
    """Cantidad máxima de solicitudes regulares de un sector para una comida."""

    __tablename__ = "Cupo"
    __table_args__ = (
        UniqueConstraint("idSector", "idTipoComida", name="uq_cupo_sector_comida"),
        CheckConstraint('"cantComensales" > 0', name="ck_cupo_cantidad_positiva"),
    )

    idCupo: Mapped[int] = mapped_column(primary_key=True)
    cantComensales: Mapped[int] = mapped_column(nullable=False)
    idTipoComida: Mapped[int] = mapped_column(
        ForeignKey("TipoComida.idTipoComida"), nullable=False
    )
    idSector: Mapped[int] = mapped_column(
        ForeignKey("Sector.idSector"), nullable=False
    )
    inserted_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )