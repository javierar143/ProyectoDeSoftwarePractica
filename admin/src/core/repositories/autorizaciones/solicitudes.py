from datetime import datetime
from sqlalchemy import select
from src.core.models.Solicitud import Solicitud
from src.core.database import db

def get_solicitudes_pendientes():
    """Obtiene todas las solicitudes pendientes (aquellas que estan confirmadas) """
    statement = select(Solicitud).where(Solicitud.estadoAutorizacion == "confirmado")
    return db.session.scalars(statement).all()


def get_solicitudes_aprobadas():
    """Obtiene todas las solicitudes aprobadas"""
    statement = select(Solicitud).where(Solicitud.estadoAutorizacion == "autorizado")
    return db.session.scalars(statement).all()

def actualizar_estado_autorizacion(idSolicitud, estado, id_evaluador):
    """Actualiza si la solicitud fue aprobada, no autorizada o rechazada"""
    solicitud = db.session.get(Solicitud, idSolicitud)

    if solicitud:
            solicitud.estadoAutorizacion = estado
            solicitud.idUserEvaluador = id_evaluador
            db.session.commit()
    return solicitud