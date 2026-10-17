
"""Modelo de asociación entre Jefes de Servicio y sectores."""

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class UsuarioEsJefeSector(BaseModel):
    """Asocia cada Jefe de Servicio con un único sector."""

    __tablename__ = "UsuarioEsJefeSector"
    __table_args__ = (
        UniqueConstraint(
            "idUser",
            name="uq_usuario_es_jefe_sector_usuario",
        ),
    )

    idUser: Mapped[int] = mapped_column(
        ForeignKey("Usuario.id_user"),
        primary_key=True,
    )
    idSector: Mapped[int] = mapped_column(
        ForeignKey("Sector.idSector"),
        primary_key=True,
    )
