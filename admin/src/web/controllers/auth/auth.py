from src.web.validators.auth import validate_login

from src.core.repositories.usuario import get_by_email
from src.core.security.password import verify_password
from flask import render_template, request
from src.core.security.session import set_authenticated_user
from src.core.security.session import clear_session

from . import auth_bp


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    response = render_template("login.html")
    status_code = 200

    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        if not validate_login(email, password):
            status_code = 400
        else:
            usuario = get_by_email(email)
            
            if usuario is None or not verify_password(
                password,
                usuario.password_hash
            ):
                status_code = 401
            else:
                set_authenticated_user(usuario.id_user) #el controlador delega la impplementacion de la sesion al modulo de seguridad en /core/security

    return response, status_code

@auth_bp.route("/logout", methods=["POST"])
def logout():
    clear_session()
    return "", 200