"""Controlador web para el listado, filtrado y baja lógica de usuarios."""

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from src.core.security.permissions import require_permission
from src.core.security.session import (
    get_authenticated_user_id,
    require_authentication,
)
from src.core.services.usuarios import personal, rol, usuario
from src.core.services.usuarios import sector as sector_service
from src.core.services.usuarios import busqueda as busqueda_service
from src.web.validators.usuarios.filtros import validar_filtros_listado


listado_controller = Blueprint("listado_usuarios", __name__)


@listado_controller.get("/")
def index():
    """Muestra el listado paginado y filtrado de usuarios."""
    require_permission("user_index")

    filtros, errores_validacion = validar_filtros_listado(request.args)
    resultado_busqueda = busqueda_service.buscar_paginado(filtros)

    return render_template(
        "usuarios/index.html",
        usuarios=resultado_busqueda["usuarios"],
        pagination=resultado_busqueda,
        filtros=filtros,
        errores=errores_validacion,
        roles=rol.get_all(),
        sectores=sector_service.get_all(),
    )


@listado_controller.post("/desactivar")
def desactivar():
    """Bloquea una cuenta si la operación está permitida."""
    require_permission("user_destroy")

    user_id_form = request.form.get("user_id", "")

    if not user_id_form.isdecimal():
        abort(
            400,
            description="Identificador de usuario inválido.",
        )

    user_id = int(user_id_form)

    try:
        usuario_actualizado = usuario.set_active(user_id, False)
    except ValueError as error:
        current_app.logger.warning(
            "Intento prohibido de desactivar la cuenta ID %s: %s",
            user_id,
            error,
        )
        abort(
            403,
            description="No se puede bloquear una cuenta de administrador.",
        )
    except Exception:
        current_app.logger.exception(
            "Error al desactivar el usuario ID %s",
            user_id,
        )
        abort(500)

    if usuario_actualizado is None:
        abort(404, description="Usuario no encontrado.")

    current_app.logger.info(
        "Usuario ID %s desactivado correctamente.",
        user_id,
    )
    flash("El usuario fue bloqueado correctamente.", "success")

    return redirect(url_for("usuarios.listado_usuarios.index"))


@listado_controller.post("/activar")
def activar():
    """Desbloquea una cuenta si la operación está permitida."""
    require_permission("user_update")

    user_id_form = request.form.get("user_id", "")

    if not user_id_form.isdecimal():
        abort(
            400,
            description="Identificador de usuario inválido.",
        )

    user_id = int(user_id_form)

    try:
        usuario_actualizado = usuario.set_active(user_id, True)
    except ValueError as error:
        current_app.logger.warning(
            "Operación no permitida al activar el usuario ID %s: %s",
            user_id,
            error,
        )
        abort(403, description="Operación no permitida.")
    except Exception:
        current_app.logger.exception(
            "Error al activar el usuario ID %s",
            user_id,
        )
        abort(500)

    if usuario_actualizado is None:
        abort(404, description="Usuario no encontrado.")

    current_app.logger.info(
        "Usuario ID %s activado correctamente.",
        user_id,
    )
    flash("El usuario fue desbloqueado correctamente.", "success")

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

    personal_asociado = personal.get_by_id(
        usuario_seleccionado.idPersonal
    )

    return render_template(
        "usuarios/detalle.html",
        usuario=usuario_seleccionado,
        rol_nombre=rol_nombre,
        personal=personal_asociado,
    )


@listado_controller.get("/perfil")
def perfil():
    """Muestra los datos del usuario autenticado."""
    require_authentication()

    user_id = get_authenticated_user_id()

    if user_id is None:
        abort(401)

    usuario_seleccionado = usuario.get_by_id(user_id)

    if usuario_seleccionado is None:
        abort(404, description="Usuario no encontrado.")

    rol_actual = rol.get_by_id(usuario_seleccionado.idRol)
    rol_nombre = rol_actual.nombre if rol_actual is not None else "Sin rol"

    personal_asociado = personal.get_by_id(
        usuario_seleccionado.idPersonal
    )

    return render_template(
        "usuarios/detalle.html",
        usuario=usuario_seleccionado,
        rol_nombre=rol_nombre,
        personal=personal_asociado,
    )