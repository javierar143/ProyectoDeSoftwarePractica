from sqlalchemy import select
from src.core.models.Entrega import Entrega
from src.core.database import db

def verificar_entrega_existente(id_solicitud):
    """Verifica si una solicitud ya fue entregada para evitar entregas duplicadas"""
    statement = select(Entrega).where(Entrega.idSolicitud == id_solicitud)
    return db.session.scalars(statement).first() is not None

def registrar_entrega(id_user, id_solicitud, id_personal):
    """Registra de manera física la entrega de la vianda"""
    nueva_entrega = Entrega(
        idUser=id_user,
        idSolicitud=id_solicitud,
        idPersonal=id_personal
    )
    db.session.add(nueva_entrega)
    db.session.commit()
    return nueva_entrega