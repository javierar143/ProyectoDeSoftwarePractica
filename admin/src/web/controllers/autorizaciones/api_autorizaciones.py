from flask import Blueprint, jsonify, request, session, current_app
from src.core.services.autorizaciones import autorizaciones as autorizaciones_service
from src.core.services.autorizaciones.autorizaciones import (
    RecursoNoEncontradoError,
    ConflictoEstadoError,
)

api_autorizaciones_controller = Blueprint(
    "api_autorizaciones",
    __name__,
    url_prefix="/api",
)


def obtener_id_usuario_autenticado(data: dict | None = None) -> int:
    """Obtiene el id del usuario desde la sesion/token del servidor"""

    from flask import g
    if hasattr(g, "current_user") and g.current_user:
        return getattr(g.current_user, "id_user", None)
    if "user_id" in session:
        return session["user_id"]

    if data and "id_evaluador" in data:
        return data.get("id_evaluador")
    if data and "id_user" in data:
        return data.get("id_user")
    return 1


# <------ Endpoints de Autorizaciones ------>

@api_autorizaciones_controller.route("/authorizations", methods=["GET"])
def listar_autorizaciones():
    """Lista pedidos confirmados/autorizados/rechazados con totales pedidos vs autorizados"""

    filtros = {
        "fecha_desde": request.args.get("fecha_desde"),
        "fecha_hasta": request.args.get("fecha_hasta"),
        "sector": request.args.get("sector", type=int),
        "tipo_comida": request.args.get("tipo_comida", type=int),
        "tipo_menu": request.args.get("tipo_menu", type=int),
        "estado": request.args.get("estado"),
    }
    try:
        resultado = autorizaciones_service.listar_pedidos_para_autorizacion(filtros)
        return jsonify(resultado), 200
    except ValueError as e:
        current_app.logger.warning(f"Error de validación al listar autorizaciones: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error interno al listar autorizaciones: {str(e)}")
        return jsonify({"error": "Ocurrió un error interno en el servidor"}), 500


@api_autorizaciones_controller.route("/authorizations/<int:request_id>", methods=["GET"])
def detalle_autorizacion(request_id: int):
    """Obtiene el detalle de un pedido con cantidades pedidas y autorizadas por separado."""
    try:
        detalle = autorizaciones_service.obtener_detalle_pedido_autorizacion(request_id)
        return jsonify(detalle), 200
    except RecursoNoEncontradoError as e:
        current_app.logger.warning(f"Pedido no encontrado ({request_id}): {str(e)}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error interno al obtener detalle del pedido {request_id}: {str(e)}")
        return jsonify({"error": "Ocurrió un error interno en el servidor"}), 500


@api_autorizaciones_controller.route("/authorizations/<int:request_id>", methods=["PUT"])
def autorizar_pedido(request_id: int):
    """Autoriza nominadamente las solicitudes de un pedido"""

    data = request.get_json(silent=True) or {}
    items = data.get("solicitudes", [])
    ultima_modificacion = data.get("ultima_modificacion")
    id_evaluador = obtener_id_usuario_autenticado(data)

    try:
        pedido_actualizado = autorizaciones_service.autorizar_pedido(
            request_id, items, id_evaluador, ultima_modificacion
        )
        return jsonify(pedido_actualizado), 200
    except RecursoNoEncontradoError as e:
        current_app.logger.warning(f"Recurso no encontrado al autorizar pedido {request_id}: {str(e)}")
        return jsonify({"error": str(e)}), 404
    except ConflictoEstadoError as e:
        current_app.logger.warning(f"Conflicto de estado al autorizar pedido {request_id}: {str(e)}")
        return jsonify({"error": str(e)}), 409
    except ValueError as e:
        current_app.logger.warning(f"Datos inválidos al autorizar pedido {request_id}: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error inesperado al autorizar pedido {request_id}: {str(e)}")
        return jsonify({"error": "Ocurrió un error interno en el servidor"}), 500


