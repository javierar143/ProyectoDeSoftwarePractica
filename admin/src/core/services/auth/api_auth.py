
"""Servicios relacionados con la autenticación de la API."""

from datetime import datetime, timezone

from src.core.models.ApiToken import ApiToken
from src.core.models.Usuario import Usuario
from src.core.repositories.auth import api_token
from src.core.repositories.usuarios import usuario
from src.core.security.password import verify_password
from src.core.services.auth.api_token import hash_token
from src.core.services.auth import jwt_service

class UsuarioBloqueadoError(Exception):
    """Indica que las credenciales son correctas pero la cuenta está bloqueada."""

def login(email: str, password: str) -> dict[str, str] | None:
    """Autentica al usuario y genera los tokens de acceso y renovación."""
    stored_user = usuario.get_by_email(email)

    if stored_user is None:
        return None

    if not verify_password(password, stored_user.password_hash):
        return None

    if not stored_user.isActive:
        raise UsuarioBloqueadoError

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

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

def refresh_access_token(token: str) -> str | None:
    """Genera un nuevo token de acceso a partir de un refresh token válido."""
    payload = jwt_service.decode_refresh_token(token)
    access_token = None

    if payload is not None:
        now = datetime.now(timezone.utc)
        token_hash = hash_token(token)
        stored_token = api_token.get_by_hash(token_hash)

        if (
            stored_token is not None
            and stored_token.token_type == "refresh"
            and stored_token.revoked_at is None
            and stored_token.expires_at > now
            and str(stored_token.id_user) == payload["sub"]
        ):
            user = usuario.get_by_id(stored_token.id_user)

            if user is not None and user.isActive:
                access_token = jwt_service.generate_access_token(
                    stored_token.id_user
                )

                access_entity = ApiToken(
                    token_hash=hash_token(access_token),
                    token_type="access",
                    id_user=stored_token.id_user,
                    created_at=now,
                    expires_at=now + jwt_service.ACCESS_TOKEN_DURATION,
                )

                api_token.create(access_entity)

    return access_token


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


def logout(access_token: str | None, refresh_token: str | None) -> bool:
    """Revoca los tokens de acceso y renovación de una sesión."""
    now = datetime.now(timezone.utc)
    tokens_to_revoke = []

    if access_token:
        payload = jwt_service.decode_access_token(access_token)

        if payload is not None:
            stored_token = api_token.get_by_hash(hash_token(access_token))

            if (
                stored_token is not None
                and stored_token.token_type == "access"
                and stored_token.revoked_at is None
                and stored_token.expires_at > now
                and str(stored_token.id_user) == payload["sub"]
            ):
                tokens_to_revoke.append(stored_token)

    if refresh_token:
        payload = jwt_service.decode_refresh_token(refresh_token)

        if payload is not None:
            stored_token = api_token.get_by_hash(hash_token(refresh_token))

            if (
                stored_token is not None
                and stored_token.token_type == "refresh"
                and stored_token.revoked_at is None
                and stored_token.expires_at > now
                and str(stored_token.id_user) == payload["sub"]
            ):
                tokens_to_revoke.append(stored_token)

    revoked = bool(tokens_to_revoke)

    if revoked:
        api_token.revoke_many(tokens_to_revoke, now)

    return revoked
