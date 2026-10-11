
"""Validaciones de los datos de usuarios."""


def validate_user_data(
    email: str,
    alias: str,
    password: str,
    rol_nombre: str,
    personal_id: str,
) -> bool:
    """Comprueba que los campos obligatorios estén completos y sean válidos."""
    email_limpio = email.strip()
    alias_limpio = alias.strip()
    password_limpia = password.strip()
    rol_limpio = rol_nombre.strip()
    personal_id_limpio = personal_id.strip()

    datos_validos = all(
        [
            email_limpio,
            "@" in email_limpio,
            alias_limpio,
            password_limpia,
            rol_limpio,
            personal_id_limpio.isdigit(),
        ]
    )

    return datos_validos
