"""Controlador web para la administración de usuarios."""

from flask import Blueprint, abort, render_template

from src.core.security.session import (
    get_authenticated_user_id,
    require_authentication,
)
from src.core.services import usuario


usuarios_controller = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/usuarios",
)


@usuarios_controller.get("/")
def index():
    """Muestra el listado de usuarios al administrador."""
    require_authentication()

    user_id = get_authenticated_user_id()
    usuario_actual = usuario.get_by_id(user_id)

    if not usuario_actual.isSystemAdmin:
        abort(403)

    usuarios = usuario.get_all_with_role()

    return render_template(
        "usuarios/index.html",
        usuarios=usuarios,
    )