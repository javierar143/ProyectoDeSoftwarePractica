"""Validaciones de los datos de alta y edición de usuarios."""

def validate_user_data(
    email: str,
    alias: str,
    password: str,
    confirmar_password: str,
    rol_nombre: str,
) -> bool:
    """Comprueba que los datos obligatorios del usuario sean válidos."""
    email_limpio = email.strip()
    alias_limpio = alias.strip()
    rol_limpio = rol_nombre.strip()

    datos_validos = all(
        (
            email_limpio,
            "@" in email_limpio,
            alias_limpio,
            password.strip(),
            len(password) >= 8,
            password == confirmar_password,
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

    email = datos.get("email", "")
    alias = datos.get("alias", "")
    password = datos.get("password", "")
    confirmar_password = datos.get("confirmar_password", "")
    rol_nombre = datos.get("rol_nombre", "")

    if not email.strip() or "@" not in email.strip():
        errores.append(
            "El correo electrónico es obligatorio y debe ser válido."
        )

    if not alias.strip():
        errores.append("El alias es obligatorio.")

    if not password.strip():
        errores.append("La contraseña es obligatoria.")
    elif len(password) < 8:
        errores.append(
            "La contraseña debe tener al menos 8 caracteres."
        )

    if not confirmar_password.strip():
        errores.append("Debés confirmar la contraseña.")
    elif password != confirmar_password:
        errores.append("Las contraseñas no coinciden.")

    if not rol_nombre.strip():
        errores.append("Debe seleccionar un rol.")

    return errores


def validate_edit_user_data(
    email: str,
    alias: str,
    rol_id_texto: str,
    password: str = "",
    confirmar_password: str = "",
) -> list[str]:
    """Valida los campos requeridos para la edición de un usuario."""
    errores = []
    email_limpio = email.strip()
    alias_limpio = alias.strip()

    if not email_limpio or "@" not in email_limpio:
        errores.append(
            "El correo electrónico es obligatorio y debe ser válido."
        )

    if not alias_limpio:
        errores.append("El alias es obligatorio.")

    if not rol_id_texto.strip().isdigit():
        errores.append("Debe seleccionar un rol válido.")

    # La contraseña es opcional, pero si se completa alguno
    # de los dos campos, deben completarse ambos correctamente.
    if password or confirmar_password:
        if not password.strip():
            errores.append("Debés ingresar la nueva contraseña.")

        elif len(password) < 8:
            errores.append(
                "La contraseña debe tener al menos 8 caracteres."
            )

        if not confirmar_password:
            errores.append("Debés confirmar la nueva contraseña.")

        elif password != confirmar_password:
            errores.append("Las contraseñas no coinciden.")

    return errores