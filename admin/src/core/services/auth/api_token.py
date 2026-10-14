"""Servicios relacionados con la generación de tokens de la API."""

import hashlib
import secrets


def generate_token() -> str:
    """Genera un token aleatorio seguro para autenticar peticiones de la API."""
    token = secrets.token_urlsafe(32)

    return token


def hash_token(token: str) -> str:
    """Genera el hash SHA-256 de un token de autenticación."""
    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    return token_hash

#Seguridad: si se filtra la base de datos, el atacante no obtiene directamente los tokens utilizables.