from datetime import date
from flask import Blueprint, jsonify, request, session
from src.core.services.autorizaciones import autorizaciones as autorizaciones_service
from src.core.services.autorizaciones.autorizaciones import (RecursoNoEncontradoError,ConflictoEstadoError,)
from src.core.repositories.autorizaciones import entregas as repo_entregas

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
        return jsonify({"error": str(e)}), 400


@api_autorizaciones_controller.route("/authorizations/<int:request_id>", methods=["GET"])
def detalle_autorizacion(request_id: int):
    """Obtiene el detalle de un pedido con cantidades pedidas y autorizadas por separado."""
    try:
        detalle = autorizaciones_service.obtener_detalle_pedido_autorizacion(request_id)
        return jsonify(detalle), 200
    except RecursoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@api_autorizaciones_controller.route("/authorizations/<int:request_id>", methods=["PUT"])
def autorizar_pedido(request_id: int):
    """Autoriza nominadamente las solicitudes de un pedido"""

    data = request.get_json() or {}
    items = data.get("solicitudes", [])
    id_evaluador = obtener_id_usuario_autenticado(data)

    try:
        pedido_actualizado = autorizaciones_service.autorizar_pedido(
            request_id, items, id_evaluador
        )
        return jsonify(pedido_actualizado), 200
    except RecursoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404
    except ConflictoEstadoError as e:
        return jsonify({"error": str(e)}), 409
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api_autorizaciones_controller.route("/authorizations/<int:request_id>/reject", methods=["POST"])
def rechazar_pedido(request_id: int):
    """Rechaza completamente un pedido"""

    data = request.get_json(silent=True) or {}
    id_evaluador = obtener_id_usuario_autenticado(data)

    try:
        pedido_rechazado = autorizaciones_service.rechazar_pedido(request_id, id_evaluador)
        return jsonify(pedido_rechazado), 200
    except RecursoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404
    except ConflictoEstadoError as e:
        return jsonify({"error": str(e)}), 409


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
        return jsonify({"error": str(e)}), 400


@api_autorizaciones_controller.route("/authorized-meals/<int:person_id>", methods=["GET"])
def comidas_autorizadas_por_persona(person_id: int):
    """Consulta las comidas autorizadas para una persona en una fecha"""

    fecha_str = request.args.get("fecha")
    try:
        fecha_consulta = date.fromisoformat(fecha_str) if fecha_str else date.today()
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}), 400

    try:
        resultado = autorizaciones_service.consultar_comidas_autorizadas_persona(
            person_id, fecha_consulta
        )
        return jsonify(resultado), 200
    except RecursoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404

# <------ Endpoints de Entregas ------>

@api_autorizaciones_controller.route("/deliveries", methods=["POST"])
def registrar_entrega():
    """Registra la entrega física de una o varias comidas con responsable del retiro"""

    data = request.get_json() or {}
    id_user = obtener_id_usuario_autenticado(data)
    id_personal_retira = data.get("id_personal")

    ids_solicitudes = data.get("ids_solicitudes")
    if not ids_solicitudes and data.get("id_solicitud") is not None:
        ids_solicitudes = [data.get("id_solicitud")]

    try:
        entregas = autorizaciones_service.registrar_entrega_comedor(
            id_user, ids_solicitudes, id_personal_retira
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
        return jsonify({"error": str(e)}), 409
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api_autorizaciones_controller.route("/deliveries", methods=["GET"])
def listar_entregas():
    """Lista las entregas realizadas filtrando por fecha, sector o tipo de comida"""

    fecha_str = request.args.get("fecha")
    id_sector = request.args.get("sector", type=int)
    id_tipo_comida = request.args.get("tipo_comida", type=int)

    fecha_filtro = None
    if fecha_str:
        try:
            fecha_filtro = date.fromisoformat(fecha_str)
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}), 400

    filas = repo_entregas.listar_entregas(fecha_filtro, id_sector, id_tipo_comida)
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


@api_autorizaciones_controller.route("/deliveries/<int:delivery_id>", methods=["GET"])
def detalle_entrega(delivery_id: int):
    """Obtiene el detalle de una entrega específica"""
    
    entrega = repo_entregas.get_entrega_by_id(delivery_id)
    if not entrega:
        return jsonify({"error": "Entrega no encontrada"}), 404

    return jsonify({
        "idEntrega": entrega.idEntrega,
        "fecha_hora": entrega.fecha_hora.isoformat(),
        "idUser": entrega.idUser,
        "idSolicitud": entrega.idSolicitud,
        "idPersonalResponsable": entrega.idPersonal,
    }), 200

# <------ Endpoints de Resumenes ------>

@api_autorizaciones_controller.route("/deliveries/summary", methods=["GET"])
def resumen_entregas():
    """Obtiene el resumen de entregas de una fecha o tipo de comida (autorizados/entregados)"""

    fecha_str = request.args.get("fecha")
    id_sector = request.args.get("sector", type=int)
    id_tipo_comida = request.args.get("tipo_comida", type=int)

    fecha_filtro = None
    if fecha_str:
        try:
            fecha_filtro = date.fromisoformat(fecha_str)
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}), 400

    filtros = {
        "fecha": fecha_filtro,
        "sector": id_sector,
        "tipo_comida": id_tipo_comida,
    }

    try:
        resultado = autorizaciones_service.obtener_resumen_entregas_service(filtros)
        return jsonify(resultado), 200
    except Exception as e:
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
    }
    try:
        resultado = autorizaciones_service.resumen_autorizaciones_service(filtros)
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_autorizaciones_controller.route("/summaries/deliveries", methods=["GET"])
def resumen_deliveries_general():
    """Obtiene el resumen general de entregas (autorizados vs entregados)"""

    filtros = {
        "fecha_desde": request.args.get("fecha_desde"),
        "fecha_hasta": request.args.get("fecha_hasta"),
        "sector": request.args.get("sector", type=int),
        "tipo_comida": request.args.get("tipo_comida", type=int),
        "tipo_menu": request.args.get("tipo_menu", type=int),
    }
    try:
        resultado = autorizaciones_service.resumen_entregas_generales_service(filtros)
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400