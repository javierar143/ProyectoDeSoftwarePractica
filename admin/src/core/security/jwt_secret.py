
"""Utilidades para obtener la clave de firma de JWT."""

import os


def obtener_clave_jwt() -> str:
    """Obtiene la clave JWT configurada en el entorno."""
    clave = os.environ.get("JWT_SECRET_KEY")

    if not clave:
        raise RuntimeError("La variable de entorno JWT_SECRET_KEY es obligatoria.")

    return clave
