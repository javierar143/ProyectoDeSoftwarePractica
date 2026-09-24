from flask import Flask
from flask import render_template
from src.web.handlers import error
from .config import config



def create_app(env="development", test_config=None, static_folder="../../static"): 
    app = Flask(__name__, static_folder=static_folder)

    if test_config is not None:
        app.config.update(test_config)

    app.config.from_object(config[env]) // sirve para poner la configuracion de la app dependiendo del entorno en el que se encuentre

    @app.route("/")
    def home():
        return render_template("home.html") // Sirve para mostrar la pagina de inicio de la aplicacion renderizando el html de home

    app.register_error_handler(404, error.not_found)
    app.register_error_handler(401, error.unauthorized)
    app.register_error_handler(500, error.internal_server_error)

    return app