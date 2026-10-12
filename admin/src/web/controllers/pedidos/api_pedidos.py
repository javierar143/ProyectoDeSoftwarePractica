"""Controlador API para la gestión de pedidos de comidas."""

from datetime import date
from flask import Blueprint, request, jsonify
from src.core.database import db
from src.core.services.pedidos import pedidos
from src.core.services.pedidos.pedidos import (
    PedidoValidationError,
    PedidoConflictError,
)

bp_pedidos = Blueprint("pedidos", __name__, url_prefix="/api/requests")


@bp_pedidos.route("", methods=["POST"])
def crear_nuevo_pedido():
    """Endpoint para que un Jefe de Servicio registre un nuevo pedido."""
    data = request.get_json()

    campos_requeridos = ("fecha_desde", "periodicidad", "comidas")
    if not data or not all(k in data for k in campos_requeridos):
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    try:
        fecha_parsed = date.fromisoformat(data["fecha_desde"])
    except (ValueError, TypeError):
        return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400

    id_jefe = 1
    id_sector = 1

    try:
        nuevo_pedido = pedidos.crear_pedido(
            id_jefe=id_jefe,
            id_sector=id_sector,
            fecha_desde=fecha_parsed,
            periodicidad=data["periodicidad"],
            comidas=data["comidas"],
        )

        db.session.commit()

        return jsonify({
            "mensaje": "Pedido creado exitosamente",
            "idPedido": nuevo_pedido.idPedido,
            "estado": nuevo_pedido.estado_general.value,
        }), 201

    except PedidoValidationError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    except PedidoConflictError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 409

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error interno al procesar el pedido."}), 500