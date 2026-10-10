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
        solicitudes = autorizaciones_service.obtener_solicitudes_pendientes()
        resultado = [
            {
                "idSolicitud": s.idSolicitud,
                "estadoAutorizacion": s.estadoAutorizacion.name if s.estadoAutorizacion else None,
            }
            for s in solicitudes
        ]
        return jsonify(resultado), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_autorizaciones_controller.route("/<int:id_solicitud>", methods=["PUT"])
def actualizar_autorizacion(id_solicitud):
    """Actualiza la autorizacion de una solicitud"""
    data = request.get_json() or {}
    nuevo_estado = data.get("estado")
    id_evaluador = data.get("id_evaluador")

    try:
        solicitud_actualizada = autorizaciones_service.actualizar_autorizacion(
            id_solicitud, nuevo_estado, id_evaluador
        )
        if not solicitud_actualizada:
            return jsonify({"error": "Solicitud no encontrada"}), 404
            
        return jsonify({
            "mensaje": "Autorización actualizada correctamente",
            "idSolicitud": solicitud_actualizada.idSolicitud,
            "estadoAutorizacion": solicitud_actualizada.estadoAutorizacion.name # <-- ¡Agregamos .name!
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api_autorizaciones_controller.route("/deliveries", methods=["POST"])
def registrar_entrega():
    """Registra la entrega física en el comedor"""
    data = request.get_json() or {}
    id_user = data.get("id_user")
    id_solicitud = data.get("id_solicitud")
    id_personal = data.get("id_personal")

    try:
        entrega = autorizaciones_service.registrar_entrega_comedor(
            id_user, id_solicitud, id_personal
        )
        return jsonify({
            "mensaje": "Entrega registrada con éxito",
            "idEntrega": entrega.idEntrega
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 409