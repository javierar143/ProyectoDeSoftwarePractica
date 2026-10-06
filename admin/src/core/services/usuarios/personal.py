"""Servicios relacionados con la consulta de personal."""

from src.core.repositories.usuarios import personal


def get_by_dni(dni: str) -> dict | None:
    """Obtiene una persona a partir de su DNI."""
    persona_encontrada = personal.get_by_dni(dni)
    return persona_encontrada