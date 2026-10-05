"""Repositorio para la persistencia y consulta de tokens de la API."""

from datetime import datetime

from sqlalchemy import select

from src.core.database import db
from src.core.models.ApiToken import ApiToken


def create(api_token: ApiToken) -> ApiToken:
    """Persiste un token de API y devuelve la entidad creada."""
    db.session.add(api_token)
    db.session.commit()

    return api_token


def get_by_hash(token_hash: str) -> ApiToken | None:
    """Obtiene un token de API a partir de su hash."""
    statement = select(ApiToken).where(
        ApiToken.token_hash == token_hash
    )

    api_token = db.session.execute(statement).scalar_one_or_none()

    return api_token


def revoke(api_token: ApiToken, revoked_at: datetime) -> ApiToken:
    """Revoca un token de API estableciendo su fecha de revocación."""
    api_token.revoked_at = revoked_at
    db.session.commit()

    return api_token