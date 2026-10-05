"""Servicios relacionados con la autenticación web."""

from src.core.models.Usuario import Usuario
from src.core.repositories import usuario
from src.core.security.password import verify_password


def authenticate(email: str, password: str) -> Usuario | None:
    """Autentica un usuario mediante email y contraseña."""
    stored_user = usuario.get_by_email(email)
    authenticated_user = None

    if stored_user is not None and stored_user.isActive:
        if verify_password(password, stored_user.password_hash):
            authenticated_user = stored_user

    return authenticated_user