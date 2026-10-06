"""Repositorio temporal para la consulta de personal."""

from src.core.seeds.personal_temporal import PERSONAL_TEMPORAL


def get_by_dni(dni: str) -> dict | None:
    """Obtiene una persona temporal a partir de su DNI."""
    persona_encontrada = None

    # TODO: reemplazar esta consulta temporal por la consulta
    # al modelo Personal cuando el módulo esté disponible.

    for persona in PERSONAL_TEMPORAL:
        if persona["dni"] == dni:
            persona_encontrada = persona
            break

    return persona_encontrada