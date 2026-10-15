"""Modelo de cupo de comensales por sector y tipo de comida."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import BaseModel

if TYPE_CHECKING:
    from src.core.models.Sector import Sector
    from src.core.models.TipoComida import TipoComida


class Cupo(BaseModel):
    """Cantidad máxima de solicitudes regulares vigentes de un sector para una comida."""

    __tablename__ = "Cupo"
    __table_args__ = (
        Index(
            "uq_cupo_sector_comida_activo",
            "idSector",
            "idTipoComida",
            unique=True,
            postgresql_where=text('"activo" = true'),
        ),
        CheckConstraint(
            '"cantComensales" > 0', name="ck_cupo_cantidad_positiva"
        ),
    )

    idCupo: Mapped[int] = mapped_column(primary_key=True)
    cantComensales: Mapped[int] = mapped_column(nullable=False)
    idTipoComida: Mapped[int] = mapped_column(
        ForeignKey("TipoComida.idTipoComida"), nullable=False
    )
    idSector: Mapped[int] = mapped_column(
        ForeignKey("Sector.idSector"), nullable=False
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, nullable=True
    )
    inserted_at: Mapped[datetime] = mapped_column(
        default=datetime.now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now, nullable=False
    )

    sector: Mapped["Sector"] = relationship("Sector", lazy="joined")
    tipo_comida: Mapped["TipoComida"] = relationship(
        "TipoComida", lazy="joined"
    )