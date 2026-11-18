
"""Controladores REST relacionados con autenticación."""

from flask import Blueprint, abort, current_app, g, jsonify, request

from src.core.services.auth import api_auth
from src.core.services.auth import google_identity
from src.core.services.personal import personal as personal_service
from src.core.services.sectores import sector as sector_service
from src.core.services.usuarios import rol as rol_service
from src.web.decorators.api import authenticate_api_request


api_auth_controller = Blueprint(
    "api_auth",
    __name__,
    url_prefix="/api/auth",
)


def _response_with_tokens(tokens: dict[str, str]):
    """Devuelve el access token y establece la cookie refresh de la API."""
    response = jsonify({
        "access_token": tokens["access_token"]
    })

    response.set_cookie(
        "refresh_token",
        tokens["refresh_token"],
        httponly=True,
        secure=current_app.config["COOKIE_SECURE"],
        samesite="Lax",
        max_age=12 * 60 * 60,
        path="/api/auth",
    )

    return response, 200


@api_auth_controller.post("/login")
def login():
    """Autentica al usuario y entrega los tokens de acceso y renovación."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        abort(400, description="El cuerpo de la solicitud debe ser un objeto JSON.")

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not email.strip():
        return jsonify({"error": "El email es obligatorio.", "field_errors": {"email": "El email es obligatorio."}}), 400

    if not isinstance(password, str) or not password:
        return jsonify({"error": "La contraseña es obligatoria.", "field_errors": {"password": "La contraseña es obligatoria."}}), 400

    try:
        tokens = api_auth.login(email.strip(), password)
    except api_auth.UsuarioBloqueadoError:
        abort(
            403,
            description="La cuenta está bloqueada. Contactá al administrador.",
        )

    if tokens is None:
        abort(401, description="Credenciales inválidas.")

    return _response_with_tokens(tokens)


@api_auth_controller.post("/google")
def login_google():
    """Autentica un usuario existente mediante un ID token de Google."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        abort(400, description="El cuerpo de la solicitud debe ser un objeto JSON.")

    id_token = data.get("id_token")
    if not isinstance(id_token, str) or not id_token.strip():
        abort(400, description="El ID token de Google es obligatorio.")

    try:
        tokens = api_auth.login_with_google(id_token)
    except api_auth.GoogleLoginTokenInvalidError:
        abort(401, description="El token de Google no es válido.")
    except api_auth.GoogleLoginAccessDeniedError:
        abort(403, description="La cuenta no tiene acceso habilitado.")
    except google_identity.GoogleIdentityConfigurationError:
        abort(500, description="La autenticación con Google no está disponible.")
    except google_identity.GoogleIdentityUnavailableError:
        abort(500, description="La autenticación con Google no está disponible.")

    return _response_with_tokens(tokens)


@api_auth_controller.post("/logout")
def logout():
    """Cierra la sesión revocando los tokens y eliminando la cookie."""
    authorization = request.headers.get("Authorization", "")
    access_token = None

    if authorization.startswith("Bearer "):
        access_token = authorization.removeprefix("Bearer ").strip()

    refresh_token = request.cookies.get("refresh_token")

    api_auth.logout(access_token, refresh_token)

    response = jsonify({"message": "Sesión cerrada correctamente."})

    response.delete_cookie(
        "refresh_token",
        path="/api/auth",
        httponly=True,
        secure=current_app.config["COOKIE_SECURE"],
        samesite="Lax",
    )

    return response, 200

@api_auth_controller.get("/me")
def me():
    """Devuelve los datos del usuario autenticado mediante Bearer token."""
    auth_error = authenticate_api_request()
    if auth_error is not None:
        return auth_error

    user = g.user

    personal = personal_service.get_by_id(user.idPersonal)
    rol = rol_service.get_by_id(user.idRol)

    sector = (
        sector_service.get_by_id(user.idSector)
        if user.idSector is not None
        else None
    )

    return jsonify({
        "id": user.id_user,
        "alias": user.alias,
        "email": user.email,
        "idRol": user.idRol,
        "nombre": personal.nombre if personal else None,
        "apellido": personal.apellido if personal else None,
        "rol": rol.nombre if rol else None,
        "sector": {
            "id": sector.idSector,
            "nombre": sector.nombre,
        } if sector else None,
    }), 200

@api_auth_controller.post("/refresh")
def refresh():
    """Renueva el token de acceso utilizando el refresh token de la cookie."""
    refresh_token = request.cookies.get("refresh_token")
    response = None

    if refresh_token:
        try:
            access_token = api_auth.refresh_access_token(refresh_token)
        except api_auth.UsuarioBloqueadoError:
            return jsonify({
                "code": api_auth.ACCOUNT_BLOCKED_CODE,
                "error": "La cuenta está bloqueada. Contactá al administrador.",
            }), 401

        if access_token is not None:
            response = jsonify({"access_token": access_token}), 200

    if response is None:
        response = jsonify({"message": "Refresh token inválido o expirado."}), 401

    return response
