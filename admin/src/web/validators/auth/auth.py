

def validate_login(email: str, password: str) -> bool:
    """Valida que los campos de correo electrónico y contraseña no estén vacíos.

    Args:
        email (str): El correo electrónico ingresado por el usuario.
        password (str): La contraseña ingresada por el usuario.

    Returns:
        bool: True si ambos campos contienen información (no están vacíos), 
              False en caso contrario.
    """
    return bool(email and password)