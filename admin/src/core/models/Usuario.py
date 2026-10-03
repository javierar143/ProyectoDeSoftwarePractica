from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class Usuario(BaseModel):
    __tablename__ = "Usuario"

    id_user: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    alias: Mapped[str]
    isSystemAdmin: Mapped[bool]
    isActive: Mapped[bool]
    updated_at: Mapped[datetime]
    inserted_at: Mapped[datetime]
    idRol: Mapped[int] = mapped_column(ForeignKey("Rol.idRol"))
    idPersonal: Mapped[int] = mapped_column(ForeignKey("Personal.idPersonal"))