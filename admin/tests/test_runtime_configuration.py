import pytest

from src.core.security.jwt_secret import obtener_clave_jwt
from src.web import cors


def test_obtener_clave_jwt_uses_environment_variable(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "configured-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql://database-secret")

    assert obtener_clave_jwt() == "configured-secret"


def test_obtener_clave_jwt_requires_environment_variable(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://database-secret")

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        obtener_clave_jwt()


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
