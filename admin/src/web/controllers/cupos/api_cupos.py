# src/web/controllers/cupos/api_cupos.py

from flask import Blueprint, request, jsonify
from src.core.database import db
from src.core.services.cupos import cupos
from src.core.services.cupos.cupos import CupoServiceError

bp_cupos = Blueprint('cupos', __name__, url_prefix='/api/quotas')


@bp_cupos.route('', methods=['POST'])
def crear_nuevo_cupo():
    """Endpoint para crear un cupo."""
    data = request.get_json()

    if not data or not all(k in data for k in ("idSector", "idTipoComida", "cantComensales")):
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    try:
        nuevo_cupo = cupos.create(
            id_sector=data['idSector'],
            id_tipo_comida=data['idTipoComida'],
            cant_comensales=data['cantComensales']
        )

        db.session.commit()

        return jsonify({"mensaje": "Cupo creado exitosamente", "idCupo": nuevo_cupo.idCupo}), 201

    except CupoServiceError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error interno o conflicto de datos."}), 409