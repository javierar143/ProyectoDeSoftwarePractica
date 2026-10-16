"""Módulo de validación de entradas HTTP para Pedidos."""

from datetime import date
from typing import Any

from src.core.models.enums import EstadoPedido, Periodicidad


def _validar_diccionario_comidas(
    comidas: Any, mensaje_vacio: str
) -> tuple[bool, dict[int, list[int]] | str]:
    """Valida que 'comidas' sea un diccionario no vacío de {id_tipo_comida: [id_personal, ...]}."""
    if not isinstance(comidas, dict) or not comidas or not any(comidas.values()):
        return False, mensaje_vacio

    comidas_limpias: dict[int, list[int]] = {}
    for k, lista_ids in comidas.items():
        if isinstance(k, bool) or not isinstance(lista_ids, list):
            return (
                False,
                "El detalle de cada comida debe ser una lista de IDs de personal.",
            )
        try:
            id_comida = int(k)
            if id_comida <= 0:
                return (
                    False,
                    "El identificador de tipo de comida debe ser mayor a cero.",
                )

            ids_personal: list[int] = []
            for pid in lista_ids:
                if isinstance(pid, bool):
                    return (
                        False,
                        "Los identificadores de personal deben ser números enteros.",
                    )
                id_p = int(pid)
                if id_p <= 0:
                    return (
                        False,
                        "Los identificadores de personal deben ser mayores a cero.",
                    )
                ids_personal.append(id_p)

            if ids_personal:
                comidas_limpias[id_comida] = ids_personal
        except (ValueError, TypeError):
            return (
                False,
                "Los identificadores de comida y personal deben ser números enteros.",
            )

    if not comidas_limpias:
        return False, mensaje_vacio

    return True, comidas_limpias


def validar_creacion_pedido(
    data: dict[str, Any] | None,
) -> tuple[bool, dict[str, Any] | str]:
    """Valida los datos HTTP recibidos en POST /api/requests."""
    if not data or not isinstance(data, dict):
        return False, "Faltan datos obligatorios"

    campos_requeridos = ("fecha_desde", "periodicidad", "comidas")
    if not all(k in data and data[k] is not None for k in campos_requeridos):
        return False, "Faltan datos obligatorios"

    try:
        fecha_desde = date.fromisoformat(str(data["fecha_desde"]))
    except (ValueError, TypeError):
        return False, "Formato de fecha inválido. Use YYYY-MM-DD"

    fecha_hasta: date | None = None
    if data.get("fecha_hasta") is not None:
        try:
            fecha_hasta = date.fromisoformat(str(data["fecha_hasta"]))
        except (ValueError, TypeError):
            return False, "Formato de fecha inválido. Use YYYY-MM-DD"
        if fecha_hasta < fecha_desde:
            return (
                False,
                "La fecha hasta no puede ser anterior a la fecha desde.",
            )

    periodicidad_str = str(data["periodicidad"]).strip().lower()
    try:
        Periodicidad(periodicidad_str)
    except ValueError:
        return False, "La periodicidad indicada no es válida."

    comidas_ok, comidas_res = _validar_diccionario_comidas(
        data["comidas"],
        "El pedido debe incluir al menos una solicitud de comida.",
    )
    if not comidas_ok:
        return False, comidas_res

    return True, {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "periodicidad": periodicidad_str,
        "comidas": comidas_res,
    }


def validar_actualizacion_pedido(
    data: dict[str, Any] | None,
) -> tuple[bool, dict[str, Any] | str]:
    """
    Valida los datos HTTP recibidos en PUT /api/requests/<id>.
    Soporta tanto 'comidas' como 'fecha_desde', 'fecha_hasta' y 'periodicidad'.
    """
    if not data or not isinstance(data, dict) or "comidas" not in data:
        return False, "Faltan datos obligatorios ('comidas')"

    comidas_ok, comidas_res = _validar_diccionario_comidas(
        data["comidas"],
        "El pedido actualizado debe incluir al menos una solicitud.",
    )
    if not comidas_ok:
        return False, comidas_res

    fecha_desde: date | None = None
    if data.get("fecha_desde") is not None:
        try:
            fecha_desde = date.fromisoformat(str(data["fecha_desde"]))
        except (ValueError, TypeError):
            return False, "Formato de fecha inválido. Use YYYY-MM-DD"

    fecha_hasta: date | None = None
    if data.get("fecha_hasta") is not None:
        try:
            fecha_hasta = date.fromisoformat(str(data["fecha_hasta"]))
        except (ValueError, TypeError):
            return False, "Formato de fecha inválido. Use YYYY-MM-DD"
        if fecha_desde and fecha_hasta < fecha_desde:
            return (
                False,
                "La fecha hasta no puede ser anterior a la fecha desde.",
            )

    periodicidad_str: str | None = None
    if data.get("periodicidad") is not None:
        periodicidad_str = str(data["periodicidad"]).strip().lower()
        try:
            Periodicidad(periodicidad_str)
        except ValueError:
            return False, "La periodicidad indicada no es válida."

    return True, {
        "comidas": comidas_res,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "periodicidad": periodicidad_str,
    }


