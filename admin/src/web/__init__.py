from flask import Flask
from flask import render_template
from src.web.handlers import error

def create_app(env_name="development", test_config=None, static_folder="../../static"):
    app = Flask(__name__, static_folder=static_folder)

    if test_config is not None:
        app.config.update(test_config)

    @app.route("/")
    def home():
        return render_template("home.html")

    app.register_error_handler(404, error.not_found)
    app.register_error_handler(401, error.unauthorized)
    app.register_error_handler(500, error.internal_server_error)

    return app