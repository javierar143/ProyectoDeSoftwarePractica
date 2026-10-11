"""Controles de autorización para las acciones de la aplicación."""

from flask import abort

from src.core.security.session import (
    get_authenticated_user_id,
    require_authentication,
)
from src.core.services.usuarios import permiso


def require_permission(permiso_nombre: str) -> None:
    """Exige autenticación y el permiso necesario para una acción."""
    require_authentication()
    user_id = get_authenticated_user_id()

    if user_id is None:
        abort(401)

    if not permiso.user_has_permission(user_id, permiso_nombre):
        abort(403)

    return None
