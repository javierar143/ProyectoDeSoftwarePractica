from flask import Blueprint, jsonify, request
from src.core.database import db
from src.core.services.cupos import cupos
from src.core.services.cupos.cupos import CupoServiceError
from src.web.validators.cupos.cupos_validator import validar_entrada_cupo

bp_cupos = Blueprint("cupos", __name__, url_prefix="/api/quotas")

@bp_cupos.route("", methods=["POST"])
def crear_nuevo_cupo():
    # 1. Validación de Request (Web)
    es_valido, resultado = validar_entrada_cupo(request.get_json(silent=True))
    if not es_valido:
        return jsonify({"error": resultado}), 400

    datos = resultado  # type: ignore

    try:
        nuevo_cupo = cupos.create(
            id_sector=int(datos["id_sector"]),
            id_tipo_comida=int(datos["id_tipo_comida"]),
            cant_comensales=int(datos["cant_comensales"])
        )
        db.session.commit()
        return jsonify({
            "mensaje": "Cupo creado exitosamente",
            "idCupo": nuevo_cupo.idCupo,
            "idSector": nuevo_cupo.idSector,
            "idTipoComida": nuevo_cupo.idTipoComida,
            "cantComensales": nuevo_cupo.cantComensales
        }), 201

    except CupoServiceError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error interno al crear el cupo."}), 500