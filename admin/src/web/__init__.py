from flask import Flask

def create_app(env_name="development", static_folder="../../static"):
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "¡Hola mundo!"

    return app