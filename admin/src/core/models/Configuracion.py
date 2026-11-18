from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import BaseModel


class Configuracion(BaseModel):
    __tablename__ = "Configuracion"

    idConfiguracion: Mapped[int] = mapped_column(primary_key=True)
    elementos_por_pagina: Mapped[int] = mapped_column(default=10)
    modo_mantenimiento: Mapped[bool] = mapped_column(default=False)
    mensaje_mantenimiento: Mapped[str] = mapped_column(
        String(255),
        default=(
            "La aplicación se encuentra temporalmente en mantenimiento. Estamos "
            "trabajando para restablecer el servicio. Cuando finalice el mantenimiento, "
            "la aplicación volverá a estar disponible automáticamente. No necesitás "
            "realizar ninguna acción."
        ),
        nullable=False
    )
