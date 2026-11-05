"""Controladores web relacionados con la autenticación."""

from flask import flash, redirect, render_template, request, url_for

from src.core.security.session import (
    clear_session,
    set_authenticated_user,
)
from src.core.services.auth.auth import authenticate
from src.web.validators.auth.auth import validate_login
from src.core.services.usuarios import permiso

from . import auth_bp


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Muestra el formulario de login y procesa su autenticación."""
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        if not validate_login(email, password):
            flash("Debés completar todos los campos obligatorios.", "danger")
            return render_template("auth/login.html"), 400

        usuario = authenticate(email, password)

        if usuario is None:
            flash("Credenciales inválidas.", "danger")
            return render_template("auth/login.html"), 401

        # RÚBRICA: Ahor se valida por permisos, no por rol.
        # Si no tiene permiso para administrar usuarios, no entra al backoffice.
        if not permiso.user_has_permission(usuario.id_user, "user_index"):
            flash("No tenés permisos para acceder al panel de administración.", "danger")
            return render_template("auth/login.html"), 403

        set_authenticated_user(usuario.id_user)
        return redirect(url_for("home"))

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Cierra la sesión del usuario y redirige al login."""
    clear_session()
    return redirect(url_for("auth.login"))