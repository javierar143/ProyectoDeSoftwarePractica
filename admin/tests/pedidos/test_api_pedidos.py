"""Pruebas unitarias para la API de pedidos."""

from dotenv import load_dotenv

load_dotenv()

from unittest.mock import patch
from flask import abort
import pytest

from src.core.models.enums import EstadoPedido
from src.web import create_app


@pytest.fixture(scope="module")
def app():
    """Crea la aplicación Flask para las pruebas."""
    app = create_app()
    app.config["TESTING"] = True
    yield app


@pytest.fixture
def client(app, monkeypatch):
    """Devuelve el cliente de pruebas de Flask."""
    from types import SimpleNamespace

    from src.core.services import configuracion as config_service

    monkeypatch.setattr(
        config_service,
        "obtener_configuracion",
        lambda: SimpleNamespace(modo_mantenimiento=False, mensaje_mantenimiento=""),
    )
    return app.test_client()


class MockUser:
    """Usuario simulado para las pruebas de pedidos."""

    def __init__(self, is_active=True, id_rol=1, id_personal=1, id_sector=None):
        self.isActive = is_active
        self.id_user = 1
        self.idRol = id_rol
        self.idPersonal = id_personal
        self.idSector = id_sector


class MockRol:
    """Rol simulado para las pruebas de pedidos."""

    def __init__(self, nombre):
        self.nombre = nombre


def test_pedidos_requiere_auth(client):
    """Verifica que sin token devuelva 401."""
    response = client.get("/api/requests")
    assert response.status_code == 401


@patch("src.core.services.usuarios.permiso.user_has_role_permission")
@patch("src.core.services.usuarios.rol.get_by_id")
@patch("src.core.services.auth.api_auth.get_authenticated_user_status")
def test_pedidos_sin_permiso_403(
    mock_get_user, mock_get_rol, mock_has_perm, client
):
    """Verifica que un usuario sin permiso requests_index reciba 403."""
    mock_get_user.return_value = (MockUser(id_sector=5), None)
    mock_get_rol.return_value = MockRol(nombre="Jefe de Servicio")
    mock_has_perm.return_value = False

    response = client.get(
        "/api/requests", headers={"Authorization": "Bearer tokenfalso"}
    )
    assert response.status_code == 403

@patch("src.web.controllers.pedidos.api_pedidos.pedidos.obtener_detalle_pedido")
@patch("src.core.services.usuarios.permiso.user_has_role_permission")
@patch("src.core.services.usuarios.rol.get_by_id")
@patch("src.core.services.auth.api_auth.get_authenticated_user_status")
def test_obtener_detalle_pedido_ajeno_403(
    mock_get_user,
    mock_get_rol,
    mock_has_perm,
    mock_servicio_detalle,
    client,
):
    """Verifica que consultar un pedido de otro sector devuelva 403."""
    mock_get_user.return_value = (MockUser(id_sector=5), None)
    mock_get_rol.return_value = MockRol(nombre="Jefe de Servicio")
    mock_has_perm.side_effect = (
        lambda user_id, permiso: permiso == "requests_index"
    )
    mock_servicio_detalle.side_effect = lambda *a, **kw: abort(
        403,
        description="No tiene permisos para consultar un pedido de otro sector.",
    )

    response = client.get(
        "/api/requests/99", headers={"Authorization": "Bearer tokenfalso"}
    )
    assert response.status_code == 403

@patch("src.web.controllers.pedidos.api_pedidos.pedidos.crear_pedido")
@patch("src.core.services.usuarios.permiso.user_has_role_permission")
@patch("src.core.services.usuarios.rol.get_by_id")
@patch("src.core.services.auth.api_auth.get_authenticated_user_status")
def test_crear_pedido_exito(
    mock_get_user, mock_get_rol, mock_has_perm, mock_crear_pedido, client
):
    """Verifica que se cree un pedido correctamente (201)."""
    usuario = MockUser(id_sector=5)
    usuario.idSector = 5
    mock_get_user.return_value = (usuario, None)
    mock_get_rol.return_value = MockRol(nombre="Jefe de Servicio")
    mock_has_perm.side_effect = (
        lambda user_id, permiso: permiso == "requests_new"
    )

    class MockPedido:
        idPedido = 10
        estado_general = EstadoPedido.CONFIRMADO

    mock_crear_pedido.return_value = MockPedido()

    response = client.post(
        "/api/requests",
        headers={"Authorization": "Bearer tokenfalso"},
        json={
            "fecha_desde": "2026-11-20",
            "periodicidad": "semanal",
            "comidas": {"1": [1, 2, 10], "2": [1]},
        },
    )

    assert response.status_code == 201
    assert response.json["mensaje"] == "Pedido creado exitosamente"
    assert response.json["idPedido"] == 10
    assert response.json["estado"] == "confirmado"
    mock_crear_pedido.assert_called_once()

