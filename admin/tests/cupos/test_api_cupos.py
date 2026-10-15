"""Pruebas unitarias para el controlador API de cupos."""

from dotenv import load_dotenv

load_dotenv()

from unittest.mock import patch
import pytest

from src.web import create_app


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


class MockUser:
    """Usuario simulado para pruebas de autenticación."""

    def __init__(self, is_active=True, id_rol=1, id_personal=1):
        self.isActive = is_active
        self.id_user = 1
        self.idRol = id_rol
        self.idPersonal = id_personal


class MockRol:
    """Rol simulado para pruebas de permisos."""

    def __init__(self, nombre):
        self.nombre = nombre


def test_crear_cupo_sin_token(client):
    """Verifica que sin token devuelva 401."""
    response = client.post("/api/quotas", json={})
    assert response.status_code == 401
    assert "Token de autenticación requerido" in response.get_json()["error"]


@patch("src.web.controllers.cupos.api_cupos.api_auth.get_authenticated_user")
@patch("src.web.controllers.cupos.api_cupos.db")
def test_crear_cupo_rol_invalido_403(mock_db, mock_get_user, client):
    """Verifica que un Jefe de Servicio no pueda crear cupos (403)."""
    mock_get_user.return_value = MockUser()
    mock_db.session.get.return_value = MockRol(nombre="jefe")

    response = client.post(
        "/api/quotas",
        headers={"Authorization": "Bearer tokenfalso"},
        json={"idSector": 1, "idTipoComida": 1, "cantComensales": 10},
    )

    assert response.status_code == 403
    assert "Solo el Servicio de Alimentación" in response.get_json()["error"]


@patch("src.web.controllers.cupos.api_cupos.cupos.create")
@patch("src.web.controllers.cupos.api_cupos.api_auth.get_authenticated_user")
@patch("src.web.controllers.cupos.api_cupos.db")
def test_crear_cupo_exito_201(mock_db, mock_get_user, mock_create, client):
    """Verifica que el Servicio de Alimentación pueda crear un cupo (201)."""
    mock_get_user.return_value = MockUser()
    mock_db.session.get.return_value = MockRol(nombre="alimentacion")

    class MockCupo:
        idCupo = 1
        idSector = 2
        idTipoComida = 1
        cantComensales = 20

    mock_create.return_value = MockCupo()

    response = client.post(
        "/api/quotas",
        headers={"Authorization": "Bearer tokenfalso"},
        json={"idSector": 2, "idTipoComida": 1, "cantComensales": 20},
    )

    assert response.status_code == 201
    assert response.get_json()["idCupo"] == 1
    mock_db.session.commit.assert_called_once()


@patch("src.web.controllers.cupos.api_cupos.obtener_sector_de_personal")
@patch("src.web.controllers.cupos.api_cupos.api_auth.get_authenticated_user")
@patch("src.web.controllers.cupos.api_cupos.db")
@patch("src.web.controllers.cupos.api_cupos.cupos.listar")
def test_listar_cupos_jefe_filtra_sector_automaticamente(
    mock_listar, mock_db, mock_get_user, mock_obtener_sector, client
):
    """Verifica que al listar cupos como Jefe se filtre por su propio sector."""
    mock_get_user.return_value = MockUser()
    mock_db.session.get.return_value = MockRol(nombre="jefe")
    mock_obtener_sector.return_value = 2
    mock_listar.return_value = ([], 0, 10)

    response = client.get(
        "/api/quotas", headers={"Authorization": "Bearer tokenfalso"}
    )

    assert response.status_code == 200
    mock_listar.assert_called_once()
    assert mock_listar.call_args[1]["id_sector"] == 2