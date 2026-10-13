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

from src.core.services.usuarios import personal, rol, usuario


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


@listado_controller.get("/<int:user_id>/detalle")
def detalle(user_id: int):
    """Muestra los detalles de una cuenta de usuario."""
    require_permission("user_index")

    usuario_seleccionado = usuario.get_by_id(user_id)    

    if usuario_seleccionado is None:
        abort(404, description="Usuario no encontrado.")

    rol_actual = rol.get_by_id(usuario_seleccionado.idRol)
    rol_nombre = rol_actual.nombre if rol_actual is not None else "Sin rol"
    personal_asociado = personal.get_by_id(usuario_seleccionado.idPersonal)

    response = render_template(
        "usuarios/detalle.html",
        usuario=usuario_seleccionado,
        rol_nombre=rol_nombre,
        personal=personal_asociado,
    )
    return response
