"""Modelo de solicitud nominada de una comida."""

from datetime import date, datetime

from sqlalchemy import Enum, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel
from src.core.models.enums import CondicionCupo, EstadoAutorizacion, EstadoPedido


class Solicitud(BaseModel):
    """Una comida solicitada para una persona en una fecha."""

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
    inserted_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )

    @classmethod
    def existe_duplicado(
        cls,
        session,
        id_personal: int,
        id_sector: int,
        fecha: date,
        id_tipo_comida: int,
        excluir_id_pedido: int | None = None,
    ) -> bool:
        """Verifica si la persona ya tiene esa comida solicitada en ese sector y fecha."""
        from src.core.models.Pedido import Pedido

        stmt = (
            select(cls)
            .join(Pedido, cls.idPedido == Pedido.idPedido)
            .where(
                cls.idPersonal == id_personal,
                cls.fecha_vianda == fecha,
                cls.idTipoComida == id_tipo_comida,
                Pedido.idSector == id_sector,
                Pedido.estado_general != EstadoPedido.RECHAZADO,
            )
        )
        if excluir_id_pedido is not None:
            stmt = stmt.where(Pedido.idPedido != excluir_id_pedido)

        resultado = session.execute(stmt).scalars().first()
        return resultado is not None