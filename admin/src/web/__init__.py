"""Inicialización y configuración de la aplicación Flask."""

from flask import Flask, render_template
from flask_session import Session

from .config import config

from src.web.controllers.auth import auth_bp
from src.web.controllers.auth.api_auth import api_auth_controller
from src.web.controllers.usuarios.usuarios import usuarios_controller
from src.web.handlers import error

from src.core import database
from src.core.services.usuarios import usuario
from src.core.security.session import get_authenticated_user_id


def create_app(
    env="development",
    test_config=None,
    static_folder="../../static",
):
    """Crea y configura una instancia de la aplicación Flask."""
    app = Flask(__name__, static_folder=static_folder)

    if test_config is not None:
        app.config.update(test_config)

    app.config.from_object(config[env])

    Session(app)
    database.init_app(app) 

    @app.context_processor
    def inject_authenticated_user():
        """Expone el usuario autenticado a las plantillas."""
        user_id = get_authenticated_user_id()
        usuario_actual = usuario.get_by_id(user_id) if user_id is not None else None

        return {"usuario_actual": usuario_actual}

    @app.route("/")
    def home():
        """Renderiza la página principal de la aplicación."""
        return render_template("home.html")

    app.register_error_handler(400, error.bad_request)
    app.register_error_handler(401, error.unauthorized)
    app.register_error_handler(403, error.forbidden)
    app.register_error_handler(404, error.not_found)
    app.register_error_handler(500, error.internal_server_error)

    @app.cli.command("reset-db")
    def reset_db():
        """Restablece la base de datos de desarrollo."""
        database.reset_db()
        print("Base de datos reseteada correctamente")
        return None

    # =========================
    # AUTENTICACIÓN
    # =========================
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_auth_controller)

    # =========================
    # ADMINISTRACIÓN
    # =========================
    app.register_blueprint(usuarios_controller)

    # =========================
    # OPERACIÓN
    # =========================
    # app.register_blueprint(...)

    return app