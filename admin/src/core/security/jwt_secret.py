
"""Utilidades para obtener la clave de firma de JWT."""

import hashlib
import hmac
import os


def obtener_clave_jwt() -> str:
    """Obtiene la clave JWT o la deriva de la URL de conexión a la base de datos."""
    clave = os.environ.get("JWT_SECRET_KEY")

    if not clave:
        database_url = os.environ.get("DATABASE_URL")

        if not database_url:
            raise RuntimeError("No se encontró una clave para firmar los JWT.")

        clave = hmac.new(
            database_url.encode("utf-8"),
            b"grupo50-jwt-signing-key-v1",
            hashlib.sha256,
        ).hexdigest()

    return clave
