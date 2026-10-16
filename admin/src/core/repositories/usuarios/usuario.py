"""Repositorio para la persistencia y consulta de usuarios."""

from sqlalchemy import asc, desc, func, or_, select

from src.core.database import db
from src.core.models.Rol import Rol
from src.core.models.Usuario import Usuario
from src.core.models.Personal import Personal


def get_by_email(email: str) -> Usuario | None:
    """Obtiene un usuario a partir de su dirección de email."""
    statement = select(Usuario).where(Usuario.email == email)
    return db.session.execute(statement).scalar_one_or_none()


def get_by_personal_id(personal_id: int) -> Usuario | None:
    """Obtiene el usuario asociado a un identificador de Personal."""
    statement = select(Usuario).where(
        Usuario.idPersonal == personal_id
    )
    return db.session.execute(statement).scalar_one_or_none()


def create(usuario: Usuario) -> Usuario:
    """Persiste un usuario nuevo y revierte la operación si falla."""
    try:
        db.session.add(usuario)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return usuario


def get_by_id(user_id: int) -> Usuario | None:
    """Obtiene un usuario a partir de su identificador."""
    statement = select(Usuario).where(Usuario.id_user == user_id)
    return db.session.execute(statement).scalar_one_or_none()


def get_all() -> list[Usuario]:
    """Obtiene todos los usuarios registrados."""
    statement = select(Usuario)
    return list(db.session.execute(statement).scalars().all())


def update(usuario: Usuario) -> Usuario:
    """Persiste los cambios de un usuario y revierte si falla."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return usuario


def get_all_with_role() -> list[tuple[Usuario, str]]:
    """Obtiene todos los usuarios junto con el nombre de su rol."""
    statement = (
        select(Usuario, Rol.nombre)
        .join(Rol, Usuario.idRol == Rol.idRol)
    )
    return list(db.session.execute(statement).all())


