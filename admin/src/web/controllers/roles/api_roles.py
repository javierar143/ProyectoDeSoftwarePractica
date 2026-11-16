
"""Endpoints de la API para consultar los roles operativos."""

from flask import Blueprint, abort, jsonify, request

from src.core.services.auth import api_auth
from src.core.services.usuarios import rol as rol_service


api_roles_bp = Blueprint(
    "api_roles",
    __name__,
    url_prefix="/api/roles",
)


@api_roles_bp.before_request
def require_token():
    """Exige un token Bearer válido, excepto en las peticiones OPTIONS."""

    # El preflight CORS no lleva credenciales de autenticación.
    if request.method == "OPTIONS":
        return None

    authorization = request.headers.get("Authorization", "")

    if not authorization.startswith("Bearer "):
        abort(401, description="Token de autenticación requerido.")

    user = api_auth.get_authenticated_user(authorization[7:])

    if user is None or not user.isActive:
        abort(401, description="Token inválido o expirado.")


@api_roles_bp.get("/operational")
def listar_roles_operativos():
    """Devuelve los identificadores de los tres roles operativos."""

    roles = rol_service.get_all()

    roles_por_nombre = {
        rol.nombre: rol.idRol
        for rol in roles
    }

    nombres_requeridos = (
        "Jefe de Servicio",
        "Servicio de Alimentación",
        "Sector Comedor",
    )

    if not all(nombre in roles_por_nombre for nombre in nombres_requeridos):
        abort(500, description="No se encuentran todos los roles operativos.")

    return jsonify({
        "jefeServicio": roles_por_nombre["Jefe de Servicio"],
        "servicioAlimentacion": roles_por_nombre["Servicio de Alimentación"],
        "sectorComedor": roles_por_nombre["Sector Comedor"],
    }), 200
