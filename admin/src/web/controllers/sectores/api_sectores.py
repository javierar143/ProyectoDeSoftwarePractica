"""Endpoints de la API para la consulta de sectores."""

from flask import Blueprint, g, jsonify, request

from src.core.services.auth import api_auth
from src.core.services.sectores import sector as sector_service
from src.core.services.usuarios import rol as rol_service

ROLES_CONSULTA = ("Servicio de Alimentación", "Sector Comedor")

api_sectores_bp = Blueprint("api_sectores", __name__, url_prefix="/api/sectors")


@api_sectores_bp.before_request
def require_token():
    """Exige un Bearer token válido y rol de Alimentación o Comedor en toda la API de sectores."""
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return jsonify({"error": "Token de autenticación requerido"}), 401

    user = api_auth.get_authenticated_user(authorization[7:])
    if user is None or not user.isActive:
        return jsonify({"error": "Token inválido o expirado"}), 401

    rol = rol_service.get_by_id(user.idRol)
    if rol is None or rol.nombre not in ROLES_CONSULTA:
        return jsonify({"error": "No tenés permisos para acceder a este recurso"}), 403

    g.api_user = user
    return None


def _sector_to_dict(sector) -> dict:
    """Serializa un sector al formato JSON expuesto por la API."""
    return {
        "id": sector.idSector,
        "nombre": sector.nombre,
        "descripcion": sector.descripcion,
        "estado": "activo" if sector.isActive else "inactivo",
    }


@api_sectores_bp.get("")
def listar():
    """Lista los sectores; por defecto solo los activos."""
    estado = request.args.get("estado", "activo")
    if estado not in ("activo", "todos"):
        return jsonify({"error": "El parámetro estado debe ser 'activo' o 'todos'"}), 400

    sectores = sector_service.get_all(solo_activos=estado == "activo")
    return jsonify([_sector_to_dict(sector) for sector in sectores]), 200


@api_sectores_bp.get("/<int:sector_id>")
def detalle(sector_id: int):
    """Devuelve un sector, incluso si está inactivo, para trazabilidad histórica."""
    sector = sector_service.get_by_id(sector_id)
    if sector is None:
        return jsonify({"error": "Sector no encontrado"}), 404

    data = _sector_to_dict(sector)
    data["fecha_creacion"] = sector.inserted_at.isoformat()
    data["fecha_modificacion"] = sector.updated_at.isoformat()
    return jsonify(data), 200