"""Pruebas de la API de sectores."""

from dotenv import load_dotenv

load_dotenv()

import pytest

from src.web import create_app
from src.core.database import reset_db


@pytest.fixture(scope="module")
def app():
    """App de prueba con DB reseedeada (incluye permisos y usuarios operativos)."""
    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        reset_db()
        yield app


@pytest.fixture
def client(app):
    """Cliente HTTP de Flask para cada test."""
    return app.test_client()


def _login(client, email: str, password: str = "1234") -> str:
    """Obtiene un access_token de la API."""
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.get_json()
    return response.get_json()["access_token"]


@pytest.fixture(scope="module")
def token_jefe(app):
    """Token del Jefe, una sola vez para todo el módulo."""
    return _login(app.test_client(), "jefe@ejemplo.com")


@pytest.fixture(scope="module")
def token_alimentacion(app):
    """Token de Alimentación, una sola vez para todo el módulo."""
    return _login(app.test_client(), "alimentacion@ejemplo.com")


def test_listar_sectores_sin_token_401(client):
    """Sin Bearer token → 401."""
    response = client.get("/api/sectors")
    assert response.status_code == 401
    assert "Token" in response.get_json()["error"]


def test_listar_sectores_jefe_403(client, token_jefe):
    """Jefe de Servicio no tiene sector_index → 403."""
    response = client.get(
        "/api/sectors",
        headers={"Authorization": f"Bearer {token_jefe}"},
    )
    assert response.status_code == 403


def test_listar_sectores_alimentacion_200(client, token_alimentacion):
    """Servicio de Alimentación con sector_index → 200 y lista."""
    response = client.get(
        "/api/sectors",
        headers={"Authorization": f"Bearer {token_alimentacion}"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert {"id", "nombre", "descripcion", "estado"} <= set(data[0].keys())


def test_detalle_sector_alimentacion_200(client, token_alimentacion):
    """Detalle de un sector existente → 200 con fechas."""
    listado = client.get(
        "/api/sectors",
        headers={"Authorization": f"Bearer {token_alimentacion}"},
    ).get_json()
    sector_id = listado[0]["id"]

    response = client.get(
        f"/api/sectors/{sector_id}",
        headers={"Authorization": f"Bearer {token_alimentacion}"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == sector_id
    assert "fecha_creacion" in data
    assert "fecha_modificacion" in data


def test_detalle_sector_inexistente_404(client, token_alimentacion):
    """Id inexistente → 404."""
    response = client.get(
        "/api/sectors/999999",
        headers={"Authorization": f"Bearer {token_alimentacion}"},
    )
    assert response.status_code == 404