@api_autorizaciones_controller.route("/authorizations/<int:request_id>/reject", methods=["POST"])
def rechazar_pedido(request_id: int):
    """Rechaza completamente un pedido"""

    data = request.get_json(silent=True) or {}
    id_evaluador = obtener_id_usuario_autenticado(data)
    motivo = data.get("motivo")

    try:
        pedido_rechazado = autorizaciones_service.rechazar_pedido(
            request_id, id_evaluador, motivo
        )
        return jsonify(pedido_rechazado), 200
    except RecursoNoEncontradoError as e:
        current_app.logger.warning(f"Pedido no encontrado al rechazar {request_id}: {str(e)}")
        return jsonify({"error": str(e)}), 404
    except ConflictoEstadoError as e:
        current_app.logger.warning(f"Conflicto al rechazar pedido {request_id}: {str(e)}")
        return jsonify({"error": str(e)}), 409
    except ValueError as e:
        current_app.logger.warning(f"Datos inválidos al rechazar pedido {request_id}: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error inesperado al rechazar pedido {request_id}: {str(e)}")
        return jsonify({"error": "Ocurrió un error interno en el servidor"}), 500


# <------ Endpoints de Comidas Autorizadas ------>

@api_autorizaciones_controller.route("/authorized-meals", methods=["GET"])
def listar_comidas_autorizadas():
    """Consulta comidas autorizadas por fecha, DNI, nombre/apellido, sector o tipo de comida"""

    filtros = {
        "fecha": request.args.get("fecha"),
        "dni": request.args.get("dni"),
        "nya": request.args.get("nya"),
        "sector": request.args.get("sector", type=int),
        "tipo_comida": request.args.get("tipo_comida", type=int),
    }
    try:
        resultado = autorizaciones_service.consultar_comidas_autorizadas(filtros)
        return jsonify(resultado), 200
    except ValueError as e:
        current_app.logger.warning(f"Filtros insuficientes o inválidos en authorized-meals: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error interno en authorized-meals: {str(e)}")
        return jsonify({"error": "Ocurrió un error interno en el servidor"}), 500


