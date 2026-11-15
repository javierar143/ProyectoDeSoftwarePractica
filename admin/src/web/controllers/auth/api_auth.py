
"""Controladores REST relacionados con autenticación."""

from flask import Blueprint, abort, current_app, jsonify, request

from src.core.services.auth import api_auth


api_auth_controller = Blueprint(
    "api_auth",
    __name__,
    url_prefix="/api/auth",
)


@api_auth_controller.post("/login")
def login():
    """Autentica al usuario y entrega los tokens de acceso y renovación."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        abort(400, description="El cuerpo de la solicitud debe ser un objeto JSON.")

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not email.strip():
        abort(400, description="El email es obligatorio.")

    if not isinstance(password, str) or not password:
        abort(400, description="La contraseña es obligatoria.")

    tokens = api_auth.login(email.strip(), password)

    if tokens is None:
        abort(401, description="Credenciales inválidas.")

    response = jsonify({
        "access_token": tokens["access_token"]
    })

    response.set_cookie(
        "refresh_token",
        tokens["refresh_token"],
        httponly=True,
        secure=not current_app.debug,
        samesite="Lax",
        max_age=12 * 60 * 60,
        path="/api/auth",
    )

    return response, 200


@api_auth_controller.post("/logout")
def logout():
    """Revoca el token de acceso utilizado para cerrar sesión."""
    authorization = request.headers.get("Authorization", "")

    if not authorization.startswith("Bearer "):
        abort(401, description="Token de autenticación requerido.")

    token = authorization[7:]

    if not api_auth.logout(token):
        abort(401, description="Token inválido o expirado.")

    return jsonify({
        "message": "Sesión cerrada correctamente."
    }), 200


@api_auth_controller.get("/me")
def me():
    """Devuelve los datos del usuario autenticado mediante Bearer token."""
    authorization = request.headers.get("Authorization", "")

    if not authorization.startswith("Bearer "):
        abort(401, description="Token de autenticación requerido.")

    token = authorization[7:]
    user = api_auth.get_authenticated_user(token)

    if user is None:
        abort(401, description="Token inválido o expirado.")

    return jsonify({
        "id": user.id_user,
        "alias": user.alias,
        "email": user.email,
        "idRol": user.idRol,
    }), 200
