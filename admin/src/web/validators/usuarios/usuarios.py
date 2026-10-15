
"""Validaciones de los datos y filtros de usuarios."""

ORDENAMIENTOS_PERMITIDOS = {"fecha", "apellido_nombre", "email"}
SENTIDOS_PERMITIDOS = {"asc", "desc"}
ESTADOS_PERMITIDOS = {"", "1", "0"}

ORDENAMIENTO_DEFAULT = "fecha"
SENTIDO_DEFAULT = "asc"
PAGINA_DEFAULT = 1
LONGITUD_MAXIMA_BUSQUEDA = 100


def validate_user_data(
    email: str,
    alias: str,
    password: str,
    rol_nombre: str,
) -> bool:
    """Comprueba que los datos obligatorios del usuario sean válidos."""
    email_limpio = email.strip()
    alias_limpio = alias.strip()
    password_limpia = password.strip()
    rol_limpio = rol_nombre.strip()

    datos_validos = all(
        (
            email_limpio,
            "@" in email_limpio,
            alias_limpio,
            password_limpia,
            rol_limpio,
        )
    )

    return datos_validos


def validate_alta_conjunta_data(datos: dict[str, str]) -> list[str]:
    """Valida los campos requeridos para el alta conjunta de Personal y Usuario."""
    errores = []

    if not datos.get("dni", "").strip().isdigit():
        errores.append("El DNI es obligatorio y debe contener solo números.")

    if not datos.get("nombre", "").strip():
        errores.append("El nombre es obligatorio.")

    if not datos.get("apellido", "").strip():
        errores.append("El apellido es obligatorio.")

    if not datos.get("idTipoPersonal", "").isdigit():
        errores.append("Debe seleccionar un tipo de personal.")

    if not datos.get("idTipoMenu", "").isdigit():
        errores.append("Debe seleccionar un tipo de menú.")

    usuario_valido = validate_user_data(
        datos.get("email", ""),
        datos.get("alias", ""),
        datos.get("password", ""),
        datos.get("rol_nombre", ""),
    )

    if not usuario_valido:
        errores.append(
            "Completá correctamente los datos obligatorios del usuario."
        )

    return errores


def validar_filtros_listado(
    datos: dict[str, str],
) -> tuple[dict, dict]:
    """Normaliza filtros y devuelve los errores asociados a cada campo.

    Args:
        datos: Parámetros recibidos desde la solicitud web.

    Returns:
        Una tupla con los filtros normalizados y los errores por campo.
    """
    errores = {}

    busqueda = datos.get("buscar", "").strip()
    activo = datos.get("activo", "").strip()
    orden = datos.get("orden", ORDENAMIENTO_DEFAULT).strip()
    sentido = datos.get("sentido", SENTIDO_DEFAULT).strip().lower()

    if len(busqueda) > LONGITUD_MAXIMA_BUSQUEDA:
        errores["buscar"] = (
            f"La búsqueda no puede superar los "
            f"{LONGITUD_MAXIMA_BUSQUEDA} caracteres."
        )

    if activo not in ESTADOS_PERMITIDOS:
        errores["activo"] = "El estado seleccionado no es válido."
        activo = ""

    if orden not in ORDENAMIENTOS_PERMITIDOS:
        errores["orden"] = "El criterio de ordenamiento no es válido."
        orden = ORDENAMIENTO_DEFAULT

    if sentido not in SENTIDOS_PERMITIDOS:
        errores["sentido"] = "El sentido del ordenamiento no es válido."
        sentido = SENTIDO_DEFAULT

    rol_id, error_rol = _validar_identificador_opcional(
        datos.get("rol_id", ""),
        "rol",
    )
    if error_rol:
        errores["rol_id"] = error_rol

    sector_id, error_sector = _validar_identificador_opcional(
        datos.get("sector_id", ""),
        "sector",
    )
    if error_sector:
        errores["sector_id"] = error_sector

    pagina, error_pagina = _validar_entero_positivo(
        datos.get("pagina", str(PAGINA_DEFAULT)),
        "El número de página",
    )
    if error_pagina:
        errores["pagina"] = error_pagina

    filtros = {
        "buscar": busqueda,
        "activo": activo,
        "rol_id": rol_id,
        "sector_id": sector_id,
        "orden": orden,
        "sentido": sentido,
        "pagina": pagina,
    }

    return filtros, errores


def _validar_identificador_opcional(
    valor: str,
    nombre: str,
) -> tuple[int | None, str | None]:
    """Valida un identificador opcional de rol o sector.

    Args:
        valor: Identificador recibido como texto.
        nombre: Tipo de identificador.

    Returns:
        El identificador válido o None y un mensaje de error opcional.
    """
    valor_limpio = valor.strip()
    identificador = None
    error = None

    if valor_limpio:
        if valor_limpio.isdecimal() and int(valor_limpio) > 0:
            identificador = int(valor_limpio)
        else:
            error = f"El identificador de {nombre} debe ser positivo."

    return identificador, error


def _validar_entero_positivo(
    valor: str,
    nombre: str,
) -> tuple[int, str | None]:
    """Valida un entero positivo y devuelve un valor seguro ante errores.

    Args:
        valor: Valor textual recibido.
        nombre: Nombre del dato para el mensaje de error.

    Returns:
        El entero validado o la página predeterminada y un error opcional.
    """
    valor_limpio = valor.strip()
    numero = PAGINA_DEFAULT
    error = None

    if valor_limpio.isdecimal() and int(valor_limpio) > 0:
        numero = int(valor_limpio)
    else:
        error = f"{nombre} debe ser un entero positivo."

    return numero, error
