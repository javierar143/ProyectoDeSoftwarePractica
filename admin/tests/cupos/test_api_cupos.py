"""Pruebas de la API de cupos."""
from dotenv import load_dotenv
load_dotenv()

import pytest
from unittest.mock import patch

from src.web import create_app
from src.core.services.cupos.cupos import CupoServiceError


@pytest.fixture(scope="module")
def app():
    """Crea la aplicación Flask para las pruebas."""
    app = create_app()
    app.config["TESTING"] = True
    yield app


@pytest.fixture
def client(app):
    """Devuelve el cliente de pruebas de Flask."""
    return app.test_client()


@patch("src.web.controllers.cupos.api_cupos.db")
@patch("src.web.controllers.cupos.api_cupos.cupos.create")
def test_crear_cupo_exito(mock_create, mock_db, client):
    """Verifica que se cree un cupo correctamente (201)."""
    class MockCupo:
        idCupo = 1

    mock_create.return_value = MockCupo()

    response = client.post(
        "/api/quotas",
        json={
            "idSector": 1,
            "idTipoComida": 1,
            "cantComensales": 50,
        },
    )

    assert response.status_code == 201
    assert response.json["mensaje"] == "Cupo creado exitosamente"
    assert response.json["idCupo"] == 1

    # Verificamos que el controlador haya hecho el commit usando el mock
    mock_db.session.commit.assert_called_once()


def test_crear_cupo_faltan_datos(client):
    """Verifica que rechace peticiones con datos incompletos (400)."""
    response = client.post(
        "/api/quotas",
        json={
            "idSector": 1,
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == "Faltan datos obligatorios"


@patch("src.web.controllers.cupos.api_cupos.db")
@patch("src.web.controllers.cupos.api_cupos.cupos.create")
def test_crear_cupo_sector_inactivo(mock_create, mock_db, client):
    """Verifica que devuelva 400 ante un error de regla de negocio del servicio."""
    mock_create.side_effect = CupoServiceError("El sector no existe o está inactivo.")

    response = client.post(
        "/api/quotas",
        json={
            "idSector": 99,
            "idTipoComida": 1,
            "cantComensales": 50,
        },
    )

    assert response.status_code == 400
    assert "inactivo" in response.json["error"]

    mock_db.session.rollback.assert_called_once()