@api_autorizaciones_controller.route("/authorized-meals/<int:person_id>", methods=["GET"])
def comidas_autorizadas_por_persona(person_id: int):
    """Consulta las comidas autorizadas para una persona en una fecha"""

    fecha_str = request.args.get("fecha")

    try:
        resultado = autorizaciones_service.consultar_comidas_autorizadas_persona(
            person_id, fecha_str
        )
        return jsonify(resultado), 200
    except ValueError as e:
        current_app.logger.warning(f"Fecha inválida en authorized-meals por persona: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except RecursoNoEncontradoError as e:
        current_app.logger.warning(f"Persona no encontrada ({person_id}): {str(e)}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error interno en authorized-meals por persona: {str(e)}")
        return jsonify({"error": "Ocurrió un error interno en el servidor"}), 500


# <------ Endpoints de Entregas ------>

@api_autorizaciones_controller.route("/deliveries", methods=["POST"])
def registrar_entrega():
    """Registra la entrega física de una o varias comidas con responsable del retiro"""

    data = request.get_json(silent=True) or {}
    id_user = obtener_id_usuario_autenticado(data)
    id_personal_retira = data.get("id_personal")
    tercero = data.get("tercero")

    ids_solicitudes = data.get("ids_solicitudes")
    if not ids_solicitudes and data.get("id_solicitud") is not None:
        ids_solicitudes = [data.get("id_solicitud")]

    try:
        entregas = autorizaciones_service.registrar_entrega_comedor(
            id_user, ids_solicitudes, id_personal_retira, tercero
        )
        return jsonify({
            "mensaje": "Entrega registrada con éxito",
            "entregas": [
                {
                    "idEntrega": e.idEntrega,
                    "idSolicitud": e.idSolicitud,
                    "idPersonalResponsable": e.idPersonal,
                    "idUserOperador": e.idUser,
                    "fecha_hora": e.fecha_hora.isoformat(),
                }
                for e in entregas
            ],
        }), 201
    except ConflictoEstadoError as e:
        current_app.logger.warning(f"Entrega duplicada o conflicto: {str(e)}")
        return jsonify({"error": str(e)}), 409
    except ValueError as e:
        current_app.logger.warning(f"Validación fallida al registrar entrega: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error interno al registrar entrega: {str(e)}")
        return jsonify({"error": "Ocurrió un error interno en el servidor"}), 500


@api_autorizaciones_controller.route("/deliveries", methods=["GET"])
def listar_entregas():
    """Lista las entregas realizadas filtrando por fecha, sector o tipo de comida"""

    filtros = {
        "fecha": request.args.get("fecha"),
        "sector": request.args.get("sector", type=int),
        "tipo_comida": request.args.get("tipo_comida", type=int),
    }

    try:
        filas = autorizaciones_service.listar_entregas_service(filtros)
        resultado = [
            {
                "idEntrega": entrega.idEntrega,
                "fecha_hora": entrega.fecha_hora.isoformat(),
                "idUser": entrega.idUser,
                "idPersonalResponsable": entrega.idPersonal,
                "idSolicitud": solicitud.idSolicitud,
                "idPersonaComensal": solicitud.idPersonal,
                "idTipoComida": solicitud.idTipoComida,
                "idTipoMenu": solicitud.idTipoMenu,
                "idSector": pedido.idSector,
            }
            for entrega, solicitud, pedido in filas
        ]
        return jsonify(resultado), 200
    except ValueError as e:
        current_app.logger.warning(f"Filtro de fecha inválido al listar entregas: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error interno al listar entregas: {str(e)}")
        return jsonify({"error": "Ocurrió un error interno en el servidor"}), 500


@api_autorizaciones_controller.route("/deliveries/<int:delivery_id>", methods=["GET"])
def detalle_entrega(delivery_id: int):
    """Obtiene el detalle de una entrega específica"""

    try:
        entrega = autorizaciones_service.obtener_detalle_entrega_service(delivery_id)
        return jsonify({
            "idEntrega": entrega.idEntrega,
            "fecha_hora": entrega.fecha_hora.isoformat(),
            "idUser": entrega.idUser,
            "idSolicitud": entrega.idSolicitud,
            "idPersonalResponsable": entrega.idPersonal,
        }), 200
    except RecursoNoEncontradoError as e:
        current_app.logger.warning(f"Entrega no encontrada ({delivery_id}): {str(e)}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error interno al obtener entrega {delivery_id}: {str(e)}")
        return jsonify({"error": "Ocurrió un error interno en el servidor"}), 500


# <------ Endpoints de Resumenes ------>

@api_autorizaciones_controller.route("/deliveries/summary", methods=["GET"])
def resumen_entregas():
    """Obtiene el resumen de entregas de una fecha o tipo de comida (autorizados/entregados)"""

    filtros = {
        "fecha": request.args.get("fecha"),
        "sector": request.args.get("sector", type=int),
        "tipo_comida": request.args.get("tipo_comida", type=int),
    }

    try:
        resultado = autorizaciones_service.obtener_resumen_entregas_service(filtros)
        return jsonify(resultado), 200
    except ValueError as e:
        current_app.logger.warning(f"Error de validación en resumen de entregas: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error al obtener resumen de entregas: {str(e)}")
        return jsonify({"error": str(e)}), 400


@api_autorizaciones_controller.route("/summaries/authorizations", methods=["GET"])
def resumen_authorizations():
    """Obtiene el resumen de autorizaciones (pedidos vs autorizados)"""

    filtros = {
        "fecha_desde": request.args.get("fecha_desde"),
        "fecha_hasta": request.args.get("fecha_hasta"),
        "sector": request.args.get("sector", type=int),
        "tipo_comida": request.args.get("tipo_comida", type=int),
        "tipo_menu": request.args.get("tipo_menu", type=int),
        "condicion": request.args.get("condicion"),
    }
    try:
        resultado = autorizaciones_service.resumen_autorizaciones_service(filtros)
        return jsonify(resultado), 200
    except ValueError as e:
        current_app.logger.warning(f"Error de validación en resumen de autorizaciones: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error al obtener resumen de autorizaciones: {str(e)}")
        return jsonify({"error": str(e)}), 400