"""Modelo para gestionar los tokens de autenticación de la API."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class ApiToken(BaseModel):
    """Representa un token de autenticación asociado a un usuario."""

    __tablename__ = "ApiToken"

    id_token: Mapped[int] = mapped_column(primary_key=True)

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True
    )

    id_user: Mapped[int] = mapped_column(
        ForeignKey("Usuario.id_user")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )