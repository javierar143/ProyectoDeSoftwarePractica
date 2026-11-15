
"""Servicios relacionados con la autenticación de la API."""

from datetime import datetime, timezone

from src.core.models.ApiToken import ApiToken
from src.core.models.Usuario import Usuario
from src.core.repositories.auth import api_token
from src.core.repositories.usuarios import usuario
from src.core.security.password import verify_password
from src.core.services.auth.api_token import hash_token
from src.core.services.auth import jwt_service


def login(email: str, password: str) -> dict[str, str] | None:
    """Autentica al usuario y genera los tokens de acceso y renovación."""
    stored_user = usuario.get_by_email(email)
    tokens = None

    if stored_user is not None and stored_user.isActive:
        if verify_password(password, stored_user.password_hash):
            now = datetime.now(timezone.utc)

            access_token = jwt_service.generate_access_token(
                stored_user.id_user
            )
            refresh_token = jwt_service.generate_refresh_token(
                stored_user.id_user
            )

            access_entity = ApiToken(
                token_hash=hash_token(access_token),
                token_type="access",
                id_user=stored_user.id_user,
                created_at=now,
                expires_at=now + jwt_service.ACCESS_TOKEN_DURATION,
            )

            refresh_entity = ApiToken(
                token_hash=hash_token(refresh_token),
                token_type="refresh",
                id_user=stored_user.id_user,
                created_at=now,
                expires_at=now + jwt_service.REFRESH_TOKEN_DURATION,
            )

            api_token.create_many([access_entity, refresh_entity])

            tokens = {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }

    return tokens


def get_authenticated_user(token: str) -> Usuario | None:
    """Obtiene el usuario asociado a un JWT de acceso válido y no revocado."""
    payload = jwt_service.decode_access_token(token)
    user = None

    if payload is not None:
        token_hash = hash_token(token)
        stored_token = api_token.get_by_hash(token_hash)

        if (
            stored_token is not None
            and stored_token.token_type == "access"
            and stored_token.revoked_at is None
            and stored_token.expires_at > datetime.now(timezone.utc)
        ):
            user = usuario.get_by_id(stored_token.id_user)

            if user is not None and not user.isActive:
                user = None

    return user


def logout(token: str) -> bool:
    """Revoca un JWT de acceso autenticado."""
    payload = jwt_service.decode_access_token(token)
    revoked = False

    if payload is not None:
        token_hash = hash_token(token)
        stored_token = api_token.get_by_hash(token_hash)

        if (
            stored_token is not None
            and stored_token.token_type == "access"
            and stored_token.revoked_at is None
        ):
            now = datetime.now(timezone.utc)
            api_token.revoke(stored_token, now)
            revoked = True

    return revoked
