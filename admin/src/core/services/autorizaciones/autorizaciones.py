from src.core.repositories.autorizaciones import solicitudes as solicitudes
from src.core.repositories.autorizaciones import entregas as entregas

# Solicitudes
def obtener_solicitudes_pendientes():
    """Obtiene las solicitudes confirmadas listas para revisar"""
    return solicitudes.get_solicitudes_pendientes()

def actualizar_autorizacion(idSolicitud, nuevo_estado, id_evaluador):
    """Valida que el estado recibido sea permitido antes de actualizar"""
    estados_validos = ["autorizado", "rechazado"]
    
    # Si el estado del parametro no es uno de los validos, levanto ValueError
    if nuevo_estado not in estados_validos:
        raise ValueError("El estado de autorización no es válido.")
        
    return solicitudes.actualizar_estado_autorizacion(idSolicitud, nuevo_estado, id_evaluador)


# Entregas
def registrar_entrega_comedor(id_user, id_solicitud, id_personal):
    """Evita entregas duplicadas para una misma solicitud"""
    
    # Si ya fue entregada, levanto ValueError
    if entregas.verificar_entrega_existente(id_solicitud):
        raise ValueError("Esta comida ya fue entregada anteriormente.")
    
    # Si no fue entregada, la registro en la BD
    return entregas.registrar_entrega(id_user, id_solicitud, id_personal)