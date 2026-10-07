"""Modelo de cabecera de pedido de comidas."""

from datetime import date, datetime

from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models.enums import EstadoPedido, Periodicidad

from src.core.database import BaseModel


class Pedido(BaseModel):
    """Pedido cargado por un Jefe de Servicio para su sector."""

    __tablename__ = "Pedido"

    idPedido: Mapped[int] = mapped_column(primary_key=True)
    fecha_desde: Mapped[date]
    periodicidad: Mapped[Periodicidad] = mapped_column(
        Enum(Periodicidad, native_enum=False, length=20,
             values_callable=lambda e: [m.value for m in e])
    )
    estado_general: Mapped[EstadoPedido] = mapped_column(
        Enum(EstadoPedido, native_enum=False, length=20,
             values_callable=lambda e: [m.value for m in e])
    )
    idSector: Mapped[int] = mapped_column(ForeignKey("Sector.idSector"))
    idUser: Mapped[int] = mapped_column(ForeignKey("Usuario.id_user"))
    inserted_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)