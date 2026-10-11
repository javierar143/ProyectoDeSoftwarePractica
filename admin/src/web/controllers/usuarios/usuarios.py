"""Controlador web para la administración de usuarios."""

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from src.core.security.session import (
    get_authenticated_user_id,
    require_authentication,
)
from src.core.services.usuarios import personal, rol, usuario
from src.web.validators.usuarios.usuarios import validate_user_data


usuarios_controller = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/usuarios",
)


def _require_admin() -> None:
    """Verifica que el usuario autenticado tenga permisos de administrador."""
    require_authentication()

    user_id = get_authenticated_user_id()
    usuario_actual = usuario.get_by_id(user_id)

    if not usuario_actual.isSystemAdmin:
        abort(403)

    return None


def _get_persona_by_dni() -> tuple[str, dict | None]:
    """Obtiene el DNI del formulario y busca el personal correspondiente."""
    dni = request.form.get("dni", "").strip()
    persona_encontrada = None

    if dni:
        persona_encontrada = personal.get_by_dni(dni)

    return dni, persona_encontrada


def _create_user() -> None:
    """Valida los datos del formulario y solicita la creación del usuario."""
    email = request.form.get("email", "")
    alias = request.form.get("alias", "")
    password = request.form.get("password", "")
    rol_nombre = request.form.get("rol_nombre", "")
    personal_id = request.form.get("personal_id", "")
    is_system_admin = request.form.get("is_system_admin") == "on"

    datos_validos = validate_user_data(
        email,
        alias,
        password,
        rol_nombre,
        personal_id,
    )

    if not datos_validos:
        
        abort(400, description="VALIDATOR")
        

    nuevo_usuario = usuario.create(
        email=email,
        alias=alias,
        password=password,
        is_system_admin=is_system_admin,
        rol_nombre=rol_nombre,
        personal_id=int(personal_id),
    )

    if nuevo_usuario is None:
        
        abort(400, description="SERVICE")
        

    return None


@usuarios_controller.get("/")
def index():
    """Muestra el listado de usuarios al administrador."""
    _require_admin()

    usuarios = usuario.get_all_with_role()

    return render_template(
        "usuarios/index.html",
        usuarios=usuarios,
    )


@usuarios_controller.route("/nuevo", methods=["GET", "POST"])
def new():
    """Muestra y procesa el formulario de alta de usuarios."""
    _require_admin()

    dni = ""
    persona_encontrada = None
    mostrar_existente = False

    if request.method == "POST":
        accion = request.form.get("accion", "")

        if accion == "buscar_personal":
            dni, persona_encontrada = _get_persona_by_dni()
            mostrar_existente = True

        elif accion == "crear_usuario":
            _create_user()
            return redirect(url_for("usuarios.index"))      

        else:
           
            abort(400, description=f"Acción no válida: {accion!r}")

    return render_template(
        "usuarios/new.html",
        persona_encontrada=persona_encontrada,
        dni=dni,
        mostrar_existente=mostrar_existente,
    )


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
    



@usuarios_controller.route("/editar", methods=["GET", "POST"])
def edit():
    """Coordina la selección, edición y actualización de usuarios."""
    _require_admin()
    response = None

    if request.method == "POST":
        accion = request.form.get("accion", "")

        if accion == "seleccionar":
            _select_user_for_editing()
            response = redirect(url_for("usuarios.edit"))

        elif accion == "guardar":
            _save_user_changes()
            response = redirect(url_for("usuarios.index"))

        else:
            abort(400, description="Acción no válida")
    else:
        response = _render_edit_form()

    return response
