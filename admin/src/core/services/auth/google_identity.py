"""Verificación de identidad para ID tokens de Google."""

from flask import current_app
from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport.requests import Request
from google.oauth2.id_token import verify_oauth2_token


class GoogleIdentityError(Exception):
    """Error base del servicio de identidad de Google."""


class InvalidGoogleTokenError(GoogleIdentityError):
    """El ID token no es válido o no acredita un email verificado."""


class GoogleIdentityUnavailableError(GoogleIdentityError):
    """No fue posible validar el token por un problema de conectividad."""


class GoogleIdentityConfigurationError(GoogleIdentityError):
    """Falta la configuración del Client ID esperado por el servidor."""


def get_verified_email(id_token: str) -> str:
    """Valida el ID token y devuelve el email de sus claims verificados."""
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")

    if not isinstance(client_id, str) or not client_id.strip():
        raise GoogleIdentityConfigurationError

    try:
        claims = verify_oauth2_token(
            id_token,
            Request(),
            audience=client_id,
        )
    except TransportError as error:
        raise GoogleIdentityUnavailableError from error
    except GoogleAuthError as error:
        # verify_oauth2_token usa GoogleAuthError para un emisor no permitido.
        raise InvalidGoogleTokenError from error
    except ValueError as error:
        raise InvalidGoogleTokenError from error

    issuer = claims.get("iss")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        raise InvalidGoogleTokenError

    if claims.get("email_verified") is not True:
        raise InvalidGoogleTokenError

    email = claims.get("email")
    if not isinstance(email, str) or not email.strip():
        raise InvalidGoogleTokenError

    return email.strip()
