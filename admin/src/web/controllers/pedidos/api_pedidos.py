"""Controlador API para la gestión de pedidos de comidas."""

from datetime import date
from flask import Blueprint, request, jsonify
from src.core.database import db
from src.core.services.pedidos import pedidos
from src.core.services.pedidos.pedidos import (
    PedidoValidationError,
    PedidoConflictError,
    PedidoNotFoundError,
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

@bp_pedidos.route("/<int:request_id>", methods=["PUT"])
def actualizar_pedido_existente(request_id: int):
    """Endpoint para editar un pedido si aún no fue autorizado/rechazado."""
    data = request.get_json()

    if not data or "comidas" not in data:
        return jsonify({"error": "Faltan datos obligatorios ('comidas')"}), 400

    try:
        pedido_actualizado = pedidos.actualizar_pedido(
            id_pedido=request_id,
            comidas=data["comidas"],
        )

        db.session.commit()

        return jsonify({
            "mensaje": "Pedido actualizado exitosamente",
            "idPedido": pedido_actualizado.idPedido,
            "estado": pedido_actualizado.estado_general.value,
        }), 200

    except PedidoNotFoundError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 404

    except PedidoValidationError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    except PedidoConflictError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 409

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error interno al actualizar el pedido."}), 500

@bp_pedidos.route("/<int:request_id>", methods=["DELETE"])
def eliminar_pedido_existente(request_id: int):
    """Endpoint para dar de baja un pedido confirmado."""
    try:
        pedidos.borrar_pedido(request_id)
        db.session.commit()
        return "", 204

    except PedidoNotFoundError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 404

    except PedidoConflictError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 409

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error interno al eliminar el pedido."}), 500