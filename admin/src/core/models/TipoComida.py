from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import BaseModel

class TipoComida(BaseModel):
    __tablename__ = "TipoComida"

    idTipoComida: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)