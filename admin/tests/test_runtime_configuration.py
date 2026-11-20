import pytest
from flask import Flask

from src.core.security.jwt_secret import obtener_clave_jwt
from src.web.config import ProductionConfig
from src.web.controllers.configuracion import cors


def test_obtener_clave_jwt_uses_environment_variable(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "configured-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql://database-secret")

    assert obtener_clave_jwt() == "configured-secret"


def test_obtener_clave_jwt_requires_environment_variable(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://database-secret")

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        obtener_clave_jwt()


def test_production_secret_configuration_reads_environment_when_loaded(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("CORS_ORIGINS", "https://grupo50.proyecto2026.linti.unlp.edu.ar")
    app = Flask(__name__)

    app.config.from_object(ProductionConfig)

    assert app.config["GOOGLE_CLIENT_ID"] == "google-client-id"
    assert app.config["CORS_ORIGINS"] == "https://grupo50.proyecto2026.linti.unlp.edu.ar"


@pytest.mark.parametrize(
    ("configured_origins", "expected_origins"),
    [
        (["http://localhost:5173"], ["http://localhost:5173"]),
        (
            "https://portal.example, https://admin.example",
            ["https://portal.example", "https://admin.example"],
        ),
    ],
)
def test_configure_cors_supports_list_and_comma_separated_origins(
    monkeypatch, configured_origins, expected_origins
):
    captured = {}

    class FlaskCorsStub:
        @staticmethod
        def apply(app, resources):
            captured["app"] = app
            captured["resources"] = resources

    monkeypatch.setattr(cors, "CORS", FlaskCorsStub.apply)
    app = type("App", (), {"config": {"CORS_ORIGINS": configured_origins}})()

    cors.configure_cors(app)

    assert captured["app"] is app
    assert captured["resources"] == {
        r"/api/*": {
            "origins": expected_origins,
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
        }
    }


def test_configure_cors_allows_login_preflight_from_portal():
    app = Flask(__name__)
    app.config["CORS_ORIGINS"] = "https://grupo50.proyecto2026.linti.unlp.edu.ar"
    app.add_url_rule("/api/auth/login", view_func=lambda: "ok", methods=["POST"])
    cors.configure_cors(app)

    response = app.test_client().options(
        "/api/auth/login",
        headers={
            "Origin": "https://grupo50.proyecto2026.linti.unlp.edu.ar",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == (
        "https://grupo50.proyecto2026.linti.unlp.edu.ar"
    )
    assert "POST" in response.headers["Access-Control-Allow-Methods"]
    assert {"content-type", "authorization"}.issubset(
        {header.strip().lower() for header in response.headers["Access-Control-Allow-Headers"].split(",")}
    )
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