@patch("src.core.services.usuarios.permiso.user_has_role_permission")
@patch("src.core.services.usuarios.rol.get_by_id")
@patch("src.core.services.auth.api_auth.get_authenticated_user_status")
def test_crear_pedido_faltan_datos(
    mock_get_user, mock_get_rol, mock_has_perm, client
):
    """Verifica que rechace un JSON incompleto con código 400."""
    mock_get_user.return_value = (MockUser(id_sector=5), None)
    mock_get_rol.return_value = MockRol(nombre="Jefe de Servicio")
    mock_has_perm.side_effect = (
        lambda user_id, permiso: permiso == "requests_new"
    )

    response = client.post(
        "/api/requests",
        headers={"Authorization": "Bearer tokenfalso"},
        json={"fecha_desde": "2026-11-20"},
    )

    assert response.status_code == 400
    assert "Faltan datos obligatorios" in response.json["error"]
    assert response.json["field_errors"] == {
        "periodicidad": "Este campo es obligatorio.",
        "comidas": "Este campo es obligatorio.",
    }

@patch("src.web.controllers.pedidos.api_pedidos.pedidos.crear_pedido")
@patch("src.core.services.usuarios.permiso.user_has_role_permission")
@patch("src.core.services.usuarios.rol.get_by_id")
@patch("src.core.services.auth.api_auth.get_authenticated_user_status")
def test_crear_pedido_persona_inactiva(
    mock_get_user, mock_get_rol, mock_has_perm, mock_crear_pedido, client
):
    """Verifica que devuelva 400 si una persona está inactiva."""
    mock_get_user.return_value = (MockUser(id_sector=5), None)
    mock_get_rol.return_value = MockRol(nombre="Jefe de Servicio")
    mock_has_perm.side_effect = (
        lambda user_id, permiso: permiso == "requests_new"
    )
    mock_crear_pedido.side_effect = lambda *a, **kw: abort(
        400, description="La persona con ID 5 no existe o está inactiva."
    )

    response = client.post(
        "/api/requests",
        headers={"Authorization": "Bearer tokenfalso"},
        json={
            "fecha_desde": "2026-11-20",
            "periodicidad": "diaria",
            "comidas": {"1": [5]},
        },
    )

    assert response.status_code == 400
    assert "inactiva" in response.json["error"]

@patch("src.web.controllers.pedidos.api_pedidos.pedidos.crear_pedido")
@patch("src.core.services.usuarios.permiso.user_has_role_permission")
@patch("src.core.services.usuarios.rol.get_by_id")
@patch("src.core.services.auth.api_auth.get_authenticated_user_status")
def test_crear_pedido_duplicado(
    mock_get_user, mock_get_rol, mock_has_perm, mock_crear_pedido, client
):
    """Verifica que devuelva 409 si hay una solicitud duplicada."""
    mock_get_user.return_value = (MockUser(id_sector=5), None)
    mock_get_rol.return_value = MockRol(nombre="Jefe de Servicio")
    mock_has_perm.side_effect = (
        lambda user_id, permiso: permiso == "requests_new"
    )
    mock_crear_pedido.side_effect = lambda *a, **kw: abort(
        409,
        description="Ya existe una solicitud para la persona 1 en esa fecha y comida.",
    )

    response = client.post(
        "/api/requests",
        headers={"Authorization": "Bearer tokenfalso"},
        json={
            "fecha_desde": "2026-11-20",
            "periodicidad": "diaria",
            "comidas": {"1": [1]},
        },
    )

    assert response.status_code == 409
    assert "Ya existe una solicitud" in response.json["error"]

@patch("src.web.controllers.pedidos.api_pedidos.pedidos.actualizar_pedido")
@patch("src.core.services.usuarios.permiso.user_has_role_permission")
@patch("src.core.services.usuarios.rol.get_by_id")
@patch("src.core.services.auth.api_auth.get_authenticated_user_status")
def test_actualizar_pedido_exito(
    mock_get_user, mock_get_rol, mock_has_perm, mock_actualizar, client
):
    """Verifica que se actualice un pedido correctamente (200)."""
    mock_get_user.return_value = (MockUser(id_sector=5), None)
    mock_get_rol.return_value = MockRol(nombre="Jefe de Servicio")
    mock_has_perm.side_effect = (
        lambda user_id, permiso: permiso == "requests_update"
    )

    class MockPedido:
        idPedido = 10
        estado_general = EstadoPedido.CONFIRMADO

    mock_actualizar.return_value = MockPedido()

    response = client.put(
        "/api/requests/10",
        headers={"Authorization": "Bearer tokenfalso"},
        json={"comidas": {"1": [1, 5]}},
    )

    assert response.status_code == 200
    assert response.json["mensaje"] == "Pedido actualizado exitosamente"
    mock_actualizar.assert_called_once()

