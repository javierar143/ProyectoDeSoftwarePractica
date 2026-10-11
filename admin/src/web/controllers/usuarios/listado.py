"""Controlador web para el listado y la baja lógica de usuarios."""

from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    url_for,
)

from src.core.security.permissions import require_permission

from src.core.services.usuarios import usuario


listado_controller = Blueprint("listado_usuarios", __name__)

@listado_controller.get("/")
def index():
    """Muestra el listado de usuarios al administrador."""
    require_permission("user_index")
    usuarios = usuario.get_all_with_role()

    response = render_template(
        "usuarios/index.html",
        usuarios=usuarios,
    )
    return response


@listado_controller.post("/desactivar")
def desactivar():
    """Bloquea una cuenta si la operación está permitida."""
    require_permission("user_destroy")

    user_id_form = request.form.get("user_id", "")
    if not user_id_form.isdecimal():
        abort(400, description="Identificador de usuario inválido.")

    try:
        usuario_actualizado = usuario.set_active(
            int(user_id_form),
            False,
        )
    except ValueError:
        abort(
            403,
            description="No se puede bloquear una cuenta de administrador.",
        )

    if usuario_actualizado is None:
        abort(404, description="Usuario no encontrado.")

    return redirect(url_for("usuarios.listado_usuarios.index"))


@listado_controller.post("/activar")
def activar():
    """Desbloquea una cuenta si la operación está permitida."""
    require_permission("user_update")

    user_id_form = request.form.get("user_id", "")
    if not user_id_form.isdecimal():
        abort(400, description="Identificador de usuario inválido.")

    try:
        usuario_actualizado = usuario.set_active(
            int(user_id_form),
            True,
        )
    except ValueError:
        abort(403, description="Operación no permitida.")

    if usuario_actualizado is None:
        abort(404, description="Usuario no encontrado.")

    return redirect(url_for("usuarios.listado_usuarios.index"))