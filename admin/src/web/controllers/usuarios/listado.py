"""Controlador web para el listado, filtrado y baja lógica de usuarios."""

from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    url_for,
    current_app,
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
    """Muestra el listado paginado y filtrado de usuarios con filtros combinables."""
    require_permission("user_index")

    filtros, errores_validacion = validar_filtros_listado(request.args)

    resultado_busqueda = busqueda_service.buscar_paginado(filtros)
    

    response = render_template(
        "usuarios/index.html",
        usuarios=resultado_busqueda["usuarios"],
        pagination=resultado_busqueda,
        filtros=filtros,
        errores=errores_validacion,
        roles=rol.get_all(),
        sectores=sector_service.get_all(),
    )

    return response


@listado_controller.post("/desactivar")
def desactivar():
    """Bloquea una cuenta si la operación está permitida."""
    require_permission("user_destroy")

    user_id_form = request.form.get("user_id", "")

    if not user_id_form.isdecimal():
        current_app.logger.warning("Intento de desactivación de usuario con ID no decimal.")
        abort(400, description="Identificador de usuario inválido.")

    user_id = int(user_id_form)

    try:
        usuario_actualizado = usuario.set_active(
            user_id,
            False,
        )
    except ValueError as e:
        current_app.logger.warning(f"Intento prohibido de desactivar cuenta protegida (Admin): usuario ID {user_id}")
        abort(
            403,
            description="No se puede bloquear una cuenta de administrador.",
        )
    except Exception as e:
        current_app.logger.error(f"Error inesperado al desactivar el usuario ID {user_id}: {str(e)}")
        abort(500)

    if usuario_actualizado is None:
        current_app.logger.warning(f"Intento de desactivar usuario inexistente ID {user_id}")
        abort(404, description="Usuario no encontrado.")

    current_app.logger.info(f"Usuario ID {user_id} desactivado correctamente.")
    return redirect(url_for("usuarios.listado_usuarios.index"))


@listado_controller.post("/activar")
def activar():
    """Desbloquea una cuenta si la operación está permitida."""
    require_permission("user_update")

    user_id_form = request.form.get("user_id", "")

    if not user_id_form.isdecimal():
        current_app.logger.warning("Intento de activación de usuario con ID no decimal.")
        abort(400, description="Identificador de usuario inválido.")

    user_id = int(user_id_form)

    try:
        usuario_actualizado = usuario.set_active(
            user_id,
            True,
        )
    except ValueError as e:
        current_app.logger.warning(f"Operación no permitida al intentar activar el usuario ID {user_id}: {str(e)}")
        abort(403, description="Operación no permitida.")
    except Exception as e:
        current_app.logger.error(f"Error inesperado al activar el usuario ID {user_id}: {str(e)}")
        abort(500)

    if usuario_actualizado is None:
        current_app.logger.warning(f"Intento de activar usuario inexistente ID {user_id}")
        abort(404, description="Usuario no encontrado.")

    current_app.logger.info(f"Usuario ID {user_id} activado correctamente.")
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

    response = render_template(
        "usuarios/detalle.html",
        usuario=usuario_seleccionado,
        rol_nombre=rol_nombre,
        personal=personal_asociado,
    )

    return response


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

    response = render_template(
        "usuarios/detalle.html",
        usuario=usuario_seleccionado,
        rol_nombre=rol_nombre,
        personal=personal_asociado,
    )

    return response