from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class Personal(BaseModel):
    __tablename__ = "Personal"

    idPersonal: Mapped[int] = mapped_column(primary_key=True)
    dni: Mapped[str]
    nombre: Mapped[str]
    apellido: Mapped[str]
    isActive: Mapped[bool]
    inserted_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    idTipoPersonal: Mapped[int] = mapped_column(ForeignKey("TipoPersonal.idTipoPersonal"))
    idTipoMenu: Mapped[int] = mapped_column(ForeignKey("TipoMenu.idTipoMenu"))