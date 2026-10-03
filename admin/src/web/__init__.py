from flask import Flask
from flask import render_template
from .config import config
from src.core import database
from src.web.handlers import error
from flask_session import Session
from src.web.controllers.auth import auth_bp


def create_app(env="development", test_config=None, static_folder="../../static"): 
    app = Flask(__name__, static_folder=static_folder)    

    if test_config is not None:
        app.config.update(test_config)

    app.config.from_object(config[env]) #sirve para poner la configuracion de la app dependiendo del entorno en el que se encuentre

    Session(app) #creamos la sesion, conecta Flask con la configuración de sesión que ya tenemos.
    
    database.init_app(app)

    @app.route("/")
    def home():
        return render_template("home.html") #Sirve para mostrar la pagina de inicio de la aplicacion renderizando el html de home

    app.register_error_handler(404, error.not_found)
    app.register_error_handler(401, error.unauthorized)
    app.register_error_handler(500, error.internal_server_error)

    @app.cli.command("reset-db")
    def reset_db():
        database.reset_db()
        print("Base de datos reseteada correctamente")

    app.register_blueprint(auth_bp)

    return app