@patch("src.web.controllers.pedidos.api_pedidos.pedidos.actualizar_pedido")
@patch("src.core.services.usuarios.permiso.user_has_role_permission")
@patch("src.core.services.usuarios.rol.get_by_id")
@patch("src.core.services.auth.api_auth.get_authenticated_user_status")
def test_actualizar_pedido_no_encontrado(
    mock_get_user, mock_get_rol, mock_has_perm, mock_actualizar, client
):
    """Verifica que si el pedido no existe devuelva 404."""
    mock_get_user.return_value = (MockUser(id_sector=5), None)
    mock_get_rol.return_value = MockRol(nombre="Jefe de Servicio")
    mock_has_perm.side_effect = (
        lambda user_id, permiso: permiso == "requests_update"
    )
    mock_actualizar.side_effect = lambda *a, **kw: abort(
        404, description="El pedido con ID 99 no existe."
    )

    response = client.put(
        "/api/requests/99",
        headers={"Authorization": "Bearer tokenfalso"},
        json={"comidas": {"1": [1]}},
    )

    assert response.status_code == 404
    assert "no existe" in response.json["error"]

@patch("src.web.controllers.pedidos.api_pedidos.pedidos.actualizar_pedido")
@patch("src.core.services.usuarios.permiso.user_has_role_permission")
@patch("src.core.services.usuarios.rol.get_by_id")
@patch("src.core.services.auth.api_auth.get_authenticated_user_status")
def test_actualizar_pedido_ya_procesado(
    mock_get_user, mock_get_rol, mock_has_perm, mock_actualizar, client
):
    """Verifica que si el pedido ya fue autorizado rechace la edición (409)."""
    mock_get_user.return_value = (MockUser(id_sector=5), None)
    mock_get_rol.return_value = MockRol(nombre="Jefe de Servicio")
    mock_has_perm.side_effect = (
        lambda user_id, permiso: permiso == "requests_update"
    )
    mock_actualizar.side_effect = lambda *a, **kw: abort(
        409,
        description="No se puede modificar un pedido que ya está autorizado.",
    )

    response = client.put(
        "/api/requests/10",
        headers={"Authorization": "Bearer tokenfalso"},
        json={"comidas": {"1": [1]}},
    )

    assert response.status_code == 409
    assert "autorizado" in response.json["error"]

@patch("src.web.controllers.pedidos.api_pedidos.pedidos.borrar_pedido")
@patch("src.core.services.usuarios.permiso.user_has_role_permission")
@patch("src.core.services.usuarios.rol.get_by_id")
@patch("src.core.services.auth.api_auth.get_authenticated_user_status")
def test_eliminar_pedido_exito(
    mock_get_user, mock_get_rol, mock_has_perm, mock_borrar, client
):
    """Verifica la eliminación (baja lógica) exitosa de un pedido (204)."""
    mock_get_user.return_value = (MockUser(id_sector=5), None)
    mock_get_rol.return_value = MockRol(nombre="Jefe de Servicio")
    mock_has_perm.side_effect = (
        lambda user_id, permiso: permiso == "requests_destroy"
    )

    response = client.delete(
        "/api/requests/10",
        headers={"Authorization": "Bearer tokenfalso"},
    )

    assert response.status_code == 204
    assert response.data == b""
    mock_borrar.assert_called_once_with(10, id_sector_jefe=5)

@patch("src.web.controllers.pedidos.api_pedidos.pedidos.borrar_pedido")
@patch("src.core.services.usuarios.permiso.user_has_role_permission")
@patch("src.core.services.usuarios.rol.get_by_id")
@patch("src.core.services.auth.api_auth.get_authenticated_user_status")
def test_eliminar_pedido_no_encontrado(
    mock_get_user, mock_get_rol, mock_has_perm, mock_borrar, client
):
    """Verifica que devuelva 404 si el pedido a borrar no existe."""
    mock_get_user.return_value = (MockUser(id_sector=5), None)
    mock_get_rol.return_value = MockRol(nombre="Jefe de Servicio")
    mock_has_perm.side_effect = (
        lambda user_id, permiso: permiso == "requests_destroy"
    )
    mock_borrar.side_effect = lambda *a, **kw: abort(
        404, description="El pedido con ID 99 no existe."
    )

    response = client.delete(
        "/api/requests/99",
        headers={"Authorization": "Bearer tokenfalso"},
    )

    assert response.status_code == 404
    assert "no existe" in response.json["error"]

@patch("src.web.controllers.pedidos.api_pedidos.pedidos.borrar_pedido")
@patch("src.core.services.usuarios.permiso.user_has_role_permission")
@patch("src.core.services.usuarios.rol.get_by_id")
@patch("src.core.services.auth.api_auth.get_authenticated_user_status")
def test_eliminar_pedido_ya_procesado(
    mock_get_user, mock_get_rol, mock_has_perm, mock_borrar, client
):
    """Verifica que rechace borrar un pedido si ya fue procesado (409)."""
    mock_get_user.return_value = (MockUser(id_sector=5), None)
    mock_get_rol.return_value = MockRol(nombre="Jefe de Servicio")
    mock_has_perm.side_effect = (
        lambda user_id, permiso: permiso == "requests_destroy"
    )
    mock_borrar.side_effect = lambda *a, **kw: abort(
        409,
        description="No se puede eliminar un pedido que ya fue autorizado.",
    )

    response = client.delete(
        "/api/requests/10",
        headers={"Authorization": "Bearer tokenfalso"},
    )

    assert response.status_code == 409
    assert "autorizado" in response.json["error"]