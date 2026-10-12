
"""Repositorio de consultas de personal."""

from sqlalchemy import select

from src.core.database import db
from src.core.models.Personal import Personal


def get_by_dni(dni: str) -> Personal | None:
    """Obtiene una persona por DNI, o None si no existe."""
    statement = select(Personal).where(Personal.dni == dni)
    return db.session.execute(statement).scalar_one_or_none()
