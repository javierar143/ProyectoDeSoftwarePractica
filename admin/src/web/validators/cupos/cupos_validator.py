from typing import Any

def validar_entrada_cupo(data: dict[str, Any] | None) -> tuple[bool, dict[str, Any] | str]:
    """Valida los datos HTTP para crear o modificar un cupo."""
    if not data or not isinstance(data, dict):
        return False, "Faltan datos obligatorios."

    campos_requeridos = ("idSector", "idTipoComida", "cantComensales")
    if not all(k in data for k in campos_requeridos):
        return False, "Faltan datos obligatorios (idSector, idTipoComida, cantComensales)."

    try:
        id_sector = int(data["idSector"])
        id_tipo_comida = int(data["idTipoComida"])
        cant_comensales = int(data["cantComensales"])
    except (ValueError, TypeError):
        return False, "Sector, tipo de comida y cantidad de comensales deben ser números enteros."

    if id_sector <= 0 or id_tipo_comida <= 0:
        return False, "El sector y el tipo de comida deben ser mayores a cero."

    if cant_comensales <= 0:
        return False, "La cantidad de comensales debe ser mayor a cero."

    return True, {
        "id_sector": id_sector,
        "id_tipo_comida": id_tipo_comida,
        "cant_comensales": cant_comensales,
    }