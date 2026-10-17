"""Validaciones de los filtros de búsqueda, ordenamiento y paginación de usuarios."""

ORDENAMIENTOS_PERMITIDOS = {"fecha", "apellido_nombre", "email"}
SENTIDOS_PERMITIDOS = {"asc", "desc"}
ESTADOS_PERMITIDOS = {"", "1", "0"}

ORDENAMIENTO_DEFAULT = "fecha"
SENTIDO_DEFAULT = "asc"
PAGINA_DEFAULT = 1
LONGITUD_MAXIMA_BUSQUEDA = 100
LONGITUD_MAXIMA_DNI = 15


def validar_filtros_listado(datos: dict[str, str]) -> tuple[dict, dict]:
    """Normaliza los filtros combinables y devuelve los errores por campo.

    Args:
        datos: Parámetros recibidos desde la solicitud web (request.args).

    Returns:
        Una tupla con los filtros normalizados y los errores por campo.
    """
    errores = {}

    email = _validar_texto(
        datos.get("email", ""), "email", "El correo electrónico", errores
    )
    nombre_apellido = _validar_texto(
        datos.get("nombre_apellido", ""),
        "nombre_apellido",
        "El nombre o apellido",
        errores,
    )
    dni = _validar_dni(datos.get("dni", ""), errores)

    activo = datos.get("activo", "").strip()
    if activo not in ESTADOS_PERMITIDOS:
        errores["activo"] = "El estado seleccionado no es válido."
        activo = ""

    orden = datos.get("orden", ORDENAMIENTO_DEFAULT).strip()
    if orden not in ORDENAMIENTOS_PERMITIDOS:
        errores["orden"] = "El criterio de ordenamiento no es válido."
        orden = ORDENAMIENTO_DEFAULT

    sentido = datos.get("sentido", SENTIDO_DEFAULT).strip().lower()
    if sentido not in SENTIDOS_PERMITIDOS:
        errores["sentido"] = "El sentido del ordenamiento no es válido."
        sentido = SENTIDO_DEFAULT

    rol_id = _validar_id_opcional(
        datos.get("rol_id", ""), "rol_id", "rol", errores
    )
    sector_id = _validar_id_opcional(
        datos.get("sector_id", ""), "sector_id", "sector", errores
    )
    pagina = _validar_pagina(datos.get("pagina", str(PAGINA_DEFAULT)), errores)

    filtros = {
        "email": email,
        "nombre_apellido": nombre_apellido,
        "dni": dni,
        "activo": activo,
        "rol_id": rol_id,
        "sector_id": sector_id,
        "orden": orden,
        "sentido": sentido,
        "pagina": pagina,
    }
    
    return filtros, errores


def _validar_texto(
    valor: str, clave: str, etiqueta: str, errores: dict
) -> str:
    """Limpia un filtro de texto y registra error si supera el máximo."""
    limpio = valor.strip()
    resultado = limpio
    
    if len(limpio) > LONGITUD_MAXIMA_BUSQUEDA:
        errores[clave] = (
            f"{etiqueta} no puede superar los "
            f"{LONGITUD_MAXIMA_BUSQUEDA} caracteres."
        )
        resultado = ""
        
    return resultado


def _validar_dni(valor: str, errores: dict) -> str:
    """Valida que el DNI de filtro contenga solo dígitos hasta el máximo."""
    limpio = valor.strip()
    resultado = limpio
    
    if limpio and (
        not limpio.isdecimal() or len(limpio) > LONGITUD_MAXIMA_DNI
    ):
        errores["dni"] = (
            "El DNI debe contener solo números "
            f"(máximo {LONGITUD_MAXIMA_DNI} dígitos)."
        )
        resultado = ""
        
    return resultado


def _validar_id_opcional(
    valor: str, clave: str, nombre: str, errores: dict
) -> int | None:
    """Valida un identificador numérico positivo opcional."""
    limpio = valor.strip()
    identificador = None
    
    if not limpio:
        identificador = None
    elif limpio.isdecimal() and int(limpio) > 0:
        identificador = int(limpio)
    else:
        errores[clave] = f"El identificador de {nombre} debe ser positivo."
        identificador = None
        
    return identificador


def _validar_pagina(valor: str, errores: dict) -> int:
    """Valida el número de página o retorna la página por defecto."""
    limpio = valor.strip()
    numero = PAGINA_DEFAULT
    
    if limpio.isdecimal() and int(limpio) > 0:
        numero = int(limpio)
    else:
        errores["pagina"] = "El número de página debe ser un entero positivo."
        numero = PAGINA_DEFAULT
        
    return numero