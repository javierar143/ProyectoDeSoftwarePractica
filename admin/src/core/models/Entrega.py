from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import BaseModel

class Entrega(BaseModel):
    __tablename__ = "Entrega"

    idEntrega: Mapped[int] = mapped_column(primary_key=True)
    fecha_hora: Mapped[datetime]
    idUser: Mapped[int] = mapped_column(ForeignKey("Usuario.id_user"))
    idSolicitud: Mapped[int] = mapped_column(ForeignKey("Solicitud.idSolicitud"))
    idPersonal: Mapped[int] = mapped_column(ForeignKey("Personal.idPersonal"))