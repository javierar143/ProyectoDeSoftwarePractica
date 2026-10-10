"""Servicios relacionados con la gestión de roles."""

from src.core.models.Rol import Rol
from src.core.repositories.usuarios import rol


def get_all() -> list[Rol]:
    """Obtiene todos los roles disponibles."""
    roles = rol.get_all()

    return roles