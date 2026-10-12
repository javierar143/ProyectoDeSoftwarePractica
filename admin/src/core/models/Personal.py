from datetime import datetime

from src.core.models.TipoMenu import TipoMenu
from src.core.models.TipoPersonal import TipoPersonal
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    # son relaciones de navegacion, no columnas de la tabla 
    tipo_personal: Mapped["TipoPersonal"] = relationship(lazy="joined")
    tipo_menu: Mapped["TipoMenu"] = relationship(lazy="joined")