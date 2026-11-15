
"""Servicios para la generación y validación de tokens JWT."""

from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app


ACCESS_TOKEN_DURATION = timedelta(minutes=30)
REFRESH_TOKEN_DURATION = timedelta(hours=12)


def generate_access_token(user_id: int) -> str:
    """Genera un JWT de acceso con una duración de 30 minutos."""
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + ACCESS_TOKEN_DURATION,
        "type": "access",
    }

    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm="HS256",
    )

    return token


def decode_access_token(token: str) -> dict | None:
    """Valida la firma, expiración y tipo de un JWT de acceso."""
    payload = None

    try:
        decoded = jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"],
        )

        if decoded.get("type") == "access" and decoded.get("sub"):
            payload = decoded

    except jwt.InvalidTokenError:
        payload = None

    return payload


def generate_refresh_token(user_id: int) -> str:
    """Genera un JWT de renovación con una duración de 12 horas."""
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + REFRESH_TOKEN_DURATION,
        "type": "refresh",
    }

    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm="HS256",
    )

    return token


def decode_refresh_token(token: str) -> dict | None:
    """Valida la firma, expiración y tipo de un JWT de renovación."""
    payload = None

    try:
        decoded = jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"],
        )

        if decoded.get("type") == "refresh" and decoded.get("sub"):
            payload = decoded

    except jwt.InvalidTokenError:
        payload = None

    return payload
