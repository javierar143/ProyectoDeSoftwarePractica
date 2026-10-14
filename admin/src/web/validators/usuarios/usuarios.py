"""Validaciones relacionadas con la gestión de usuarios."""


def validate_user_data(
    email: str,
    alias: str,
    password: str,
    rol_id: str,
    personal_id: str,
) -> bool:
    """Valida los datos necesarios para crear un usuario."""
    valid = True

    if not email.strip():
        valid = False

    if not alias.strip():
        valid = False

    if not password:
        valid = False

    if not rol_id.isdigit() or int(rol_id) <= 0:
        valid = False

    if not personal_id.isdigit() or int(personal_id) <= 0:
        valid = False

    return valid