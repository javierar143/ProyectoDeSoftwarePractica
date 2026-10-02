from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class Permiso(BaseModel):
    __tablename__ = "Permiso"

    idPermiso: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str]