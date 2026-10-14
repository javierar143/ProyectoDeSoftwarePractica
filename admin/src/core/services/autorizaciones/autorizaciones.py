from src.core.repositories.autorizaciones import solicitudes as repo_solicitudes
from src.core.repositories.autorizaciones import entregas as repo_entregas
from src.core.models.enums import EstadoAutorizacion

# <------ Solicitudes ------>
def obtener_solicitudes_pendientes():
    """Obtiene las solicitudes confirmadas listas para revisar"""

    return repo_solicitudes.get_solicitudes_pendientes()

def actualizar_autorizacion(idSolicitud, nuevo_estado_texto, id_evaluador):
    """Convierte el texto recibido a Enum y valida que sea correcto"""
    
    # Convierto texto a Enum
    try:
        estado_enum = EstadoAutorizacion[nuevo_estado_texto.upper()]
    except KeyError:
        raise ValueError(f"El estado '{nuevo_estado_texto}' no es un estado de autorización válido.")
    
    # Me fijo que el estado que converti este dentro de los permitidos
    estados_permitidos = [EstadoAutorizacion.AUTORIZADA, EstadoAutorizacion.NO_AUTORIZADA]
    if estado_enum not in estados_permitidos:
        raise ValueError("Solo se permite transicionar a Autorizado o Rechazado.")
        
    return repo_solicitudes.actualizar_estado_autorizacion(idSolicitud, estado_enum, id_evaluador)

# <------ Entregas ------>
def registrar_entrega_comedor(id_user, id_solicitud, id_personal):
    """Evita entregas duplicadas para una misma solicitud"""
    
    # Si ya fue entregada, levanto ValueError
    if repo_entregas.verificar_entrega_existente(id_solicitud):
        raise ValueError("Esta comida ya fue entregada anteriormente.")
    
    # Si no fue entregada, la registro en la BD
    return repo_entregas.registrar_entrega(id_user, id_solicitud, id_personal)