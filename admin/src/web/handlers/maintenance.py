"""Middleware para interceptar peticiones cuando el sistema está en mantenimiento."""

from flask import render_template, request

from src.core import database
from src.core.security.session import get_authenticated_user_id
from src.core.services import configuracion as config_service
from src.core.services.usuarios import permiso as permiso_service
from src.core.services.usuarios import usuario as usuario_service


def verificar_modo_mantenimiento():
    """Intercepta las peticiones si el sitio se encuentra en mantenimiento."""
    try:
        cfg = config_service.obtener_configuracion()
    except Exception:
        database.db.session.rollback()
        return None

    if not cfg or not cfg.modo_mantenimiento:
        return None

    # 1. Recursos estáticos
    if request.endpoint and ("static" in request.endpoint or request.path.startswith("/static/")):
        return None

    # 2. Rutas de autenticación
    if request.endpoint and ("auth" in request.endpoint or request.path.startswith("/auth")):
        return None

    # 3. Acceso al panel de configuración
    if request.endpoint and "config" in request.endpoint:
        return None

    # 4. Verificación de privilegios administrativos
    user_id = get_authenticated_user_id()
    if user_id:
        user = usuario_service.get_by_id(user_id)
        if user:
            if getattr(user, "isSystemAdmin", False) or permiso_service.user_has_permission(user_id, "user_index"):
                return None

    # 5. Respuesta HTTP 503 para usuarios sin privilegios
    return render_template(
        "config/mantenimiento.html",
        mensaje=cfg.mensaje_mantenimiento,
    ), 503