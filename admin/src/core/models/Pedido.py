"""Modelo de cabecera de pedido de comidas."""

from datetime import date, datetime

from sqlalchemy import Enum, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel
from src.core.models.enums import EstadoPedido, Periodicidad


class Pedido(BaseModel):
    """Pedido cargado por un Jefe de Servicio para su sector."""

    __tablename__ = "Pedido"

    idPedido: Mapped[int] = mapped_column(primary_key=True)
    fecha_desde: Mapped[date] = mapped_column(nullable=False)
    # En pedidos diarios coincide con fecha_desde
    fecha_hasta: Mapped[date] = mapped_column(nullable=False)
    periodicidad: Mapped[Periodicidad] = mapped_column(
        Enum(
            Periodicidad,
            native_enum=False,
            length=20,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    estado_general: Mapped[EstadoPedido] = mapped_column(
        Enum(
            EstadoPedido,
            native_enum=False,
            length=20,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=EstadoPedido.CONFIRMADO,
        nullable=False,
    )
    idSector: Mapped[int] = mapped_column(
        ForeignKey("Sector.idSector"), nullable=False
    )
    idUser: Mapped[int] = mapped_column(
        ForeignKey("Usuario.id_user"), nullable=False
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    inserted_at: Mapped[datetime] = mapped_column(
        default=datetime.now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now, nullable=False
    )