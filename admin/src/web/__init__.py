from flask import Flask, render_template


def create_app(env_name="development", test_config=None, static_folder="../../static"):
    app = Flask(__name__, static_folder=static_folder)

    if test_config is not None:
        app.config.update(test_config)

    @app.route("/")
    def home():
        return render_template("home.html")

    return app