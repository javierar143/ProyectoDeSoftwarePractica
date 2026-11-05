
"""Controlador web para la edición de usuarios."""

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from werkzeug.exceptions import HTTPException

from src.core.security.permissions import require_permission
from src.core.services.usuarios import rol, usuario
from src.web.validators.usuarios.usuarios import validate_edit_user_data


edicion_controller = Blueprint(
    "edicion_usuarios",
    __name__,
    url_prefix="/usuarios",
)


def _require_admin() -> None:
    """Exige permiso para consultar y gestionar usuarios."""
    require_permission("user_index")


def _select_user_for_editing() -> None:
    """Valida el usuario seleccionado y guarda su identificador en sesión."""
    user_id = request.form.get("user_id", "")

    if not user_id.isdecimal():
        abort(400, description="Identificador de usuario inválido.")

    usuario_seleccionado = usuario.get_by_id(int(user_id))

    if usuario_seleccionado is None:
        abort(404, description="Usuario no encontrado.")

    session["usuario_editar_id"] = usuario_seleccionado.id_user


def _get_user_to_edit():
    """Recupera de la sesión el usuario que se está editando."""
    user_id = session.get("usuario_editar_id")

    if not isinstance(user_id, int):
        abort(
            400,
            description="Primero seleccioná un usuario para editar.",
        )

    usuario_seleccionado = usuario.get_by_id(user_id)

    if usuario_seleccionado is None:
        session.pop("usuario_editar_id", None)
        abort(404, description="Usuario no encontrado.")

    return usuario_seleccionado


def _render_edit_form(
    usuario_seleccionado=None,
    valores=None,
    errores=None,
    status=200,
):
    """Renderiza el formulario con los valores y errores correspondientes."""
    if usuario_seleccionado is None:
        usuario_seleccionado = _get_user_to_edit()

    return (
        render_template(
            "usuarios/edit.html",
            usuario=usuario_seleccionado,
            roles=rol.get_all(),
            valores=valores or {},
            errores=errores or [],
        ),
        status,
    )


def _save_user_changes():
    """Valida y persiste los cambios del usuario seleccionado."""
    user_id = session.get("usuario_editar_id")

    if not isinstance(user_id, int):
        abort(
            400,
            description="Primero seleccioná un usuario para editar.",
        )

    usuario_seleccionado = usuario.get_by_id(user_id)

    if usuario_seleccionado is None:
        session.pop("usuario_editar_id", None)
        abort(404, description="Usuario no encontrado.")

    valores = {
        "email": request.form.get("email", "").strip(),
        "alias": request.form.get("alias", "").strip(),
        "rol_id": request.form.get("rol_id", "").strip(),
        "password": request.form.get("password", ""),
        "confirmar_password": request.form.get("confirmar_password", ""),
        "is_system_admin": request.form.get("is_system_admin") == "on",
    }

    errores = validate_edit_user_data(
        valores["email"],
        valores["alias"],
        valores["rol_id"],
        valores["password"],
        valores["confirmar_password"],
    )

    if errores:
        current_app.logger.warning(
            "Validación fallida al editar usuario ID %s: %s",
            user_id,
            errores,
        )
        return _render_edit_form(
            usuario_seleccionado=usuario_seleccionado,
            valores=valores,
            errores=errores,
            status=422,
        )

    try:
        usuario_actualizado = usuario.update(
            user_id=user_id,
            email=valores["email"],
            alias=valores["alias"],
            rol_id=int(valores["rol_id"]),
            is_system_admin=valores["is_system_admin"],
            password=valores["password"],
        )
    except ValueError as error:
        current_app.logger.info(
            "No se pudo actualizar el usuario ID %s: %s",
            user_id,
            error,
        )
        return _render_edit_form(
            usuario_seleccionado=usuario_seleccionado,
            valores=valores,
            errores=[str(error)],
            status=422,
        )
    except HTTPException:
        raise
    except Exception:
        current_app.logger.exception(
            "Error al actualizar el usuario ID %s",
            user_id,
        )
        abort(
            500,
            description="No se pudo actualizar el usuario.",
        )

    if usuario_actualizado is None:
        abort(404, description="Usuario no encontrado.")

    current_app.logger.info(
        "Usuario ID %s actualizado exitosamente.",
        user_id,
    )

    session.pop("usuario_editar_id", None)
    flash("Los datos del usuario se actualizaron correctamente.", "success")

    return redirect(url_for("usuarios.listado_usuarios.index"))


@edicion_controller.route("/editar", methods=["GET", "POST"])
def edit():
    """Coordina la selección, edición y actualización de usuarios."""
    _require_admin()

    if request.method == "GET":
        return _render_edit_form()

    accion = request.form.get("accion", "")

    if accion == "seleccionar":
        _select_user_for_editing()
        return redirect(url_for("usuarios.edicion_usuarios.edit"))

    if accion == "guardar":
        return _save_user_changes()

    abort(400, description="Acción no válida.")
