from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class Rol(BaseModel):
    __tablename__ = "Rol"

    idRol: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str]