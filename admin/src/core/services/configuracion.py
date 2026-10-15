"""Servicios de aplicación para la configuración del sistema."""
from src.core.repositories import configuracion as repo_config

MIN_ELEMENTOS_POR_PAGINA = 1
MAX_ELEMENTOS_POR_PAGINA = 25
ELEMENTOS_POR_PAGINA_DEFAULT = 10


def obtener_configuracion():
    """Obtiene la configuración y corrige valores de paginación inválidos."""
    config = repo_config.obtener_configuracion()
    elementos = config.elementos_por_pagina

    if not isinstance(elementos, int) or isinstance(elementos, bool) or elementos < MIN_ELEMENTOS_POR_PAGINA:
        elementos = ELEMENTOS_POR_PAGINA_DEFAULT
    elif elementos > MAX_ELEMENTOS_POR_PAGINA:
        elementos = MAX_ELEMENTOS_POR_PAGINA

    if elementos != config.elementos_por_pagina:
        config = repo_config.actualizar_configuracion(
            elementos,
            config.modo_mantenimiento,
        )

    return config


def actualizar_configuracion(elementos: int, mantenimiento: bool):
    """Valida y persiste la configuración del sistema.

    Args:
        elementos: Cantidad de elementos por página, entre 1 y 25.
        mantenimiento: Estado del modo mantenimiento.

    Raises:
        ValueError: Si la cantidad no es un entero entre 1 y 25.
    """
    if (
        not isinstance(elementos, int)
        or isinstance(elementos, bool)
        or not MIN_ELEMENTOS_POR_PAGINA <= elementos <= MAX_ELEMENTOS_POR_PAGINA
    ):
        raise ValueError(
            "La cantidad de elementos por página debe estar entre 1 y 25."
        )
    return repo_config.actualizar_configuracion(elementos, mantenimiento)