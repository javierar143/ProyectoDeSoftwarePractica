from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class RolPoseePermiso(BaseModel):
    __tablename__ = "RolPoseePermiso"

    idRol: Mapped[int] = mapped_column(
        ForeignKey("Rol.idRol"),
        primary_key=True
    )
    idPermiso: Mapped[int] = mapped_column(
        ForeignKey("Permiso.idPermiso"),
        primary_key=True
    )