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
    PedidoNotFoundError
)

from datetime import date
from src.core.models.enums import CondicionCupo
from src.core.services.pedidos import pedidos


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

@patch("src.core.services.pedidos.pedidos.repo_pedidos.create_pedido_con_solicitudes")
@patch("src.core.services.pedidos.pedidos.Solicitud.existe_duplicado")
@patch("src.core.services.pedidos.pedidos.db")
@patch("src.core.services.pedidos.pedidos.cupos.get_by_sector_y_comida")
def test_calculo_regular_y_excepcion(
    mock_get_cupo, mock_session_get, mock_existe_duplicado, mock_repo_create
):
    """Verifica que si el cupo es 2 y se piden 3 personas, 2 sean REGULAR y 1 EXCEPCION."""
    class MockCupo:
        cantComensales = 2

    mock_get_cupo.return_value = MockCupo()

    class MockPersona:
        isActive = True
        idTipoMenu = 1

    mock_session_get.return_value = MockPersona()
    mock_existe_duplicado.return_value = False
    mock_repo_create.side_effect = lambda pedido, solicitudes: pedido

    pedidos.crear_pedido(
        id_jefe=1,
        id_sector=1,
        fecha_desde=date(2026, 6, 29),
        periodicidad="diaria",
        comidas={1: [10, 11, 12]},
    )

    _, solicitudes_generadas = mock_repo_create.call_args[0]

    assert len(solicitudes_generadas) == 3
    assert solicitudes_generadas[0].condicionCupo == CondicionCupo.REGULAR
    assert solicitudes_generadas[1].condicionCupo == CondicionCupo.REGULAR
    assert solicitudes_generadas[2].condicionCupo == CondicionCupo.EXCEPCION

@patch("src.web.controllers.pedidos.api_pedidos.db")
@patch("src.web.controllers.pedidos.api_pedidos.pedidos.validar_sector_personal")
@patch("src.core.services.pedidos.pedidos.db")
@patch("src.core.services.pedidos.pedidos.cupos.get_by_sector_y_comida")
def test_personal_fijo_otro_sector_rechazado(
    mock_get_cupo, mock_pedidos_db, mock_validar_sector, mock_controller_db, client
):
    """Verifica que si el personal fijo no pertenece al sector del jefe, devuelva 400."""
    class MockCupo:
        cantComensales = 5

    class MockPersona:
        idPersonal = 8
        isActive = True
        idTipoMenu = 1
        idTipoPersonal = 1

    mock_get_cupo.return_value = MockCupo()
    mock_pedidos_db.session.get.return_value = MockPersona()
    mock_validar_sector.side_effect = PedidoValidationError(
        "La persona con ID 8 es personal fijo y no pertenece al sector del Jefe de Servicio."
    )

    response = client.post(
        "/api/requests",
        json={
            "fecha_desde": "2026-06-29",
            "periodicidad": "diaria",
            "comidas": {"1": [8]},
        },
    )

    assert response.status_code == 400
    assert "no pertenece al sector" in response.json["error"]
    mock_controller_db.session.rollback.assert_called_once()

@patch("src.core.services.pedidos.pedidos.pertenece_a_sector")
@patch("src.core.services.pedidos.pedidos.db")
def test_regla_residente_vs_personal_fijo(mock_db, mock_pertenece):
    """Verifica que un Residente se acepte en cualquier sector y un Fijo de otro sector falle."""
    from src.core.services.pedidos.pedidos import validar_sector_personal

    class MockPersona:
        idPersonal = 15
        idTipoPersonal = 2

    class MockTipoResidente:
        nombre = "Residente"

    mock_db.session.get.return_value = MockTipoResidente()
    mock_pertenece.return_value = False

    validar_sector_personal(MockPersona(), id_sector_jefe=1)

    class MockTipoFijo:
        nombre = "Personal Fijo"

    mock_db.session.get.return_value = MockTipoFijo()
    mock_pertenece.return_value = False

    with pytest.raises(PedidoValidationError):
        validar_sector_personal(MockPersona(), id_sector_jefe=1)

