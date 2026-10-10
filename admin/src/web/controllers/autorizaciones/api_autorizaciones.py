from flask import Blueprint, jsonify, request
from src.core.services.autorizaciones import autorizaciones as autorizaciones_service

api_autorizaciones_controller = Blueprint(
    "api_autorizaciones",
    __name__,
    url_prefix="/api/authorizations", 
)

@api_autorizaciones_controller.route("/pending", methods=["GET"])
def listar_pendientes():
    """Obtiene las solicitudes confirmadas pendientes de autorizacion"""

    try:
        # Obtengo solicitudes pendientes
        solicitudes = autorizaciones_service.obtener_solicitudes_pendientes()
        # Las mapeo a JSON
        resultado = [
            {
                "idSolicitud": s.idSolicitud,
                "estadoAutorizacion": s.estadoAutorizacion.name if s.estadoAutorizacion else None,
            }
            for s in solicitudes
        ]
        return jsonify(resultado), 200
    # Si algo falla, levanto Exception con status 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_autorizaciones_controller.route("/<int:id_solicitud>", methods=["PUT"])
def actualizar_autorizacion(id_solicitud):
    """Actualiza la autorizacion de una solicitud"""
    
    # Agarro los datos del JSON
    data = request.get_json() or {}
    nuevo_estado = data.get("estado")
    id_evaluador = data.get("id_evaluador")

    try:
        # Hago que se actualice la solicitud en services
        solicitud_actualizada = autorizaciones_service.actualizar_autorizacion(
            id_solicitud, nuevo_estado, id_evaluador
        ) 
        # Si no existe devuelvo mensaje
        if not solicitud_actualizada:
            return jsonify({"error": "Solicitud no encontrada"}), 404
        # Actualizo y devuelvo mensaje con los datos nuevos
        return jsonify({
            "mensaje": "Autorización actualizada correctamente",
            "idSolicitud": solicitud_actualizada.idSolicitud,
            "estadoAutorizacion": solicitud_actualizada.estadoAutorizacion.name
        }), 200
    # Si hay un error de validacion, devuelvo status 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api_autorizaciones_controller.route("/deliveries", methods=["POST"])
def registrar_entrega():
    """Registra la entrega física en el comedor"""

    # Agarro los datos del JSON
    data = request.get_json() or {}
    id_user = data.get("id_user")
    id_solicitud = data.get("id_solicitud")
    id_personal = data.get("id_personal")

    try:
        # Intento registrar la entrega a partir de services
        entrega = autorizaciones_service.registrar_entrega_comedor(
            id_user, id_solicitud, id_personal
        )
        # Si el registro sale bien, devuelvo mensaje
        return jsonify({
            "mensaje": "Entrega registrada con éxito",
            "idEntrega": entrega.idEntrega
        }), 201
    # Si la entrega ya se entrego, levanto ValueError con status Conflict 409
    except ValueError as e:
        return jsonify({"error": str(e)}), 409