"""Servicios relacionados con la autenticación de la API."""

from datetime import datetime, timezone

from src.core.models.Usuario import Usuario
from src.core.repositories import api_token, usuario
from src.core.services.api_token import hash_token


def get_authenticated_user(token: str) -> Usuario | None:
    """Obtiene el usuario asociado a un token válido y no expirado."""
    token_hash = hash_token(token)
    stored_token = api_token.get_by_hash(token_hash)

    user = None

    if stored_token is not None:
        now = datetime.now(timezone.utc)

        if stored_token.revoked_at is None and stored_token.expires_at > now:
            user = usuario.get_by_id(stored_token.id_user)

    return user