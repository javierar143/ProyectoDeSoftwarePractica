"""Servicios relacionados con la consulta de sectores."""

from src.core.models.Sector import Sector
from src.core.repositories.usuarios import sector


def get_all() -> list[Sector]:
    """Obtiene todos los sectores disponibles."""
    sectores = sector.get_all()

    return sectores