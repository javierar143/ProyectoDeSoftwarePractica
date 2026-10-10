"""Modelo de solicitud nominada de una comida."""

from datetime import date, datetime

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel
from src.core.models.enums import CondicionCupo, EstadoAutorizacion


class Solicitud(BaseModel):
    """Una comida solicitada para una persona en una fecha."""

    __tablename__ = "Solicitud"

    idSolicitud: Mapped[int] = mapped_column(primary_key=True)
    idPedido: Mapped[int] = mapped_column(ForeignKey("Pedido.idPedido"))
    idPersonal: Mapped[int] = mapped_column(ForeignKey("Personal.idPersonal"))
    idTipoComida: Mapped[int] = mapped_column(ForeignKey("TipoComida.idTipoComida"))
    idTipoMenu: Mapped[int] = mapped_column(ForeignKey("TipoMenu.idTipoMenu"))
    fecha_vianda: Mapped[date]
    condicionCupo: Mapped[CondicionCupo] = mapped_column(
        Enum(CondicionCupo, native_enum=False, length=20,
             values_callable=lambda e: [m.value for m in e])
    )
    estadoAutorizacion: Mapped[EstadoAutorizacion] = mapped_column(
        Enum(EstadoAutorizacion, native_enum=False, length=20,
             values_callable=lambda e: [m.value for m in e]),
        default=EstadoAutorizacion.PENDIENTE,
    )
    idUserEvaluador: Mapped[int | None] = mapped_column(ForeignKey("Usuario.id_user"))
    inserted_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)