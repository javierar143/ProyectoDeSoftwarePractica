"""Pruebas unitarias para el servicio de pedidos."""

from dotenv import load_dotenv

load_dotenv()

from datetime import date
from unittest.mock import patch
import pytest

from src.core.models.enums import CondicionCupo, EstadoPedido
from src.core.services.pedidos import pedidos
from src.core.services.pedidos.pedidos import (
    PedidoConflictError,
    PedidoForbiddenError,
    PedidoValidationError,
)


@patch("src.core.services.pedidos.pedidos.repo_pedidos.existe_pedido_en_sector_y_fecha")
def test_crear_pedido_duplicado_por_fecha(mock_existe):
    """Verifica que si ya hay un pedido para ese sector y fecha lance 409."""
    mock_existe.return_value = True

    with pytest.raises(PedidoConflictError, match="Ya existe un pedido registrado"):
        pedidos.crear_pedido(
            id_jefe=1,
            id_sector=1,
            fecha_desde=date.today(),
            periodicidad="diaria",
            comidas={"1": [1, 2]},
        )


@patch("src.core.services.pedidos.pedidos.repo_pedidos.get_pedido_by_id")
def test_borrar_pedido_no_confirmado(mock_get_pedido):
    """Verifica que no se pueda eliminar un pedido ya autorizado."""
    class MockPedido:
        idSector = 1
        estado_general = EstadoPedido.AUTORIZADO

    mock_get_pedido.return_value = MockPedido()

    with pytest.raises(PedidoConflictError, match="No se puede eliminar un pedido"):
        pedidos.borrar_pedido(id_pedido=1, id_sector_jefe=1)


@patch("src.core.services.pedidos.pedidos.repo_pedidos.get_pedido_by_id")
def test_borrar_pedido_otro_sector_403(mock_get_pedido):
    """Verifica que un Jefe no pueda borrar un pedido de otro sector."""
    class MockPedido:
        idSector = 2
        estado_general = EstadoPedido.CONFIRMADO

    mock_get_pedido.return_value = MockPedido()

    with pytest.raises(PedidoForbiddenError):
        pedidos.borrar_pedido(id_pedido=1, id_sector_jefe=5)


@patch("src.core.services.pedidos.pedidos.repo_pedidos.create_pedido_con_solicitudes")
@patch("src.core.services.pedidos.pedidos.Solicitud.existe_duplicado")
@patch("src.core.services.pedidos.pedidos.db")
@patch("src.core.services.pedidos.pedidos.cupos.get_by_sector_y_comida")
@patch("src.core.services.pedidos.pedidos.repo_pedidos.existe_pedido_en_sector_y_fecha")
def test_calculo_regular_y_excepcion(
    mock_existe_pedido,
    mock_get_cupo,
    mock_db,
    mock_existe_duplicado,
    mock_repo_create,
):
    """Verifica que si el cupo es 2 y se piden 3 personas, 2 sean REGULAR y 1 EXCEPCION."""
    mock_existe_pedido.return_value = False

    class MockCupo:
        cantComensales = 2

    mock_get_cupo.return_value = MockCupo()

    class MockPersona:
        isActive = True
        idTipoMenu = 1
        idPersonal = 99
        idTipoPersonal = 1

    mock_db.session.get.return_value = MockPersona()
    mock_existe_duplicado.return_value = False
    mock_repo_create.side_effect = lambda pedido, solicitudes: pedido

    with patch("src.core.services.pedidos.pedidos.validar_sector_personal"):
        pedidos.crear_pedido(
            id_jefe=1,
            id_sector=1,
            fecha_desde=date(2026, 6, 29),
            periodicidad="diaria",
            comidas={"1": [10, 11, 12]},
        )

    _, solicitudes_generadas = mock_repo_create.call_args[0]
    assert len(solicitudes_generadas) == 3
    assert solicitudes_generadas[0].condicionCupo == CondicionCupo.REGULAR
    assert solicitudes_generadas[1].condicionCupo == CondicionCupo.REGULAR
    assert solicitudes_generadas[2].condicionCupo == CondicionCupo.EXCEPCION


@patch("src.core.services.pedidos.pedidos.repo_personal.pertenece_a_sector")
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

    with pytest.raises(PedidoValidationError):
        validar_sector_personal(MockPersona(), id_sector_jefe=1)