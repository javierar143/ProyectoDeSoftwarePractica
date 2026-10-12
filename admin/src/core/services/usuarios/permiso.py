"""Servicios para verificar los permisos de los usuarios."""

from src.core.repositories.usuarios import permiso
from src.core.repositories.usuarios import usuario


def user_has_permission(user_id: int, permiso_nombre: str) -> bool:
    """Comprueba si un usuario activo tiene permiso para una acción.

    Los administradores del sistema tienen acceso a todas las acciones
    protegidas por permisos. Los demás usuarios dependen de los permisos
    asociados a su rol.
    """
    usuario_actual = usuario.get_by_id(user_id)
    tiene_permiso = False

    if usuario_actual is not None and usuario_actual.isActive:
        if usuario_actual.isSystemAdmin:
            tiene_permiso = True
        else:
            tiene_permiso = permiso.has_permission(
                usuario_actual.idRol,
                permiso_nombre,
            )

    return tiene_permiso
