from flask import Flask


def create_app(env="development", static_folder="../../static"):
    app = Flask(__name__, static_folder=static_folder)

    @app.route("/")
    def home():
        return "¡Hola mundo!"
    return app