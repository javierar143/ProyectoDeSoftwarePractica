"""Controladores web relacionados con la autenticación."""

from flask import abort, render_template, request

from src.core.security.session import (
    clear_session,
    set_authenticated_user,
)
from src.core.services.auth import authenticate
from src.web.validators.auth import validate_login

from . import auth_bp


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Muestra el formulario de login y procesa su autenticación."""
    response = render_template("auth/login.html")

    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        if not validate_login(email, password):
            abort(400)

        usuario = authenticate(email, password)

        if usuario is None:
            abort(401)

        set_authenticated_user(usuario.id_user)

    return response


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Cierra la sesión del usuario autenticado."""
    clear_session()

    return "", 200