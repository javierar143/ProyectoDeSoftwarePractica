
"""Controlador para el alta de usuarios."""

from flask import Blueprint, abort, redirect, render_template, request, url_for

from src.core.security.permissions import require_permission

from src.core.services.usuarios import personal, usuario
from src.web.validators.usuarios.usuarios import validate_user_data


alta_controller = Blueprint("alta_usuarios", __name__)


def _require_admin() -> None:
    """Exige permiso para dar de alta usuarios."""
    require_permission("user_new")


def _get_form_data() -> dict[str, str]:
    """Recupera los datos del formulario de usuario."""
    form_data = {
        "email": request.form.get("email", "").strip(),
        "alias": request.form.get("alias", "").strip(),
        "rol_nombre": request.form.get("rol_nombre", ""),
        "personal_id": request.form.get("personal_id", ""),
        "is_system_admin": request.form.get("is_system_admin", ""),
    }

    return form_data


def _get_personal(dni: str):
    """Busca un registro de Personal mediante su DNI."""
    persona = personal.get_by_dni(dni) if dni else None

    return persona


def _render_form(
    dni: str = "",
    persona_encontrada=None,
    mostrar_existente: bool = False,
    error: str | None = None,
    form_data: dict[str, str] | None = None,
):
    """Renderiza la pantalla de alta con los datos disponibles."""
    response = render_template(
        "usuarios/new.html",
        dni=dni,
        persona_encontrada=persona_encontrada,
        mostrar_existente=mostrar_existente,
        error=error,
        form_data=form_data or {},
    )

    return response


def _search_personal():
    """Procesa la búsqueda de Personal por DNI."""
    dni = request.form.get("dni", "").strip()
    persona = _get_personal(dni)

    response = _render_form(
        dni=dni,
        persona_encontrada=persona,
        mostrar_existente=True,
    )

    return response


def _validate_and_create_user(form_data: dict[str, str]) -> str | None:
    """Valida los datos y crea un usuario asociado a Personal existente."""
    password = request.form.get("password", "")
    error = None

    datos_validos = validate_user_data(
        form_data["email"],
        form_data["alias"],
        password,
        form_data["rol_nombre"],
        form_data["personal_id"],
    )

    if not datos_validos:
        error = "Completá correctamente todos los campos obligatorios."
    else:
        try:
            usuario.create(
                email=form_data["email"],
                alias=form_data["alias"],
                password=password,
                is_system_admin=form_data["is_system_admin"] == "on",
                rol_nombre=form_data["rol_nombre"],
                personal_id=int(form_data["personal_id"]),
            )
        except ValueError as excepcion:
            error = str(excepcion)

    return error


def _create_user():
    """Procesa el alta de un usuario para Personal existente."""
    dni = request.form.get("dni", "").strip()
    persona = _get_personal(dni)
    form_data = _get_form_data()
    error = None

    if persona is None:
        error = "No se encontró el Personal asociado al usuario."
    else:
        error = _validate_and_create_user(form_data)

    if error is None:
        response = redirect(url_for("usuarios.listado_usuarios.index"))
    else:
        response = _render_form(
            dni=dni,
            persona_encontrada=persona,
            mostrar_existente=True,
            error=error,
            form_data=form_data,
        )

    return response


def _handle_post():
    """Deriva la petición POST a la acción correspondiente."""
    acciones = {
        "buscar_personal": _search_personal,
        "crear_usuario": _create_user,
    }
    accion = request.form.get("accion", "")
    manejador = acciones.get(accion)

    if manejador is None:
        abort(400, description="Acción no válida")

    response = manejador()

    return response


@alta_controller.route("/nuevo", methods=["GET", "POST"])
def new():
    """Coordina la pantalla de alta de usuarios."""
    _require_admin()

    if request.method == "GET":
        response = _render_form()
    else:
        response = _handle_post()

    return response
