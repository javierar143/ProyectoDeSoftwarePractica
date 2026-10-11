"""Controlador web para el listado de usuarios."""

from flask import Blueprint, abort, render_template

from src.core.security.session import (
    get_authenticated_user_id,
    require_authentication,
)
from src.core.services.usuarios import usuario



listado_controller = Blueprint(
    "listado_usuarios",
    __name__,
)



def _require_admin() -> None:
    """Verifica que el usuario autenticado tenga permisos de administrador."""
    require_authentication()

    user_id = get_authenticated_user_id()
    usuario_actual = usuario.get_by_id(user_id)

    if usuario_actual is None or not usuario_actual.isSystemAdmin:
        abort(403)

    return None


@listado_controller.get("/")
def index():
    """Muestra el listado de usuarios al administrador."""
    _require_admin()

    usuarios = usuario.get_all_with_role()

    return render_template(
        "usuarios/index.html",
        usuarios=usuarios,
    )