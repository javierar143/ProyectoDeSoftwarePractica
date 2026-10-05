"""Controladores REST relacionados con autenticación."""

from flask import Blueprint, jsonify, request

from src.core.services.auth import api_auth


api_auth_controller = Blueprint(
    "api_auth",
    __name__,
    url_prefix="/api/auth",
)


@api_auth_controller.post("/login")
def login():
    """Autentica un usuario y devuelve un token de acceso."""
    data = request.get_json(silent=True)
    response = None

    if data is None:
        response = jsonify(
            {"error": "El cuerpo de la solicitud debe ser JSON"}
        ), 400
    else:
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            response = jsonify(
                {"error": "Email y contraseña son obligatorios"}
            ), 400
        else:
            token = api_auth.login(email, password)

            if token is None:
                response = jsonify(
                    {"error": "Credenciales inválidas"}
                ), 401
            else:
                response = jsonify({"token": token}), 200

    return response


@api_auth_controller.post("/logout")
def logout():
    """Revoca el token utilizado para cerrar sesión."""
    authorization = request.headers.get("Authorization")
    response = None

    if authorization is None or not authorization.startswith("Bearer "):
        response = jsonify(
            {"error": "Token de autenticación requerido"}
        ), 401
    else:
        token = authorization[7:]
        revoked = api_auth.logout(token)

        if revoked:
            response = jsonify(
                {"message": "Sesión cerrada correctamente"}
            ), 200
        else:
            response = jsonify({"error": "Token inválido"}), 401

    return response


@api_auth_controller.get("/me")
def me():
    """Devuelve los datos del usuario autenticado mediante Bearer token."""
    authorization = request.headers.get("Authorization")
    response = None

    if authorization is None or not authorization.startswith("Bearer "):
        response = jsonify(
            {"error": "Token de autenticación requerido"}
        ), 401
    else:
        token = authorization[7:]
        user = api_auth.get_authenticated_user(token)

        if user is None:
            response = jsonify(
                {"error": "Token inválido o expirado"}
            ), 401
        else:
            response = jsonify(
                {
                    "id": user.id_user,
                    "alias": user.alias,
                    "email": user.email,
                    "idRol": user.idRol,
                }
            ), 200

    return response