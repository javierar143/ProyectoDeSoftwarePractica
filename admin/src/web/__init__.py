"""Inicialización y configuración de la aplicación Flask."""

from flask import Flask
from flask_session import Session

from src.core import database
from src.web import commands
from src.web.config import config
from src.web.controllers.auth import auth_bp
from src.web.controllers.home import home, home_bp
from src.web.controllers.auth.api_auth import api_auth_controller
from src.web.controllers.autorizaciones.api_autorizaciones import (
    api_autorizaciones_controller,
)
from src.web.controllers.configuracion.config import config_controller
from src.web.controllers.cupos.api_cupos import bp_cupos
from src.web.controllers.home import home_bp
from src.web.controllers.pedidos.api_pedidos import (
    bp_pedidos,
    bp_resumen_pedidos,
)
from src.web.controllers.personal.personal import personal_bp
from src.web.controllers.personal.personal_csv import personal_csv_bp
from src.web.controllers.personal.api_personal import api_personal_controller
from src.web.controllers.sectores.api_sectores import api_sectores_bp
from src.web.controllers.sectores.sectores import sectores_bp
from src.web.controllers.usuarios import usuarios_controller
from src.web.handlers import cache, context, error, maintenance


def _register_blueprints(app: Flask) -> None:
    """Registra todos los blueprints web y endpoints de la API."""
    
    # Vistas generales
    app.register_blueprint(home_bp)
    app.add_url_rule("/", endpoint="home", view_func=home)

    # Autenticación
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_auth_controller)

    # Administración
    app.register_blueprint(usuarios_controller)
    app.register_blueprint(personal_bp)
    app.register_blueprint(personal_csv_bp)
    app.register_blueprint(api_personal_controller)
    app.register_blueprint(sectores_bp)
    app.register_blueprint(api_sectores_bp)

    # Configuración y autorizaciones
    app.register_blueprint(config_controller)
    app.register_blueprint(api_autorizaciones_controller)

    # Cupos y pedidos
    app.register_blueprint(bp_cupos)
    app.register_blueprint(bp_pedidos)
    app.register_blueprint(bp_resumen_pedidos)


def create_app(
    env="development",
    test_config=None,
    static_folder="../../static",
):
    """Crea y configura la instancia de la aplicación Flask sin disparar escrituras en BD."""
    app = Flask(__name__, static_folder=static_folder)

    if test_config is not None:
        app.config.update(test_config)

    app.config.from_object(config[env])

    Session(app)
    database.init_app(app)

    # Inyectores y middlewares de ciclo de vida HTTP
    app.context_processor(context.inject_current_user)
    app.before_request(maintenance.verificar_modo_mantenimiento)
    app.after_request(cache.add_no_cache_headers)

    # Errores, comandos de terminal y Blueprints
    error.register_error_handlers(app)
    commands.register_commands(app)
    _register_blueprints(app)

    return app