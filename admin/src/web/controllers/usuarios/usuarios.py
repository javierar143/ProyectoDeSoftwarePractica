"""Controlador web para la administración de usuarios."""

from flask import Blueprint, abort, render_template, request

from src.core.security.session import (
    get_authenticated_user_id,
    require_authentication,
)
from src.core.services.usuarios import usuario
from src.core.security.password import hash_password
from src.web.validators.usuarios.usuarios import validate_user_data


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

@usuarios_controller.route("/nuevo", methods=["GET", "POST"])
def new():
    """Muestra y procesa el formulario de alta de usuarios."""
    require_authentication()

    user_id = get_authenticated_user_id()
    usuario_actual = usuario.get_by_id(user_id)

    if not usuario_actual.isSystemAdmin:
        abort(403)

    response = render_template("usuarios/new.html")

    if request.method == "POST":
        email = request.form.get("email", "")
        alias = request.form.get("alias", "")
        password = request.form.get("password", "")
        rol_id = request.form.get("rol_id", "")
        personal_id = request.form.get("personal_id", "")

        if not validate_user_data(
            email,
            alias,
            password,
            rol_id,
            personal_id,
        ):
            abort(400)

        password_hash = hash_password(password)

        nuevo_usuario = usuario.create(
            email=email,
            alias=alias,
            password_hash=password_hash,
            is_system_admin=False,
            rol_id=int(rol_id),
            personal_id=int(personal_id),
        )

        if nuevo_usuario is None:
            abort(400)

        response = render_template("usuarios/new.html")

    return response