"""TEMPORAL: reemplazar por el modelo TipoMenu real."""

from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel



class TipoMenuTemporal(BaseModel):


    __tablename__ = "TipoMenu"

    idTipoMenu: Mapped[int] = mapped_column(primary_key=True)