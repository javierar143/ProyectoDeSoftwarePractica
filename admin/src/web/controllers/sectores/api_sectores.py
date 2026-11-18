"""Endpoints de la API para la consulta de sectores."""

from flask import Blueprint, jsonify, request

from src.core.services.sectores import sector as sector_service
from src.web.decorators.api import permission_required, token_required

api_sectores_bp = Blueprint("api_sectores", __name__, url_prefix="/api/sectors")


def _sector_to_dict(sector) -> dict:
    """Serializa un sector al formato JSON expuesto por la API."""
    return {
        "id": sector.idSector,
        "nombre": sector.nombre,
        "descripcion": sector.descripcion,
        "estado": "activo" if sector.isActive else "inactivo",
    }


@api_sectores_bp.get("")
@token_required
@permission_required("sector_index")
def listar():
    """Lista los sectores; por defecto solo los activos."""
    estado = request.args.get("estado", "activo")
    if estado not in ("activo", "todos"):
        return jsonify({"error": "El parámetro estado debe ser 'activo' o 'todos'"}), 400

    sectores = sector_service.get_all(solo_activos=estado == "activo")
    return jsonify([_sector_to_dict(sector) for sector in sectores]), 200


@api_sectores_bp.get("/<int:sector_id>")
@token_required
@permission_required("sector_index")
def detalle(sector_id: int):
    """Devuelve un sector, incluso si está inactivo, para trazabilidad histórica."""
    sector = sector_service.get_by_id(sector_id)
    if sector is None:
        return jsonify({"error": "Sector no encontrado"}), 404

    data = _sector_to_dict(sector)
    data["fecha_creacion"] = sector.inserted_at.isoformat()
    data["fecha_modificacion"] = sector.updated_at.isoformat()
    return jsonify(data), 200