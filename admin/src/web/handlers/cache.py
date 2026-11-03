"""Control de cabeceras de respuesta y prevención de almacenamiento en caché."""

from flask import request


def add_no_cache_headers(response):
    """Evita que el navegador guarde en caché las páginas protegidas."""
    if request.endpoint != "static":
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response