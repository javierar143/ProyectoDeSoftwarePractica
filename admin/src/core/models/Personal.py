"""Modelo que representa al personal del hospital."""

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import BaseModel
from src.core.models.TipoMenu import TipoMenu
from src.core.models.TipoPersonal import TipoPersonal


class Personal(BaseModel):
    """Representa a una persona que puede recibir comidas."""

    __tablename__ = "Personal"

    idPersonal: Mapped[int] = mapped_column(primary_key=True)
    dni: Mapped[str] = mapped_column(unique=True)
    nombre: Mapped[str]
    apellido: Mapped[str]
    isActive: Mapped[bool]
    inserted_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    is_deleted: Mapped[bool] = mapped_column(default=False)
    idTipoPersonal: Mapped[int] = mapped_column(
        ForeignKey("TipoPersonal.idTipoPersonal")
    )
    idTipoMenu: Mapped[int] = mapped_column(
        ForeignKey("TipoMenu.idTipoMenu")
    )

    # Relaciones de navegación; no agregan columnas a la tabla.
    tipo_personal: Mapped["TipoPersonal"] = relationship(lazy="joined")
    tipo_menu: Mapped["TipoMenu"] = relationship(lazy="joined")
