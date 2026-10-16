"""Controlador API para la gestión de pedidos de comidas."""

from flask import Blueprint, abort, jsonify, request
from werkzeug.exceptions import HTTPException

from src.core.database import db
from src.core.models.Rol import Rol
from src.core.services.auth import api_auth
from src.core.services.pedidos import pedidos
from src.core.services.pedidos.pedidos import obtener_sector_de_personal
from src.web.validators.pedidos.pedidos_validator import (
    validar_actualizacion_pedido,
    validar_creacion_pedido,
    validar_filtros_pedidos,
)

bp_pedidos = Blueprint("pedidos", __name__, url_prefix="/api/requests")


def _autenticar_jefe():
    """
    Valida el Bearer token con el servicio de Javi, verifica que el usuario
    tenga rol Jefe de Servicio y obtiene su sector asignado.
    """
    authorization = request.headers.get("Authorization")
    if authorization is None or not authorization.startswith("Bearer "):
        abort(401, description="Token de autenticación requerido")

    token = authorization[7:].strip()
    user = api_auth.get_authenticated_user(token)

    if user is None or not user.isActive:
        abort(401, description="Token inválido o expirado")

    rol = db.session.get(Rol, user.idRol)
    nombre_rol = rol.nombre.strip().lower() if rol and rol.nombre else ""

    if "jefe" not in nombre_rol:
        abort(
            403,
            description="Solo un Jefe de Servicio puede gestionar pedidos",
        )

    id_sector = obtener_sector_de_personal(getattr(user, "idPersonal", None))
    if id_sector is None:
        id_sector = getattr(user, "idSector", None)

    if id_sector is None:
        abort(
            403,
            description="El Jefe de Servicio no tiene un sector asignado",
        )

    return user, id_sector


@bp_pedidos.route("", methods=["GET"])
def listar_pedidos():
    """Endpoint para listar los pedidos correspondientes al sector del Jefe de Servicio."""
    _, id_sector = _autenticar_jefe()

    es_valido, resultado = validar_filtros_pedidos(request.args)
    if not es_valido:
        abort(400, description=str(resultado))

    filtros = resultado  # type: ignore[assignment]

    items, total, per_page = pedidos.listar_pedidos_sector(
        id_sector=id_sector,
        fecha_desde=filtros["fecha_desde"],
        fecha_hasta=filtros["fecha_hasta"],
        estado_str=filtros["estado_str"],
        id_tipo_comida=filtros["id_tipo_comida"],
        id_tipo_menu=filtros["id_tipo_menu"],
        page=filtros["page"],
    )
    return (
        jsonify(
            {
                "items": items,
                "total": total,
                "page": filtros["page"],
                "per_page": per_page,
            }
        ),
        200,
    )


@bp_pedidos.route("/<int:request_id>", methods=["GET"])
def obtener_pedido(request_id: int):
    """Endpoint para obtener el detalle completo de un pedido por su ID."""
    _, id_sector = _autenticar_jefe()

    detalle = pedidos.obtener_detalle_pedido(
        request_id, id_sector_jefe=id_sector
    )
    return jsonify(detalle), 200


@bp_pedidos.route("", methods=["POST"])
def crear_nuevo_pedido():
    """Endpoint para que un Jefe de Servicio registre un nuevo pedido."""
    user, id_sector = _autenticar_jefe()

    es_valido, resultado = validar_creacion_pedido(
        request.get_json(silent=True)
    )
    if not es_valido:
        abort(400, description=str(resultado))

    datos = resultado  # type: ignore[assignment]

    try:
        kwargs_extra = (
            {"fecha_hasta": datos["fecha_hasta"]}
            if datos.get("fecha_hasta") is not None
            else {}
        )
        nuevo_pedido = pedidos.crear_pedido(
            id_jefe=user.id_user,
            id_sector=id_sector,
            fecha_desde=datos["fecha_desde"],
            periodicidad=datos["periodicidad"],
            comidas=datos["comidas"],
            **kwargs_extra,
        )

        db.session.commit()

        return (
            jsonify(
                {
                    "mensaje": "Pedido creado exitosamente",
                    "idPedido": nuevo_pedido.idPedido,
                    "estado": nuevo_pedido.estado_general.value,
                }
            ),
            201,
        )
    except HTTPException:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        abort(500)


@bp_pedidos.route("/<int:request_id>", methods=["PUT"])
def actualizar_pedido_existente(request_id: int):
    """Endpoint para editar un pedido si aún no fue autorizado/rechazado."""
    _, id_sector = _autenticar_jefe()

    es_valido, resultado = validar_actualizacion_pedido(
        request.get_json(silent=True)
    )
    if not es_valido:
        abort(400, description=str(resultado))

    datos = resultado  # type: ignore[assignment]

    try:
        pedido_actualizado = pedidos.actualizar_pedido(
            id_pedido=request_id,
            comidas=datos["comidas"],
            id_sector_jefe=id_sector,
        )

        db.session.commit()

        return (
            jsonify(
                {
                    "mensaje": "Pedido actualizado exitosamente",
                    "idPedido": pedido_actualizado.idPedido,
                    "estado": pedido_actualizado.estado_general.value,
                }
            ),
            200,
        )
    except HTTPException:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        abort(500)


@bp_pedidos.route("/<int:request_id>", methods=["DELETE"])
def eliminar_pedido_existente(request_id: int):
    """Endpoint para dar de baja lógica un pedido confirmado."""
    _, id_sector = _autenticar_jefe()

    try:
        pedidos.borrar_pedido(request_id, id_sector_jefe=id_sector)
        db.session.commit()
        return "", 204
    except HTTPException:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        abort(500)