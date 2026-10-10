"""Controladores web relacionados con la autenticación."""

from flask import abort, redirect, render_template, request, url_for

from src.core.security.session import (
    clear_session,
    set_authenticated_user,
)
from src.core.services.auth.auth import authenticate
from src.web.validators.auth.auth import validate_login

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
        response = redirect(url_for("home"))

    return response


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Cierra la sesión del usuario y redirige al login."""
    clear_session()
    response = redirect(url_for("auth.login"))

    return response