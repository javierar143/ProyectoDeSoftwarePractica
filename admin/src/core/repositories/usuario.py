from sqlalchemy import select

from src.core.database import db
from src.core.models.Usuario import Usuario


def get_by_email(email: str) -> Usuario | None:
    statement = select(Usuario).where(Usuario.email == email)

    return db.session.execute(statement).scalar_one_or_none()

def create(usuario: Usuario) -> Usuario:
    db.session.add(usuario)
    db.session.commit()
    return usuario

def get_by_id(user_id: int) -> Usuario | None:
    statement = select(Usuario).where(Usuario.id_user == user_id)
    usuario = db.session.execute(statement).scalar_one_or_none()
    return usuario