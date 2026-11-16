
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


def token_required(view):
    """Exige un Bearer token válido y un usuario activo."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")

        if not authorization.startswith("Bearer "):
            return jsonify({
                "error": "Token de autenticación requerido."
            }), 401

        token = authorization[7:].strip()

        if not token:
            return jsonify({
                "error": "Token de autenticación requerido."
            }), 401

        user = api_auth.get_authenticated_user(token)

        if user is None:
            return jsonify({
                "error": "Token inválido o expirado."
            }), 401

        g.user = user

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
