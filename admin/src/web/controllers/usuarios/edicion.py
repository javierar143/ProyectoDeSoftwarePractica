
"""Controlador web para la edición de usuarios."""

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from src.core.security.session import (
    get_authenticated_user_id,
    require_authentication,
)
from src.core.services.usuarios import rol, usuario


edicion_controller = Blueprint(
    "edicion_usuarios",
    __name__,
    url_prefix="/usuarios",
)

def _require_admin() -> None:
    """Verifica que el usuario autenticado tenga permisos de administrador."""
    require_authentication()

    user_id = get_authenticated_user_id()
    usuario_actual = usuario.get_by_id(user_id)

    if usuario_actual is None or not usuario_actual.isSystemAdmin:
        abort(403)

    return None


def _select_user_for_editing() -> None:
    """Valida el usuario seleccionado y guarda su identificador en la sesión."""
    user_id = request.form.get("user_id", "")
    usuario_seleccionado = None

    if not user_id.isdigit():
        abort(400)

    usuario_seleccionado = usuario.get_by_id(int(user_id))

    if usuario_seleccionado is None:
        abort(404)

    session["usuario_editar_id"] = usuario_seleccionado.id_user
    return None


def _get_user_to_edit():
    """Recupera de la sesión el usuario que se está editando."""
    user_id = session.get("usuario_editar_id")
    usuario_seleccionado = None

    if not isinstance(user_id, int):
        abort(400, description="Primero seleccioná un usuario")

    usuario_seleccionado = usuario.get_by_id(user_id)

    if usuario_seleccionado is None:
        session.pop("usuario_editar_id", None)
        abort(404)

    return usuario_seleccionado


def _save_user_changes() -> None:
    """Valida y persiste los cambios del usuario seleccionado."""
    user_id = session.get("usuario_editar_id")
    email = request.form.get("email", "").strip()
    alias = request.form.get("alias", "").strip()
    rol_id_texto = request.form.get("rol_id", "")

    if (
        not isinstance(user_id, int)
        or not email
        or not alias
        or not rol_id_texto.isdigit()
    ):
        abort(400)

    usuario_actualizado = usuario.update(
        user_id=user_id,
        email=email,
        alias=alias,
        rol_id=int(rol_id_texto),
    )

    if usuario_actualizado is None:
        abort(400, description="No se pudo actualizar el usuario")

    session.pop("usuario_editar_id", None)
    return None


def _render_edit_form():
    """Muestra el formulario del usuario seleccionado y los roles disponibles."""
    usuario_seleccionado = _get_user_to_edit()
    roles = rol.get_all()

    response = render_template(
        "usuarios/edit.html",
        usuario=usuario_seleccionado,
        roles=roles,
    )
    return response


@edicion_controller.route("/editar", methods=["GET", "POST"])
def edit():
    """Coordina la selección, edición y actualización de usuarios."""
    _require_admin()
    response = None

    if request.method == "POST":
        accion = request.form.get("accion", "")

        if accion == "seleccionar":
            _select_user_for_editing()
            response = redirect(url_for("usuarios.edicion_usuarios.edit"))

        elif accion == "guardar":
            _save_user_changes()
            response = redirect(url_for("usuarios.listado_usuarios.index"))

        else:
            abort(400, description="Acción no válida")
    else:
        response = _render_edit_form()

    return response
