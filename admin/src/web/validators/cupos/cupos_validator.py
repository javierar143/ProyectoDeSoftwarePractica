"""Validadores de entrada HTTP para el módulo de Cupos."""

from typing import Any


def validar_entrada_cupo(
    data: dict[str, Any] | None,
) -> tuple[bool, dict[str, int] | str]:
    """Valida los datos HTTP para crear o modificar un cupo."""
    if not data or not isinstance(data, dict):
        return False, "Faltan datos obligatorios."

    campos_requeridos = ("idSector", "idTipoComida", "cantComensales")
    if not all(k in data and data[k] is not None for k in campos_requeridos):
        return (
            False,
            "Faltan datos obligatorios (idSector, idTipoComida, cantComensales).",
        )

    if any(isinstance(data[k], bool) for k in campos_requeridos):
        return (
            False,
            "Sector, tipo de comida y cantidad de comensales deben ser números enteros.",
        )

    try:
        id_sector = int(data["idSector"])
        id_tipo_comida = int(data["idTipoComida"])
        cant_comensales = int(data["cantComensales"])
    except (ValueError, TypeError):
        return (
            False,
            "Sector, tipo de comida y cantidad de comensales deben ser números enteros.",
        )

    if id_sector <= 0 or id_tipo_comida <= 0:
        return False, "El sector y el tipo de comida deben ser mayores a cero."

    if cant_comensales <= 0:
        return False, "La cantidad de comensales debe ser mayor a cero."

    return True, {
        "id_sector": id_sector,
        "id_tipo_comida": id_tipo_comida,
        "cant_comensales": cant_comensales,
    }


def validar_filtros_listado_cupos(
    args: dict[str, Any],
) -> tuple[bool, dict[str, Any] | str]:
    """Valida los parámetros query de búsqueda, ordenamiento y página de GET /api/quotas."""
    sector_raw = args.get("sector")
    comida_raw = args.get("tipo_comida")
    orden_raw = str(args.get("orden", "asc")).strip().lower()
    page_raw = args.get("page", 1)

    id_sector: int | None = None
    if sector_raw is not None and sector_raw != "":
        try:
            id_sector = int(sector_raw)
            if id_sector <= 0:
                return False, "El parámetro 'sector' debe ser un entero positivo."
        except (ValueError, TypeError):
            return False, "El parámetro 'sector' debe ser un número entero."

    id_tipo_comida: int | None = None
    if comida_raw is not None and comida_raw != "":
        try:
            id_tipo_comida = int(comida_raw)
            if id_tipo_comida <= 0:
                return (
                    False,
                    "El parámetro 'tipo_comida' debe ser un entero positivo.",
                )
        except (ValueError, TypeError):
            return False, "El parámetro 'tipo_comida' debe ser un número entero."

    if orden_raw not in ("asc", "desc"):
        return False, "El parámetro 'orden' solo admite 'asc' o 'desc'."

    try:
        page = int(page_raw)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        return False, "El parámetro 'page' debe ser un número entero."

    return True, {
        "id_sector": id_sector,
        "id_tipo_comida": id_tipo_comida,
        "orden": orden_raw,
        "page": page,
    }