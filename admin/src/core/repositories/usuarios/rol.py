"""Repositorio para la persistencia y consulta de roles."""

from sqlalchemy import select

from src.core.database import db
from src.core.models.Rol import Rol


def get_by_name(nombre: str) -> Rol | None:
    """Obtiene un rol a partir de su nombre."""
    statement = select(Rol).where(Rol.nombre == nombre)
    rol = db.session.execute(statement).scalar_one_or_none()
    
    return rol