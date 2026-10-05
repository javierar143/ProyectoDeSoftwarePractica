

def validate_login(email: str, password: str) -> bool:
    return bool(email and password)