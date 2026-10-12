"""Pruebas unitarias para la API de pedidos."""
from dotenv import load_dotenv
load_dotenv()

import pytest
from unittest.mock import patch

from src.web import create_app
from src.core.models.enums import EstadoPedido
from src.core.services.pedidos.pedidos import (
    PedidoValidationError,
    PedidoConflictError,
)


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


# 1. TEST CAMINO FELIZ (201)
@patch("src.web.controllers.pedidos.api_pedidos.db")
@patch("src.web.controllers.pedidos.api_pedidos.pedidos.crear_pedido")
def test_crear_pedido_exito(mock_crear_pedido, mock_db, client):
    """Verifica que se cree un pedido correctamente y se haga commit (201)."""
    class MockPedido:
        idPedido = 10
        estado_general = EstadoPedido.CONFIRMADO

    mock_crear_pedido.return_value = MockPedido()

    response = client.post(
        "/api/requests",
        json={
            "fecha_desde": "2026-06-29",
            "periodicidad": "semanal",
            "comidas": {
                "1": [1, 2, 10],
                "2": [1],
            },
        },
    )

    assert response.status_code == 201
    assert response.json["mensaje"] == "Pedido creado exitosamente"
    assert response.json["idPedido"] == 10
    assert response.json["estado"] == "confirmado"
    mock_db.session.commit.assert_called_once()


# 2. TEST FALTAN DATOS OBLIGATORIOS (400)
def test_crear_pedido_faltan_datos(client):
    """Verifica que rechace un JSON incompleto con código 400."""
    response = client.post(
        "/api/requests",
        json={
            "fecha_desde": "2026-06-29",
            # Faltan 'periodicidad' y 'comidas'
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == "Faltan datos obligatorios"


@patch("src.web.controllers.pedidos.api_pedidos.db")
@patch("src.web.controllers.pedidos.api_pedidos.pedidos.crear_pedido")
def test_crear_pedido_persona_inactiva(mock_crear_pedido, mock_db, client):
    """Verifica que devuelva 400 y haga rollback si una persona está inactiva."""
    mock_crear_pedido.side_effect = PedidoValidationError(
        "La persona con ID 5 no existe o está inactiva."
    )

    response = client.post(
        "/api/requests",
        json={
            "fecha_desde": "2026-06-29",
            "periodicidad": "diaria",
            "comidas": {"1": [5]},
        },
    )

    assert response.status_code == 400
    assert "inactiva" in response.json["error"]
    mock_db.session.rollback.assert_called_once()


@patch("src.web.controllers.pedidos.api_pedidos.db")
@patch("src.web.controllers.pedidos.api_pedidos.pedidos.crear_pedido")
def test_crear_pedido_duplicado(mock_crear_pedido, mock_db, client):
    """Verifica que devuelva 409 y haga rollback si hay una solicitud duplicada."""
    mock_crear_pedido.side_effect = PedidoConflictError(
        "Ya existe una solicitud para la persona 1 en esa fecha y comida."
    )

    response = client.post(
        "/api/requests",
        json={
            "fecha_desde": "2026-06-29",
            "periodicidad": "diaria",
            "comidas": {"1": [1]},
        },
    )

    assert response.status_code == 409
    assert "Ya existe una solicitud" in response.json["error"]
    mock_db.session.rollback.assert_called_once()