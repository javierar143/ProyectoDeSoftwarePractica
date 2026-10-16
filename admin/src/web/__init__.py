"""Inicialización y configuración de la aplicación Flask."""

from flask import Flask, render_template, request, session
from flask_session import Session

from .config import config
from src.core import database
from src.web.controllers.auth import auth_bp
from src.web.controllers.auth.api_auth import api_auth_controller
from src.web.controllers.usuarios import usuarios_controller
from src.web.controllers.personal.personal import personal_bp
from src.web.controllers.autorizaciones.api_autorizaciones import api_autorizaciones_controller
from src.web.controllers.configuracion.config import config_controller
from src.web.handlers import error
from src.web.controllers.sectores.sectores import sectores_bp
from src.web.controllers.cupos.api_cupos import bp_cupos
from src.web.controllers.pedidos.api_pedidos import bp_pedidos

from src.core.seeds.sectores import SECTORES_INICIALES
from src.core.services.sectores import sector as sector_service
from src.core.security.session import get_authenticated_user_id
from src.core.services.usuarios import usuario as usuario_service
from src.core.services import configuracion as config_service
from src.core.services.usuarios import permiso as permiso_service
from src.core.services.personal import personal as personal_service
from src.web.controllers.sectores.api_sectores import api_sectores_bp

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

    if not app.config.get("TESTING"):
        with app.app_context():
            database.ensure_db_initialized()

    @app.context_processor
    def inject_current_user():
        """Expone el usuario autenticado y su personal asociado a todas las plantillas."""
        user_id = get_authenticated_user_id()
        current_user = usuario_service.get_by_id(user_id) if user_id else None
        current_personal = None
        if current_user and hasattr(current_user, "idPersonal") and current_user.idPersonal:
            current_personal = personal_service.get_by_id(current_user.idPersonal)
        return {"current_user": current_user, "current_personal": current_personal}

    # =========================
    # MIDDLEWARE MODO MANTENIMIENTO
    # =========================
    @app.before_request
    def verificar_modo_mantenimiento():
        """Intercepta las peticiones si el sitio se encuentra en mantenimiento."""
        try:
            cfg = config_service.obtener_configuracion()
        except Exception:
            database.db.session.rollback()
            return None

        # Si no está en mantenimiento, permitimos el flujo normal
        if not cfg or not cfg.modo_mantenimiento:
            return None

        # 1. Permitir recursos estáticos (CSS, JS, imágenes)
        if request.endpoint and ('static' in request.endpoint or request.path.startswith('/static/')):
            return None

        # 2. Permitir acceso al login / autenticación para que el admin pueda ingresar
        if request.endpoint and ('auth' in request.endpoint or request.path.startswith('/auth')):
            return None

        # 3. Permitir acceso al propio panel de configuración
        if request.endpoint and 'config' in request.endpoint:
            return None

        # 4. Verificar si el usuario autenticado es Administrador o tiene permisos
        user_id = get_authenticated_user_id()
        if user_id:
            user = usuario_service.get_by_id(user_id)
            if user:
                # Verificamos si es administrador del sistema (isSystemAdmin) o si tiene permisos globales
                if getattr(user, "isSystemAdmin", False) or permiso_service.user_has_permission(user_id, "user_index"):
                    return None

        # 5. Si es un usuario común o invitado, bloqueamos y mostramos la vista de mantenimiento
        return render_template(
            "config/mantenimiento.html",
            mensaje=cfg.mensaje_mantenimiento
        ), 503

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

    @app.cli.command("seed-sectores")
    def seed_sectores():
        """Carga los sectores iniciales del hospital que todavía no existan."""
        creados = sector_service.seed(SECTORES_INICIALES)
        print(f"Sectores creados: {creados}")

    # =========================
    # AUTENTICACIÓN
    # =========================
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_auth_controller)

    # =========================
    # ADMINISTRACIÓN
    # =========================
    app.register_blueprint(usuarios_controller)
    app.register_blueprint(personal_bp)
    app.register_blueprint(sectores_bp)
    app.register_blueprint(api_sectores_bp)

    # =========================
    # OPERACIÓN/AUTORIZACIONES
    # =========================
    app.register_blueprint(config_controller)
    app.register_blueprint(api_autorizaciones_controller)
    # =========================
    # CUPOS Y PEDIDOS
    # =========================
    app.register_blueprint(bp_cupos)
    app.register_blueprint(bp_pedidos)
    return app