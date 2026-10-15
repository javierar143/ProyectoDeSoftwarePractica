"""Repositorio de consulta de sectores para el módulo de usuarios."""

from sqlalchemy import select

from src.core.database import db
from src.core.models.Sector import Sector


def get_all() -> list[Sector]:
    """Obtiene todos los sectores ordenados alfabéticamente por nombre."""
    statement = select(Sector).order_by(Sector.nombre.asc())
    return list(db.session.execute(statement).scalars().all())