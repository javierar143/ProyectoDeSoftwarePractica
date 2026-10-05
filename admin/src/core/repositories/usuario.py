"""Repositorio para la persistencia y consulta de usuarios."""

from sqlalchemy import select

from src.core.database import db
from src.core.models.Usuario import Usuario


def get_by_email(email: str) -> Usuario | None:
    """Obtiene un usuario a partir de su dirección de email."""
    statement = select(Usuario).where(Usuario.email == email)
    usuario = db.session.execute(statement).scalar_one_or_none()

    return usuario


def create(usuario: Usuario) -> Usuario:
    """Persiste un nuevo usuario y devuelve la entidad creada."""
    db.session.add(usuario)
    db.session.commit()

    return usuario


def get_by_id(user_id: int) -> Usuario | None:
    """Obtiene un usuario a partir de su identificador."""
    statement = select(Usuario).where(Usuario.id_user == user_id)
    usuario = db.session.execute(statement).scalar_one_or_none()

    return usuario


def get_all() -> list[Usuario]:
    """Obtiene todos los usuarios registrados."""
    statement = select(Usuario)
    usuarios = db.session.execute(statement).scalars().all()

    return usuarios


def update(usuario: Usuario) -> Usuario:
    """Persiste los cambios realizados sobre un usuario."""
    db.session.commit()   #El usuario ya existe y está siendo gestionado por la sesión de SQLAlchemy.
                          # Después de modificar sus atributos, commit() persiste esos cambios.

    return usuario