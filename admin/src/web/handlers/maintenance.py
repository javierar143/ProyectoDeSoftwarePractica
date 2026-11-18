"""Middleware para interceptar peticiones cuando el sistema está en mantenimiento."""

from flask import current_app, g, jsonify, render_template, request

from src.core import database
from src.core.security.session import get_authenticated_user_id
from src.core.services import configuracion as config_service
from src.core.services.usuarios import permiso as permiso_service
from src.core.services.usuarios import usuario as usuario_service
from src.web.decorators.api import authenticate_api_request


def _respuesta_indisponible():
    mensaje = config_service.MENSAJE_MANTENIMIENTO_DEFAULT
    if request.path.startswith("/api/"):
        return jsonify({"error": mensaje}), 503
    return mensaje, 503


def verificar_modo_mantenimiento():
    """Intercepta las peticiones si el sitio se encuentra en mantenimiento."""
    if request.method == "OPTIONS":
        return None

    # Estas rutas deben poder funcionar durante mantenimiento y sin consultar su estado.
    if request.endpoint and ("static" in request.endpoint or request.path.startswith("/static/")):
        return None
    if request.endpoint and ("auth" in request.endpoint or request.path.startswith("/auth")):
        return None
    if request.path == "/api/configuration":
        return None
    if request.endpoint and request.endpoint.startswith("config."):
        return None

    try:
        cfg = config_service.obtener_configuracion()
    except Exception:
        current_app.logger.exception("No se pudo consultar el estado de mantenimiento.")
        try:
            database.db.session.rollback()
        except Exception:
            current_app.logger.exception("No se pudo revertir la sesión tras el error de configuración.")

        # Conserva la respuesta específica de cuenta bloqueada aunque el estado global no esté disponible.
        if request.path.startswith("/api/"):
            try:
                auth_response = authenticate_api_request()
            except Exception:
                current_app.logger.exception(
                    "No se pudo validar la autenticación API tras fallar la consulta de configuración."
                )
            else:
                if auth_response is not None:
                    return auth_response

        return _respuesta_indisponible()

    if not cfg or not cfg.modo_mantenimiento:
        return None

    # Las APIs usan exclusivamente la identidad Bearer de esta petición.
    if request.path.startswith("/api/"):
        auth_response = authenticate_api_request()
        if auth_response is not None:
            return auth_response

        user = g.user
        user_id = user.id_user
        if getattr(user, "isSystemAdmin", False) or permiso_service.user_has_permission(
            user_id, "user_index"
        ):
            return None
    else:
        # El backoffice web conserva su autenticación por sesión Flask.
        user_id = get_authenticated_user_id()
        if user_id:
            user = usuario_service.get_by_id(user_id)
            if user and (
                getattr(user, "isSystemAdmin", False)
                or permiso_service.user_has_permission(user_id, "user_index")
            ):
                return None

    return render_template(
        "config/mantenimiento.html",
        mensaje=cfg.mensaje_mantenimiento,
    ), 503
