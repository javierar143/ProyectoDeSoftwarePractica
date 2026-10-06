def validate_user_data(
    email: str,
    alias: str,
    password: str,
    rol_nombre: str,
    personal_id: str,
) -> bool:
    """Valida los datos obligatorios para crear un usuario."""
    datos_validos = all(
        [
            email.strip(),
            alias.strip(),
            password.strip(),
            rol_nombre.strip(),
            personal_id.strip(),
        ]
    )

    return datos_validos