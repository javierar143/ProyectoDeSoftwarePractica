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
