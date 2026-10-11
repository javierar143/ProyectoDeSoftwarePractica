"""Servicios para verificar permisos de los usuarios."""

from src.core.repositories.usuarios import permiso
from src.core.repositories.usuarios import usuario


def user_has_permission(user_id: int, permiso_nombre: str) -> bool:
    """Comprueba si un usuario activo posee un permiso mediante su rol."""
    usuario_actual = usuario.get_by_id(user_id)
    tiene_permiso = False

    if usuario_actual is not None and usuario_actual.isActive:
        tiene_permiso = permiso.has_permission(
            usuario_actual.idRol,
            permiso_nombre,
        )

    return tiene_permiso
