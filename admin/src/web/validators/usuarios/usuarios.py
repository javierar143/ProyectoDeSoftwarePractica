"""Validaciones de los datos de usuarios."""


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
    """Valida los campos requeridos para el alta simultánea de Personal y Usuario."""
    errores = []

    if not datos.get("dni", "").isdigit():
        errores.append("El DNI es obligatorio y debe contener solo números.")

    if not datos.get("nombre", ""):
        errores.append("El nombre es obligatorio.")

    if not datos.get("apellido", ""):
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
        errores.append("Completá correctamente los datos obligatorios del usuario.")

    return errores