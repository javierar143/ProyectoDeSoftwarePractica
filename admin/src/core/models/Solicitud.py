from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import BaseModel

class Solicitud(BaseModel):
    __tablename__ = "Solicitud"

    idSolicitud: Mapped[int] = mapped_column(primary_key=True)
    idPedido: Mapped[int] = mapped_column(ForeignKey("Pedido.idPedido"))
    idPersonal: Mapped[int] = mapped_column(ForeignKey("Personal.idPersonal"))
    idTipoComida: Mapped[int] = mapped_column(ForeignKey("Tipo_comida.idTipoComida"))
    idTipoMenu: Mapped[int] = mapped_column(ForeignKey("Tipo_menu.idTipoMenu"))
    fecha_vianda: Mapped[datetime]
    condicionCupo: Mapped[str]
    estadoAutorizacion: Mapped[str]
    inserted_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    idUserEvaluador: Mapped[int] = mapped_column(ForeignKey("Usuario.id_user"))