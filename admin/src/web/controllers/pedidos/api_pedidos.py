"""Controlador API para la gestión de pedidos de comidas."""

from flask import Blueprint, abort, current_app, jsonify, request

from src.core.services.auth import api_auth
from src.core.services.pedidos import pedidos
from src.core.services.personal.personal import get_sector_asignado
from src.core.services.usuarios.rol import get_by_id
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


def _obtener_id_sector_jefe(user) -> int | None:
    """Obtiene el idSector asignado al Jefe desde el servicio de personal o desde su usuario."""
    id_personal = getattr(user, "idPersonal", None)
    if id_personal is not None:
        sector = get_sector_asignado(id_personal)
        if sector is not None:
            return getattr(sector, "idSector", sector)
    return getattr(user, "idSector", None)


def _autenticar_jefe():
    """
    Valida el Bearer token con el servicio de Javi, verifica que el usuario
    tenga rol Jefe de Servicio y obtiene su sector asignado.
    """
    authorization = request.headers.get("Authorization")
    if authorization is None or not authorization.startswith("Bearer "):
        current_app.logger.warning(
            "Intento de acceso a /api/requests sin token de autenticación"
        )
        abort(401, description="Token de autenticación requerido")

    token = authorization[7:].strip()
    user = api_auth.get_authenticated_user(token)

    if user is None or not user.isActive:
        current_app.logger.warning(
            "Intento de acceso a /api/requests con token inválido o expirado"
        )
        abort(401, description="Token inválido o expirado")

    rol = get_by_id(user.idRol)
    nombre_rol = rol.nombre.strip().lower() if rol and rol.nombre else ""

    if "jefe" not in nombre_rol:
        current_app.logger.warning(
            f"Usuario ID {user.id_user} con rol '{nombre_rol}' intentó gestionar pedidos sin ser Jefe de Servicio"
        )
        abort(
            403,
            description="Solo un Jefe de Servicio puede gestionar pedidos",
        )

    id_sector = _obtener_id_sector_jefe(user)

    if id_sector is None:
        current_app.logger.warning(
            f"Jefe de Servicio ID {user.id_user} sin sector asignado intentó operar en /api/requests"
        )
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
        current_app.logger.warning(
            f"Datos inválidos al crear pedido en sector ID {id_sector}: {resultado}"
        )
        abort(400, description=str(resultado))

    datos = resultado  # type: ignore[assignment]

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
def actualizar_pedido_existente(request_id: int):
    """Endpoint para editar un pedido si aún no fue autorizado/rechazado."""
    user, id_sector = _autenticar_jefe()

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
def eliminar_pedido_existente(request_id: int):
    """Endpoint para dar de baja lógica un pedido confirmado."""
    user, id_sector = _autenticar_jefe()

    pedidos.borrar_pedido(request_id, id_sector_jefe=id_sector)
    current_app.logger.info(
        f"Baja lógica de pedido ID {request_id} realizada por Jefe ID {user.id_user}"
    )
    return "", 204


@bp_resumen_pedidos.route("/requests", methods=["GET"])
def resumen_de_pedidos():
    """
    Endpoint GET /api/summaries/requests para obtener el resumen de pedidos.
    Roles permitidos: Servicio de Alimentación y Jefe de Servicio (limitado a su sector).
    """
    authorization = request.headers.get("Authorization")
    if authorization is None or not authorization.startswith("Bearer "):
        current_app.logger.warning(
            "Intento de acceso a /api/summaries/requests sin token"
        )
        abort(401, description="Token de autenticación requerido")

    token = authorization[7:].strip()
    user = api_auth.get_authenticated_user(token)
    if user is None or not user.isActive:
        current_app.logger.warning(
            "Intento de acceso a /api/summaries/requests con token inválido"
        )
        abort(401, description="Token inválido o expirado")

    rol = get_by_id(user.idRol)
    nombre_rol = rol.nombre.strip().lower() if rol and rol.nombre else ""

    es_jefe = "jefe" in nombre_rol
    es_alimentacion = "alimenta" in nombre_rol

    if not (es_jefe or es_alimentacion):
        current_app.logger.warning(
            f"Usuario ID {user.id_user} con rol '{nombre_rol}' intentó consultar resumen de pedidos sin permisos"
        )
        abort(
            403,
            description="No tiene permisos para consultar el resumen de pedidos",
        )

    es_valido, resultado = validar_filtros_resumen_pedidos(request.args)
    if not es_valido:
        current_app.logger.warning(
            f"Filtros inválidos en /api/summaries/requests: {resultado}"
        )
        abort(400, description=str(resultado))

    filtros = resultado  # type: ignore[assignment]
    id_sector_param = filtros["id_sector"]

    if es_jefe:
        sector_jefe = _obtener_id_sector_jefe(user)
        if sector_jefe is None:
            abort(
                403,
                description="El Jefe de Servicio no tiene un sector asignado",
            )
        if id_sector_param is not None and id_sector_param != sector_jefe:
            abort(
                403,
                description="Un Jefe de Servicio solo puede consultar resúmenes de su propio sector",
            )
        id_sector_filtro = sector_jefe
    else:
        id_sector_filtro = id_sector_param

    resumen = pedidos.obtener_resumen_pedidos(
        id_sector=id_sector_filtro,
        fecha_desde=filtros["fecha_desde"],
        fecha_hasta=filtros["fecha_hasta"],
        id_tipo_comida=filtros["id_tipo_comida"],
        id_tipo_menu=filtros["id_tipo_menu"],
        agrupamiento=filtros["agrupamiento"],
    )
    return jsonify(resumen), 200