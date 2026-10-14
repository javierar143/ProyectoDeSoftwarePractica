"""Servicios relacionados con la gestión de roles."""

from src.core.models.Rol import Rol
from src.core.repositories.usuarios import rol


def get_all() -> list[Rol]:
    """Obtiene todos los roles disponibles."""
    roles = rol.get_all()

    return roles


def get_by_id(rol_id: int) -> Rol | None:
    """Obtiene un rol por su identificador."""
    rol_encontrado = rol.get_by_id(rol_id)

    return rol_encontrado
