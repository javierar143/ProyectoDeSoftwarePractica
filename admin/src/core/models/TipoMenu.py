from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class TipoMenu(BaseModel):
    __tablename__ = "TipoMenu"

    idTipoMenu: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str]