"""Controlador API para la gestión y consulta de cupos por sector."""

from flask import Blueprint, jsonify, request

from src.core.database import db
from src.core.services.cupos import cupos
from src.core.services.cupos.cupos import CupoNotFoundError, CupoServiceError

bp_cupos = Blueprint("cupos", __name__, url_prefix="/api/quotas")


def _serializar_cupo(cupo) -> dict:
    """Convierte una instancia de Cupo a diccionario serializable en JSON."""
    return {
        "idCupo": cupo.idCupo,
        "idSector": cupo.idSector,
        "idTipoComida": cupo.idTipoComida,
        "cantComensales": cupo.cantComensales,
    }


@bp_cupos.route("", methods=["GET"])
def listar_cupos():
    """Endpoint para listar cupos filtrados por sector y tipo de comida."""
    id_sector = request.args.get("sector", type=int)
    id_tipo_comida = request.args.get("tipo_comida", type=int)
    orden = request.args.get("orden", default="asc", type=str)
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=25, type=int)

    items, total = cupos.listar(
        id_sector=id_sector,
        id_tipo_comida=id_tipo_comida,
        orden=orden,
        page=page,
        per_page=per_page,
    )

    return jsonify({
        "items": [_serializar_cupo(c) for c in items],
        "total": total,
        "page": page,
        "per_page": per_page,
    }), 200


@bp_cupos.route("/<int:quota_id>", methods=["GET"])
def obtener_cupo(quota_id: int):
    """Endpoint para consultar el detalle de un cupo por su ID."""
    try:
        cupo = cupos.obtener_por_id(quota_id)
        return jsonify(_serializar_cupo(cupo)), 200
    except CupoNotFoundError as e:
        return jsonify({"error": str(e)}), 404


@bp_cupos.route("", methods=["POST"])
def crear_nuevo_cupo():
    """Endpoint para crear un cupo."""
    data = request.get_json(silent=True)

    if not data or not all(
        k in data for k in ("idSector", "idTipoComida", "cantComensales")
    ):
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    try:
        nuevo_cupo = cupos.create(
            id_sector=data["idSector"],
            id_tipo_comida=data["idTipoComida"],
            cant_comensales=data["cantComensales"],
        )
        db.session.commit()
        return jsonify({
            "mensaje": "Cupo creado exitosamente",
            **_serializar_cupo(nuevo_cupo),
        }), 201

    except CupoServiceError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error interno al crear el cupo."}), 500


@bp_cupos.route("/<int:quota_id>", methods=["PUT"])
def modificar_cupo(quota_id: int):
    """Endpoint para modificar un cupo existente."""
    data = request.get_json(silent=True)

    if not data or not all(
        k in data for k in ("idSector", "idTipoComida", "cantComensales")
    ):
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    try:
        cupo_actualizado = cupos.actualizar(
            id_cupo=quota_id,
            id_sector=data["idSector"],
            id_tipo_comida=data["idTipoComida"],
            cant_comensales=data["cantComensales"],
        )
        db.session.commit()
        return jsonify({
            "mensaje": "Cupo actualizado exitosamente",
            **_serializar_cupo(cupo_actualizado),
        }), 200

    except CupoNotFoundError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 404

    except CupoServiceError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error interno al modificar el cupo."}), 500