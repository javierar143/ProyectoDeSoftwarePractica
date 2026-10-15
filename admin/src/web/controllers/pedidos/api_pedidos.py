"""Controlador API para la gestión de pedidos de comidas."""

from datetime import date
from flask import Blueprint, jsonify, request

from src.core.database import db
from src.core.models.Rol import Rol
from src.core.services.auth import api_auth
from src.core.services.pedidos import pedidos
from src.core.services.pedidos.pedidos import (
    PedidoConflictError,
    PedidoForbiddenError,
    PedidoNotFoundError,
    PedidoValidationError,
    obtener_sector_de_personal,
)

bp_pedidos = Blueprint("pedidos", __name__, url_prefix="/api/requests")


def _autenticar_jefe():
    """
    Valida el Bearer token con el servicio de Javi, verifica que el usuario
    tenga rol Jefe de Servicio y obtiene su sector asignado.
    """
    authorization = request.headers.get("Authorization")
    if authorization is None or not authorization.startswith("Bearer "):
        return None, None, (jsonify({"error": "Token de autenticación requerido"}), 401)

    token = authorization[7:]
    user = api_auth.get_authenticated_user(token)

    if user is None or not user.isActive:
        return None, None, (jsonify({"error": "Token inválido o expirado"}), 401)

    rol = db.session.get(Rol, user.idRol)
    nombre_rol = rol.nombre.strip().lower() if rol and rol.nombre else ""

    if "jefe" not in nombre_rol:
        return (
            None,
            None,
            (jsonify({"error": "Solo un Jefe de Servicio puede gestionar pedidos"}), 403),
        )

    id_sector = obtener_sector_de_personal(user.idPersonal)
    if id_sector is None:
        return (
            None,
            None,
            (jsonify({"error": "El Jefe de Servicio no tiene un sector asignado"}), 403),
        )

    return user, id_sector, None


@bp_pedidos.route("", methods=["GET"])
def listar_pedidos():
    """Endpoint para listar los pedidos correspondientes al sector del Jefe de Servicio."""
    _, id_sector, error_auth = _autenticar_jefe()
    if error_auth:
        return error_auth

    fecha_desde_str = request.args.get("fecha_desde")
    fecha_hasta_str = request.args.get("fecha_hasta")
    estado = request.args.get("estado")
    id_tipo_comida = request.args.get("tipo_comida", type=int)
    id_tipo_menu = request.args.get("tipo_menu", type=int)
    page = request.args.get("page", default=1, type=int)

    try:
        fecha_desde = date.fromisoformat(fecha_desde_str) if fecha_desde_str else None
        fecha_hasta = date.fromisoformat(fecha_hasta_str) if fecha_hasta_str else None
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400

    try:
        items, total, per_page = pedidos.listar_pedidos_sector(
            id_sector=id_sector,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            estado_str=estado,
            id_tipo_comida=id_tipo_comida,
            id_tipo_menu=id_tipo_menu,
            page=page,
        )
        return jsonify({
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
        }), 200
    except PedidoValidationError as e:
        return jsonify({"error": str(e)}), 400


@bp_pedidos.route("/<int:request_id>", methods=["GET"])
def obtener_pedido(request_id: int):
    """Endpoint para obtener el detalle completo de un pedido por su ID."""
    _, id_sector, error_auth = _autenticar_jefe()
    if error_auth:
        return error_auth

    try:
        detalle = pedidos.obtener_detalle_pedido(request_id, id_sector_jefe=id_sector)
        return jsonify(detalle), 200
    except PedidoNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except PedidoForbiddenError as e:
        return jsonify({"error": str(e)}), 403


@bp_pedidos.route("", methods=["POST"])
def crear_nuevo_pedido():
    """Endpoint para que un Jefe de Servicio registre un nuevo pedido."""
    user, id_sector, error_auth = _autenticar_jefe()
    if error_auth:
        return error_auth

    data = request.get_json(silent=True)

    campos_requeridos = ("fecha_desde", "periodicidad", "comidas")
    if not data or not all(k in data for k in campos_requeridos):
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    try:
        fecha_parsed = date.fromisoformat(data["fecha_desde"])
    except (ValueError, TypeError):
        return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400

    try:
        nuevo_pedido = pedidos.crear_pedido(
            id_jefe=user.id_user,
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
    _, id_sector, error_auth = _autenticar_jefe()
    if error_auth:
        return error_auth

    data = request.get_json(silent=True)

    if not data or "comidas" not in data:
        return jsonify({"error": "Faltan datos obligatorios ('comidas')"}), 400

    try:
        pedido_actualizado = pedidos.actualizar_pedido(
            id_pedido=request_id,
            comidas=data["comidas"],
            id_sector_jefe=id_sector,
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

    except PedidoForbiddenError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 403

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
    _, id_sector, error_auth = _autenticar_jefe()
    if error_auth:
        return error_auth

    try:
        pedidos.borrar_pedido(request_id, id_sector_jefe=id_sector)
        db.session.commit()
        return "", 204

    except PedidoNotFoundError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 404

    except PedidoForbiddenError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 403

    except PedidoConflictError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 409

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error interno al eliminar el pedido."}), 500