def validar_filtros_pedidos(
    args: dict[str, Any],
) -> tuple[bool, dict[str, Any] | str]:
    """Valida los parámetros query de GET /api/requests."""
    fecha_desde_str = args.get("fecha_desde")
    fecha_hasta_str = args.get("fecha_hasta")
    estado_str = args.get("estado")
    comida_raw = args.get("tipo_comida")
    menu_raw = args.get("tipo_menu")
    page_raw = args.get("page", 1)

    try:
        fecha_desde = (
            date.fromisoformat(fecha_desde_str) if fecha_desde_str else None
        )
        fecha_hasta = (
            date.fromisoformat(fecha_hasta_str) if fecha_hasta_str else None
        )
    except ValueError:
        return False, "Formato de fecha inválido. Use YYYY-MM-DD"

    if fecha_desde and fecha_hasta and fecha_hasta < fecha_desde:
        return (
            False,
            "La fecha hasta no puede ser anterior a la fecha desde.",
        )

    estado_limpio: str | None = None
    if estado_str not in (None, ""):
        estado_limpio = str(estado_str).strip().lower()
        try:
            EstadoPedido(estado_limpio)
        except ValueError:
            return False, "El filtro de estado no es válido."

    id_tipo_comida: int | None = None
    if comida_raw not in (None, ""):
        try:
            id_tipo_comida = int(comida_raw)
            if id_tipo_comida <= 0:
                return False, "El filtro 'tipo_comida' debe ser mayor a cero."
        except (ValueError, TypeError):
            return False, "El filtro 'tipo_comida' debe ser un número entero."

    id_tipo_menu: int | None = None
    if menu_raw not in (None, ""):
        try:
            id_tipo_menu = int(menu_raw)
            if id_tipo_menu <= 0:
                return False, "El filtro 'tipo_menu' debe ser mayor a cero."
        except (ValueError, TypeError):
            return False, "El filtro 'tipo_menu' debe ser un número entero."

    try:
        page = int(page_raw)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        return False, "El parámetro 'page' debe ser un número entero."

    return True, {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "estado_str": estado_limpio,
        "id_tipo_comida": id_tipo_comida,
        "id_tipo_menu": id_tipo_menu,
        "page": page,
    }


def validar_filtros_resumen_pedidos(
    args: dict[str, Any],
) -> tuple[bool, dict[str, Any] | str]:
    """Valida los query params de GET /api/summaries/requests."""
    fecha_desde_str = args.get("fecha_desde")
    fecha_hasta_str = args.get("fecha_hasta")
    sector_raw = args.get("sector")
    comida_raw = args.get("tipo_comida")
    menu_raw = args.get("tipo_menu")
    agrupamiento_raw = str(args.get("agrupamiento", "sector")).strip().lower()

    try:
        fecha_desde = (
            date.fromisoformat(fecha_desde_str) if fecha_desde_str else None
        )
        fecha_hasta = (
            date.fromisoformat(fecha_hasta_str) if fecha_hasta_str else None
        )
    except ValueError:
        return False, "Formato de fecha inválido. Use YYYY-MM-DD"

    if fecha_desde and fecha_hasta and fecha_hasta < fecha_desde:
        return (
            False,
            "La fecha hasta no puede ser anterior a la fecha desde.",
        )

    id_sector: int | None = None
    if sector_raw not in (None, ""):
        try:
            id_sector = int(sector_raw)
            if id_sector <= 0:
                return False, "El filtro 'sector' debe ser mayor a cero."
        except (ValueError, TypeError):
            return False, "El filtro 'sector' debe ser un número entero."

    id_tipo_comida: int | None = None
    if comida_raw not in (None, ""):
        try:
            id_tipo_comida = int(comida_raw)
            if id_tipo_comida <= 0:
                return False, "El filtro 'tipo_comida' debe ser mayor a cero."
        except (ValueError, TypeError):
            return False, "El filtro 'tipo_comida' debe ser un número entero."

    id_tipo_menu: int | None = None
    if menu_raw not in (None, ""):
        try:
            id_tipo_menu = int(menu_raw)
            if id_tipo_menu <= 0:
                return False, "El filtro 'tipo_menu' debe ser mayor a cero."
        except (ValueError, TypeError):
            return False, "El filtro 'tipo_menu' debe ser un número entero."

    agrupamientos_validos = (
        "dia",
        "día",
        "semana",
        "mes",
        "sector",
        "comida",
        "tipo_menu",
    )
    if agrupamiento_raw not in agrupamientos_validos:
        return (
            False,
            "El parámetro 'agrupamiento' debe ser: dia, semana, mes, sector, comida o tipo_menu.",
        )

    if agrupamiento_raw == "día":
        agrupamiento_raw = "dia"

    return True, {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "id_sector": id_sector,
        "id_tipo_comida": id_tipo_comida,
        "id_tipo_menu": id_tipo_menu,
        "agrupamiento": agrupamiento_raw,
    }