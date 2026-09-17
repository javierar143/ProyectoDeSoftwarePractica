from flask import Flask
from src.web.handlers import error

def create_app(env_name="development", static_folder="../../static"):
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "¡Hola mundo!"

    app.register_error_handler(404, error.not_found)
    app.register_error_handler(401, error.unauthorized)
    app.register_error_handler(500, error.internal_server_error)
    
    return app