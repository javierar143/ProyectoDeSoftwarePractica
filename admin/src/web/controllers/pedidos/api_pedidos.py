"""Controlador API para la gestión de pedidos de comidas."""

from flask import Blueprint, abort, current_app, g, jsonify, request

from src.core.services.pedidos import pedidos
from src.core.services.usuarios import permiso as service_permiso
from src.web.decorators.api import token_required, permission_required, sector_assignment_required
from src.web.validators.pedidos.pedidos_validator import (
    validar_actualizacion_pedido,
    validar_creacion_pedido,
    validar_filtros_pedidos,
    validar_filtros_resumen_pedidos,
)

bp_pedidos = Blueprint("pedidos", __name__, url_prefix="/api/requests")
bp_resumen_pedidos = Blueprint(
    "resumen_pedidos", __name__, url_prefix="/api/summaries"
)

@bp_pedidos.route("", methods=["GET"])
@token_required
@permission_required("requests_index")
@sector_assignment_required
def listar_pedidos():
    """Endpoint para listar los pedidos correspondientes al sector del Jefe de Servicio."""
    id_sector = getattr(g, "sector_forzado", None)
    if id_sector is None:
        abort(403, description="El usuario no tiene un sector asignado")

    es_valido, resultado = validar_filtros_pedidos(request.args)
    if not es_valido:
        current_app.logger.warning(
            f"Filtros inválidos al listar pedidos del sector ID {id_sector}: {resultado}"
        )
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
@token_required
@permission_required("requests_index")
@sector_assignment_required
def obtener_pedido(request_id: int):
    """Endpoint para obtener el detalle completo de un pedido por su ID."""
    id_sector = getattr(g, "sector_forzado", None)
    if id_sector is None:
        abort(403, description="El usuario no tiene un sector asignado")

    detalle = pedidos.obtener_detalle_pedido(
        request_id, id_sector_jefe=id_sector
    )
    return jsonify(detalle), 200


@bp_pedidos.route("", methods=["POST"])
@token_required
@permission_required("requests_new")
@sector_assignment_required
def crear_nuevo_pedido():
    """Endpoint para que un Jefe de Servicio registre un nuevo pedido."""
    user = g.user

    id_sector = getattr(g, "sector_forzado", None)
    if id_sector is None:
        abort(403, description="El usuario no tiene un sector asignado")

    es_valido, resultado = validar_creacion_pedido(
        request.get_json(silent=True)
    )
    if not es_valido:
        current_app.logger.warning(
            f"Datos inválidos al crear pedido en sector ID {id_sector}: {resultado}"
        )
        if isinstance(resultado, dict):
            mensaje = "Faltan datos obligatorios" if all(
                m == "Este campo es obligatorio." for m in resultado.values()
            ) else "Revisá los campos indicados."
            return jsonify({"error": mensaje, "field_errors": resultado}), 400
        abort(400, description=str(resultado))

    datos = resultado  # type: ignore[assignment]

    kwargs_extra = {}
    if datos.get("fecha_hasta") is not None:
        kwargs_extra["fecha_hasta"] = datos["fecha_hasta"]
    if datos.get("dias_excluidos") is not None:
        kwargs_extra["dias_excluidos"] = datos["dias_excluidos"]

    resultado_servicio = pedidos.crear_pedido(
        id_jefe=user.id_user,
        id_sector=id_sector,
        fecha_desde=datos["fecha_desde"],
        periodicidad=datos["periodicidad"],
        comidas=datos["comidas"],
        **kwargs_extra,
    )

    if isinstance(resultado_servicio, tuple):
        cuerpo_respuesta, codigo_estado = resultado_servicio
        return jsonify(cuerpo_respuesta), codigo_estado

    nuevo_pedido = resultado_servicio

    current_app.logger.info(
        f"Pedido creado exitosamente ID {nuevo_pedido.idPedido} para sector ID {id_sector} por Jefe ID {user.id_user}"
    )

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


@bp_pedidos.route("/<int:request_id>", methods=["PUT"])
@token_required
@permission_required("requests_update")
@sector_assignment_required
def actualizar_pedido_existente(request_id: int):
    """Endpoint para editar un pedido si aún no fue autorizado/rechazado."""
    user = g.user

    id_sector = getattr(g, "sector_forzado", None)
    if id_sector is None:
        abort(403, description="El usuario no tiene un sector asignado")

    es_valido, resultado = validar_actualizacion_pedido(
        request.get_json(silent=True)
    )
    if not es_valido:
        current_app.logger.warning(
            f"Datos inválidos al actualizar pedido ID {request_id}: {resultado}"
        )
        abort(400, description=str(resultado))

    datos = resultado  # type: ignore[assignment]

    kwargs_extra = {}
    for campo in ("fecha_desde", "fecha_hasta", "periodicidad"):
        if datos.get(campo) is not None:
            kwargs_extra[campo] = datos[campo]

    pedido_actualizado = pedidos.actualizar_pedido(
        id_pedido=request_id,
        comidas=datos["comidas"],
        id_sector_jefe=id_sector,
        **kwargs_extra,
    )

    current_app.logger.info(
        f"Pedido ID {request_id} actualizado exitosamente por Jefe ID {user.id_user}"
    )

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


@bp_pedidos.route("/<int:request_id>", methods=["DELETE"])
@token_required
@permission_required("requests_destroy")
@sector_assignment_required
def eliminar_pedido_existente(request_id: int):
    """Endpoint para dar de baja lógica un pedido confirmado."""
    user = g.user

    id_sector = getattr(g, "sector_forzado", None)
    if id_sector is None:
        abort(403, description="El usuario no tiene un sector asignado")

    pedidos.borrar_pedido(request_id, id_sector_jefe=id_sector)
    current_app.logger.info(
        f"Baja lógica de pedido ID {request_id} realizada por Jefe ID {user.id_user}"
    )
    return "", 204


@bp_resumen_pedidos.route("/requests", methods=["GET"])
@token_required
@permission_required("summaries_index")
@sector_assignment_required
def resumen_de_pedidos():
    """Obtiene el resumen de pedidos acotado al sector si no tiene permiso global."""
    user = g.user

    es_valido, resultado = validar_filtros_resumen_pedidos(request.args)
    if not es_valido:
        current_app.logger.warning(
            f"Filtros inválidos en /api/summaries/requests: {resultado}"
        )
        abort(400, description=str(resultado))

    filtros = resultado  # type: ignore[assignment]
    id_sector_param = filtros["id_sector"]
    sector_forzado = getattr(g, "sector_forzado", None)

    puede_ver_todos = service_permiso.user_has_role_permission(
        user.id_user,
        "personal_manage_all_sectors",
    )

    if puede_ver_todos:
        id_sector_filtro = id_sector_param
    else:
        if sector_forzado is None:
            abort(403, description="El usuario no tiene un sector asignado")
        if id_sector_param is not None and id_sector_param != sector_forzado:
            abort(
                403,
                description="Solo puede consultar resúmenes de su propio sector",
            )
        id_sector_filtro = sector_forzado

    resumen = pedidos.obtener_resumen_pedidos(
        id_sector=id_sector_filtro,
        fecha_desde=filtros["fecha_desde"],
        fecha_hasta=filtros["fecha_hasta"],
        id_tipo_comida=filtros["id_tipo_comida"],
        id_tipo_menu=filtros["id_tipo_menu"],
        agrupamiento=filtros["agrupamiento"],
    )
    return jsonify(resumen), 200