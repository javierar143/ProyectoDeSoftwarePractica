"""Servicios relacionados con la autenticación de la API."""

from datetime import datetime, timedelta, timezone

from src.core.models.ApiToken import ApiToken
from src.core.models.Usuario import Usuario
from src.core.repositories import api_token, usuario
from src.core.security.password import verify_password
from src.core.services.api_token import generate_token, hash_token


def login(email: str, password: str) -> str | None:
    """Autentica un usuario y genera un token de API válido."""
    stored_user = usuario.get_by_email(email)

    token = None

    if stored_user is not None and stored_user.isActive:
        if verify_password(password, stored_user.password_hash):
            raw_token = generate_token()
            now = datetime.now(timezone.utc)

            api_token_entity = ApiToken(
                token_hash=hash_token(raw_token),
                id_user=stored_user.id_user,
                created_at=now,
                expires_at=now + timedelta(hours=24),
            )

            api_token.create(api_token_entity)
            token = raw_token

    return token


    #Seguridad: almacenamos solamente el hash del token; si alguien accede a la base de datos, 
    #no obtiene directamente el bearer token.

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


def logout(token: str) -> bool:
    """Revoca un token de API autenticado."""
    token_hash = hash_token(token)
    stored_token = api_token.get_by_hash(token_hash)

    revoked = False

    if stored_token is not None and stored_token.revoked_at is None:
        stored_token.revoked_at = datetime.now(timezone.utc)
        api_token.revoke(stored_token, stored_token.revoked_at)
        revoked = True

    return revoked