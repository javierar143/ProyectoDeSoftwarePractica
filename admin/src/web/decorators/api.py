
"""Decoradores de autenticación y autorización para la API."""

from functools import wraps

from flask import g, jsonify, request

from src.core.services.auth import api_auth
from src.core.services.usuarios import permiso as service_permiso
from src.core.services.usuarios import rol as service_rol


ROLES_OPERATIVOS = {
    "Jefe de Servicio",
    "Servicio de Alimentación",
    "Sector Comedor",
}

ACCOUNT_BLOCKED_MESSAGE = "La cuenta está bloqueada. Contactá al administrador."


def authenticate_api_request():
    """Valida el Bearer token y marca la cuenta inactiva con un código estable."""
    if request.method == "OPTIONS":
        return None

    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer ") or not authorization[7:].strip():
        return jsonify({"error": "Token de autenticación requerido."}), 401

    user, error_code = api_auth.get_authenticated_user_status(
        authorization[7:].strip()
    )
    if error_code == api_auth.ACCOUNT_BLOCKED_CODE:
        return jsonify({
            "code": api_auth.ACCOUNT_BLOCKED_CODE,
            "error": ACCOUNT_BLOCKED_MESSAGE,
        }), 401
    if user is None:
        return jsonify({"error": "Token inválido o expirado."}), 401

    g.user = user
    g.current_user = user
    return None


def token_required(view):
    """Exige un Bearer token válido y un usuario activo."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        response = authenticate_api_request()
        if response is not None:
            return response

        return view(*args, **kwargs)

    return wrapped


def permission_required(permiso_requerido: str):
    """Exige un rol operativo habilitado y el permiso correspondiente."""

    def decorator(view):

        @wraps(view)
        def wrapped(*args, **kwargs):
            user = getattr(g, "user", None)

            if user is None:
                return jsonify({
                    "error": "Token de autenticación requerido."
                }), 401

            rol = service_rol.get_by_id(user.idRol)

            if rol is None or rol.nombre not in ROLES_OPERATIVOS:
                return jsonify({
                    "error": "El usuario no tiene un rol operativo habilitado."
                }), 403

            if not service_permiso.user_has_role_permission(
                user.id_user,
                permiso_requerido,
            ):
                return jsonify({
                    "error": "No tenés permisos para realizar esta operación."
                }), 403

            return view(*args, **kwargs)

        return wrapped

    return decorator


def sector_assignment_required(view):
    """Determina el alcance de sector permitido para el usuario."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = getattr(g, "user", None)

        if user is None:
            return jsonify({
                "error": "Token de autenticación requerido."
            }), 401

        puede_ver_todos = service_permiso.user_has_role_permission(
            user.id_user,
            "personal_manage_all_sectors",
        )

        if puede_ver_todos:
            g.sector_forzado = None
        else:
            if user.idSector is None:
                return jsonify({
                    "error": "El usuario no posee un sector asignado."
                }), 403

            g.sector_forzado = user.idSector

        return view(*args, **kwargs)

    return wrapped
