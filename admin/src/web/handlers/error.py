"""Manejadores centralizados de errores HTTP de la aplicación web y API."""

from dataclasses import dataclass

from flask import jsonify, render_template, request


@dataclass
class HTTPError:
    """Representa la información necesaria para mostrar un error HTTP."""

    code: int
    message: str
    description: str


def _obtener_descripcion(error, default_text: str) -> str:
    """Obtiene la descripción personalizada pasada a abort() o usa el texto por defecto."""
    descripcion = getattr(error, "description", None)
    if descripcion:
        return str(descripcion)
    return default_text


def _responder(error_data: HTTPError):
    """Devuelve JSON para los endpoints de la API (/api/*) o renderiza error.html para vistas web."""
    if request.path.startswith("/api/"):
        return (
            jsonify(
                {
                    "error": error_data.description,
                    "message": error_data.message,
                    "code": error_data.code,
                }
            ),
            error_data.code,
        )
    return render_template("error.html", error=error_data), error_data.code


def bad_request(error):
    """Renderiza la respuesta correspondiente a un error HTTP 400."""
    error_data = HTTPError(
        code=400,
        message="Solicitud incorrecta",
        description=_obtener_descripcion(
            error, "Los datos enviados no son válidos."
        ),
    )
    return _responder(error_data)


def unauthorized(error):
    """Renderiza la respuesta correspondiente a un error HTTP 401."""
    error_data = HTTPError(
        code=401,
        message="Acceso no autorizado",
        description=_obtener_descripcion(
            error,
            "No estás autorizado para ver este contenido. Por favor, inicia sesión.",
        ),
    )
    return _responder(error_data)


def forbidden(error):
    """Renderiza la respuesta correspondiente a un error HTTP 403."""
    error_data = HTTPError(
        code=403,
        message="Acceso prohibido",
        description=_obtener_descripcion(
            error,
            "No tenés permisos suficientes para acceder a este contenido.",
        ),
    )
    return _responder(error_data)


def not_found(error):
    """Renderiza la respuesta correspondiente a un error HTTP 404."""
    error_data = HTTPError(
        code=404,
        message="Página no encontrada",
        description=_obtener_descripcion(
            error, "Lo sentimos, la página que estás buscando no existe."
        ),
    )
    return _responder(error_data)


def conflict(error):
    """Renderiza la respuesta correspondiente a un error HTTP 409."""
    error_data = HTTPError(
        code=409,
        message="Conflicto en la solicitud",
        description=_obtener_descripcion(
            error,
            "La operación genera un conflicto con el estado actual del recurso.",
        ),
    )
    return _responder(error_data)


def internal_server_error(error):
    """Renderiza la respuesta correspondiente a un error HTTP 500."""
    error_data = HTTPError(
        code=500,
        message="Internal Server Error",
        description="Ocurrió un error en el servidor. Inténtelo más tarde.",
    )
    return _responder(error_data)