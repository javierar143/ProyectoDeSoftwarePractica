"""Configuración CORS de la aplicación."""

from flask_cors import CORS


def configure_cors(app):
    """Configura los recursos y orígenes permitidos para la API."""
    origins = app.config["CORS_ORIGINS"]
    if isinstance(origins, str):
        origins = origins.split(",")
    origins = [
        origin.strip()
        for origin in origins or []
        if isinstance(origin, str) and origin.strip()
    ]
    if not origins:
        raise RuntimeError("CORS_ORIGINS debe contener al menos un origen permitido.")

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": origins,
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,
            }
        },
    )