@patch("src.web.controllers.pedidos.api_pedidos.db")
@patch("src.web.controllers.pedidos.api_pedidos.pedidos.actualizar_pedido")
def test_actualizar_pedido_exito(mock_actualizar, mock_db, client):
    """Verifica que se actualice un pedido correctamente y se haga commit (200)."""
    class MockPedido:
        idPedido = 10
        estado_general = EstadoPedido.CONFIRMADO

    mock_actualizar.return_value = MockPedido()

    response = client.put(
        "/api/requests/10",
        json={"comidas": {"1": [1, 5]}},
    )

    assert response.status_code == 200
    assert response.json["mensaje"] == "Pedido actualizado exitosamente"
    mock_db.session.commit.assert_called_once()


@patch("src.web.controllers.pedidos.api_pedidos.db")
@patch("src.web.controllers.pedidos.api_pedidos.pedidos.actualizar_pedido")
def test_actualizar_pedido_no_encontrado(mock_actualizar, mock_db, client):
    """Verifica que si el pedido no existe devuelva 404."""
    mock_actualizar.side_effect = PedidoNotFoundError("El pedido con ID 99 no existe.")

    response = client.put(
        "/api/requests/99",
        json={"comidas": {"1": [1]}},
    )

    assert response.status_code == 404
    assert "no existe" in response.json["error"]

@patch("src.web.controllers.pedidos.api_pedidos.db")
@patch("src.web.controllers.pedidos.api_pedidos.pedidos.actualizar_pedido")
def test_actualizar_pedido_ya_procesado(mock_actualizar, mock_db, client):
    """Verifica que si el pedido ya fue autorizado rechace la edición (409)."""
    mock_actualizar.side_effect = PedidoConflictError(
        "No se puede modificar un pedido que ya está autorizado."
    )

    response = client.put(
        "/api/requests/10",
        json={"comidas": {"1": [1]}},
    )

    assert response.status_code == 409
    assert "autorizado" in response.json["error"]
    mock_db.session.rollback.assert_called_once()

@patch("src.web.controllers.pedidos.api_pedidos.db")
@patch("src.web.controllers.pedidos.api_pedidos.pedidos.borrar_pedido")
def test_eliminar_pedido_exito(mock_borrar, mock_db, client):
    """Verifica la eliminación exitosa de un pedido (204)."""
    response = client.delete("/api/requests/10")

    assert response.status_code == 204
    assert response.data == b""
    mock_borrar.assert_called_once_with(10)
    mock_db.session.commit.assert_called_once()


@patch("src.web.controllers.pedidos.api_pedidos.db")
@patch("src.web.controllers.pedidos.api_pedidos.pedidos.borrar_pedido")
def test_eliminar_pedido_no_encontrado(mock_borrar, mock_db, client):
    """Verifica que devuelva 404 si el pedido a borrar no existe."""
    mock_borrar.side_effect = PedidoNotFoundError("El pedido con ID 99 no existe.")

    response = client.delete("/api/requests/99")

    assert response.status_code == 404
    assert "no existe" in response.json["error"]
    mock_db.session.rollback.assert_called_once()

@patch("src.web.controllers.pedidos.api_pedidos.db")
@patch("src.web.controllers.pedidos.api_pedidos.pedidos.borrar_pedido")
def test_eliminar_pedido_ya_procesado(mock_borrar, mock_db, client):
    """Verifica que rechace borrar un pedido si ya fue procesado (409)."""
    mock_borrar.side_effect = PedidoConflictError(
        "No se puede eliminar un pedido que ya fue autorizado."
    )

    response = client.delete("/api/requests/10")

    assert response.status_code == 409
    assert "autorizado" in response.json["error"]
    mock_db.session.rollback.assert_called_once()