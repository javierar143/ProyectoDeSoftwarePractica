"""Servicio para la búsqueda, filtrado y paginación de usuarios."""

import math

from src.core.repositories.usuarios import busqueda as repo_busqueda
from src.core.services import configuracion


def buscar_paginado(filtros: dict) -> dict:
    """Ejecuta la búsqueda paginada respetando los ajustes del sistema.

    Args:
        filtros: Diccionario de filtros previamente validados.

    Returns:
        Diccionario con los usuarios de la página y metadatos de paginación.
    """
    config = configuracion.obtener_configuracion()
    por_pagina = config.elementos_por_pagina

    usuarios, total = repo_busqueda.buscar_paginado(filtros, por_pagina)
    total_paginas = max(1, math.ceil(total / por_pagina))

    if filtros["pagina"] > total_paginas and total > 0:
        filtros["pagina"] = total_paginas
        usuarios, total = repo_busqueda.buscar_paginado(filtros, por_pagina)

    return {
        "usuarios": usuarios,
        "total_usuarios": total,
        "pagina_actual": filtros["pagina"],
        "total_paginas": total_paginas,
        "elementos_por_pagina": por_pagina,
        "tiene_anterior": filtros["pagina"] > 1,
        "tiene_siguiente": filtros["pagina"] < total_paginas,
    }