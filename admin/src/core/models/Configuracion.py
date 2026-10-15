from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import BaseModel


class Configuracion(BaseModel):
    __tablename__ = "Configuracion"

    idConfiguracion: Mapped[int] = mapped_column(primary_key=True)
    elementos_por_pagina: Mapped[int] = mapped_column(default=10)
    modo_mantenimiento: Mapped[bool] = mapped_column(default=False)