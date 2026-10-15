"""Validaciones del lado del servidor para el módulo de sectores."""

import re

NOMBRE_MIN = 2
NOMBRE_MAX = 100
DESCRIPCION_MAX = 500
NOMBRE_PATTERN = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .,()\-]+$")

ORDER_FIELDS = {"nombre", "fecha"}
DIRECTIONS = {"asc", "desc"}
ESTADOS = {"activo": True, "inactivo": False}


def validate_sector_data(nombre: str, descripcion: str) -> list[str]:
    """Valida los datos del formulario de sector y devuelve la lista de errores."""

    errores = []

    if not nombre:
        errores.append("El nombre es obligatorio.")
    elif not NOMBRE_MIN <= len(nombre) <= NOMBRE_MAX:
        errores.append(f"El nombre debe tener entre {NOMBRE_MIN} y {NOMBRE_MAX} caracteres.")
    elif not NOMBRE_PATTERN.match(nombre):
        errores.append("El nombre solo admite letras, números y espacios")

    if len(descripcion) > DESCRIPCION_MAX:
        errores.append(f"La descripción no puede superar los {DESCRIPCION_MAX} caracteres.")

    return errores


def validate_jefes_ids(raw_ids: list[str]) -> tuple[list[int], list[str]]:
    """Convierte los ids de jefes recibidos a enteros únicos, informando valores inválidos."""

    ids = []
    errores = []
    for raw in raw_ids:
        if raw.isdigit():
            ids.append(int(raw))
        else:
            errores.append("Se recibió un Jefe de Servicio inválido.")
    return list(dict.fromkeys(ids)), errores


def parse_search_params(args) -> dict:
    """Normaliza los parámetros de búsqueda; los valores inválidos toman el valor por defecto."""

    page = args.get("page", "1")
    order_by = args.get("order_by", "nombre")
    direction = args.get("direction", "asc")
    id_jefe = args.get("jefe", "")

    return {
        "nombre": args.get("nombre", "").strip()[:NOMBRE_MAX] or None,
        "activo": ESTADOS.get(args.get("estado", "")),
        "id_jefe": int(id_jefe) if id_jefe.isdigit() else None,
        "order_by": order_by if order_by in ORDER_FIELDS else "nombre",
        "direction": direction if direction in DIRECTIONS else "asc",
        "page": int(page) if page.isdigit() and int(page) > 0 else 1,
    }