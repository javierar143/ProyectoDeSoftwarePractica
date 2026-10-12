from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class TipoPersonal(BaseModel):
    __tablename__ = "TipoPersonal"

    idTipoPersonal: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str]