"""Modelo de solicitud nominada de una comida."""

from datetime import date, datetime

from sqlalchemy import Enum, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel
from src.core.models.enums import CondicionCupo, EstadoAutorizacion


class Solicitud(BaseModel):
    """Una comida solicitada para una persona en una fecha determinada."""

    __tablename__ = "Solicitud"

    idSolicitud: Mapped[int] = mapped_column(primary_key=True)
    idPedido: Mapped[int] = mapped_column(
        ForeignKey("Pedido.idPedido", ondelete="CASCADE"), nullable=False
    )
    idPersonal: Mapped[int] = mapped_column(
        ForeignKey("Personal.idPersonal"), nullable=False
    )
    idTipoComida: Mapped[int] = mapped_column(
        ForeignKey("TipoComida.idTipoComida"), nullable=False
    )
    idTipoMenu: Mapped[int] = mapped_column(
        ForeignKey("TipoMenu.idTipoMenu"), nullable=False
    )
    fecha_vianda: Mapped[date] = mapped_column(nullable=False)
    condicionCupo: Mapped[CondicionCupo] = mapped_column(
        Enum(
            CondicionCupo,
            native_enum=False,
            length=20,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    estadoAutorizacion: Mapped[EstadoAutorizacion] = mapped_column(
        Enum(
            EstadoAutorizacion,
            native_enum=False,
            length=20,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=EstadoAutorizacion.PENDIENTE,
        nullable=False,
    )
    idUserEvaluador: Mapped[int | None] = mapped_column(
        ForeignKey("Usuario.id_user"), nullable=True
    )
    fecha_evaluacion: Mapped[datetime | None] = mapped_column(
        default=None, nullable=True
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    inserted_at: Mapped[datetime] = mapped_column(
        default=datetime.now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now, nullable=False
    )