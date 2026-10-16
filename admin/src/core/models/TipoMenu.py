"""Modelo de tipo de menú alimentario (General, Vegetariano, Celíaco)."""

from datetime import datetime

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class TipoMenu(BaseModel):
    """Representa una categoría de menú predefinida o administrada en el sistema."""

    __tablename__ = "TipoMenu"

    idTipoMenu: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    isActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    inserted_at: Mapped[datetime] = mapped_column(
        default=datetime.now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now, nullable=False
    )