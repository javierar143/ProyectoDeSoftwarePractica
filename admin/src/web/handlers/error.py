"""Manejadores centralizados de errores HTTP de la aplicación web."""

from dataclasses import dataclass

from flask import render_template


@dataclass
class HTTPError:
    """Representa la información necesaria para mostrar un error HTTP."""

    code: int
    message: str
    description: str


def not_found(error):
    """Renderiza la página correspondiente a un error HTTP 404."""
    error_data = HTTPError(
        code=404,
        message="Página no encontrada",
        description="Lo sentimos, la página que estás buscando no existe.",
    )

    return render_template("error.html", error=error_data), 404


def unauthorized(error):
    """Renderiza la página correspondiente a un error HTTP 401."""
    error_data = HTTPError(
        code=401,
        message="Acceso no autorizado",
        description="No estás autorizado para ver este contenido. Por favor, inicia sesión.",
    )

    return render_template("error.html", error=error_data), 401


def forbidden(error):
    """Renderiza la página correspondiente a un error HTTP 403."""
    error_data = HTTPError(
        code=403,
        message="Acceso prohibido",
        description="No tenés permisos suficientes para acceder a este contenido.",
    )

    return render_template("error.html", error=error_data), 403


def internal_server_error(error):
    """Renderiza la página correspondiente a un error HTTP 500."""
    error_data = HTTPError(
        code=500,
        message="Internal Server Error",
        description="Ocurrió un error en el servidor. Inténtelo más tarde.",
    )

    return render_template("error.html", error=error_data), 500

def bad_request(error):
    """Renderiza la página correspondiente a un error HTTP 400."""
    error_data = HTTPError(
        code=400,
        message="Solicitud incorrecta",
        description="Los datos enviados no son válidos.",
    )

    return render_template("error.html", error=error_data), 400