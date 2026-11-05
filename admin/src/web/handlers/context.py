"""Inyectores de contexto global para plantillas."""

from src.core.security.session import get_authenticated_user_id, clear_session
from src.core.services.personal import personal as personal_service
from src.core.services.usuarios import usuario as usuario_service


def inject_current_user() -> dict:
    """Expone el usuario autenticado y su personal asociado a todas las plantillas."""
    user_id = get_authenticated_user_id()
    current_user = usuario_service.get_by_id(user_id) if user_id else None

    # Verificamos estado antes de buscar el personal
    if current_user and not current_user.isActive:
        clear_session()
        current_user = None

    current_personal = None
    if current_user and getattr(current_user, "idPersonal", None):
        current_personal = personal_service.get_by_id(current_user.idPersonal)

    return {
        "current_user": current_user,
        "current_personal": current_personal,
    }