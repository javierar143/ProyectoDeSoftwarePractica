from sqlalchemy import select
from src.core.models.Solicitud import Solicitud
from src.core.database import db
from src.core.models.enums import EstadoAutorizacion

def get_solicitudes_pendientes():
    """Obtiene todas las solicitudes pendientes"""

    statement = select(Solicitud).where(Solicitud.estadoAutorizacion == EstadoAutorizacion.PENDIENTE)
    return db.session.scalars(statement).all()

def get_solicitudes_aprobadas():
    """Obtiene todas las solicitudes aprobadas/autorizadas"""

    statement = select(Solicitud).where(Solicitud.estadoAutorizacion == EstadoAutorizacion.AUTORIZADA)
    return db.session.scalars(statement).all()

def actualizar_estado_autorizacion(idSolicitud, estado_enum, id_evaluador):
    """Actualiza el estado de autorizacion"""
    solicitud = db.session.get(Solicitud, idSolicitud)

    if solicitud:
        solicitud.estadoAutorizacion = estado_enum
        solicitud.idUserEvaluador = id_evaluador
        db.session.commit()
    return solicitud