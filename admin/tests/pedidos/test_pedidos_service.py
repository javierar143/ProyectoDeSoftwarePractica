"""Pruebas unitarias para el servicio de pedidos."""

from dotenv import load_dotenv

load_dotenv()

from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch
import pytest

from src.core.models.enums import CondicionCupo, EstadoPedido
from src.core.services.pedidos import pedidos


@patch("src.core.services.pedidos.pedidos.repo_pedidos.create_pedido_con_solicitudes")
@patch("src.core.services.pedidos.pedidos.repo_pedidos.existe_pedido_en_sector_y_fecha")
def test_crear_pedido_duplicado_por_fecha(mock_existe, mock_repo_create):
    """Verifica que si ya hay un pedido para ese sector y fecha aborte con 409 y no persista nada."""
    mock_existe.return_value = True
    fecha_futura = date.today() + timedelta(days=5)

    with pytest.raises(Exception) as exc_info:
        pedidos.crear_pedido(
            id_jefe=1,
            id_sector=1,
            fecha_desde=fecha_futura,
            periodicidad="diaria",
            comidas={"1": [1, 2]},
        )

    assert getattr(exc_info.value, "code", None) == 409
    assert "Ya existe un pedido registrado" in str(exc_info.value.description)
    mock_repo_create.assert_not_called()


@patch("src.core.services.pedidos.pedidos.repo_pedidos.eliminar_pedido")
@patch("src.core.services.pedidos.pedidos.repo_pedidos.get_pedido_by_id")
def test_borrar_pedido_autorizado_falla_409(mock_get_pedido, mock_eliminar):
    """Verifica que no se pueda eliminar un pedido en estado AUTORIZADO (409) ni se llame al repo."""
    mock_get_pedido.return_value = SimpleNamespace(
        idPedido=1,
        idSector=1,
        estado_general=EstadoPedido.AUTORIZADO,
    )

    with pytest.raises(Exception) as exc_info:
        pedidos.borrar_pedido(id_pedido=1, id_sector_jefe=1)

    assert getattr(exc_info.value, "code", None) == 409
    assert "No se puede eliminar un pedido" in str(exc_info.value.description)
    mock_eliminar.assert_not_called()


@patch("src.core.services.pedidos.pedidos.repo_pedidos.eliminar_pedido")
@patch("src.core.services.pedidos.pedidos.repo_pedidos.get_pedido_by_id")
def test_borrar_pedido_otro_sector_403(mock_get_pedido, mock_eliminar):
    """Verifica que un Jefe no pueda borrar un pedido de otro sector (403)."""
    mock_get_pedido.return_value = SimpleNamespace(
        idPedido=1,
        idSector=2,
        estado_general=EstadoPedido.CONFIRMADO,
    )

    with pytest.raises(Exception) as exc_info:
        pedidos.borrar_pedido(id_pedido=1, id_sector_jefe=5)

    assert getattr(exc_info.value, "code", None) == 403
    mock_eliminar.assert_not_called()


@patch("src.core.services.pedidos.pedidos.repo_personal.pertenece_a_sector")
@patch("src.core.services.pedidos.pedidos.repo_pedidos.create_pedido_con_solicitudes")
@patch("src.core.services.pedidos.pedidos.repo_pedidos.existe_solicitud_duplicada")
@patch("src.core.services.pedidos.pedidos.repo_personal.get_by_id")
@patch("src.core.services.pedidos.pedidos.cupos.get_by_sector_y_comida")
@patch("src.core.services.pedidos.pedidos.repo_pedidos.existe_pedido_en_sector_y_fecha")
def test_calculo_regular_y_excepcion(
    mock_existe_pedido,
    mock_get_cupo,
    mock_get_personal,
    mock_existe_duplicado,
    mock_repo_create,
    mock_pertenece_sector,
):
    """
    Verifica que si el cupo es 2 y se piden 3 personas distintas (fijos y residente),
    2 sean REGULAR y 1 EXCEPCION, conservando el idTipoMenu individual de cada persona.
    """
    fecha_futura = date.today() + timedelta(days=7)
    mock_existe_pedido.return_value = False
    mock_get_cupo.return_value = SimpleNamespace(cantComensales=2)
    mock_existe_duplicado.return_value = False
    mock_pertenece_sector.return_value = True

    personas_db = {
        10: SimpleNamespace(
            idPersonal=10,
            isActive=True,
            idTipoMenu=1,
            idTipoPersonal=1,
            tipo_personal=SimpleNamespace(nombre="Personal Fijo"),
        ),
        11: SimpleNamespace(
            idPersonal=11,
            isActive=True,
            idTipoMenu=2,
            idTipoPersonal=1,
            tipo_personal=SimpleNamespace(nombre="Personal Fijo"),
        ),
        12: SimpleNamespace(
            idPersonal=12,
            isActive=True,
            idTipoMenu=3,
            idTipoPersonal=2,
            tipo_personal=SimpleNamespace(nombre="Residente"),
        ),
    }
    mock_get_personal.side_effect = lambda pid: personas_db.get(pid)
    mock_repo_create.side_effect = (
        lambda nuevo_pedido, lista_solicitudes: nuevo_pedido
    )

    pedidos.crear_pedido(
        id_jefe=1,
        id_sector=1,
        fecha_desde=fecha_futura,
        periodicidad="diaria",
        comidas={"1": [10, 11, 12]},
    )

    mock_repo_create.assert_called_once()
    call = mock_repo_create.call_args
    solicitudes_generadas = (
        call.kwargs["lista_solicitudes"]
        if "lista_solicitudes" in call.kwargs
        else call.args[1]
    )

    assert len(solicitudes_generadas) == 3
    por_persona = {s.idPersonal: s for s in solicitudes_generadas}

    assert set(por_persona.keys()) == {10, 11, 12}
    assert por_persona[10].condicionCupo == CondicionCupo.REGULAR
    assert por_persona[10].idTipoMenu == 1
    assert por_persona[11].condicionCupo == CondicionCupo.REGULAR
    assert por_persona[11].idTipoMenu == 2
    assert por_persona[12].condicionCupo == CondicionCupo.EXCEPCION
    assert por_persona[12].idTipoMenu == 3


@patch("src.core.services.pedidos.pedidos.repo_personal.pertenece_a_sector")
@patch("src.core.services.pedidos.pedidos.repo_pedidos.guardar_nuevas_solicitudes")
@patch("src.core.services.pedidos.pedidos.repo_pedidos.limpiar_solicitudes_de_pedido")
@patch("src.core.services.pedidos.pedidos.repo_pedidos.existe_solicitud_duplicada")
@patch("src.core.services.pedidos.pedidos.repo_personal.get_by_id")
@patch("src.core.services.pedidos.pedidos.cupos.get_by_sector_y_comida")
@patch("src.core.services.pedidos.pedidos.repo_pedidos.get_pedido_by_id")
def test_actualizar_pedido_limpia_antes_de_guardar_y_recalcula(
    mock_get_pedido,
    mock_get_cupo,
    mock_get_personal,
    mock_existe_duplicado,
    mock_limpiar,
    mock_guardar_nuevas,
    mock_pertenece_sector,
):
    """
    Verifica que al modificar un pedido confirmado:
    1. Se ejecute limpiar_solicitudes_de_pedido ANTES de guardar_nuevas_solicitudes.
    2. Se recalcule Regular y Excepción según el cupo actual.
    """
    fecha_futura = date.today() + timedelta(days=7)
    orden_ejecucion: list[str] = []

    mock_get_pedido.return_value = SimpleNamespace(
        idPedido=8,
        idSector=1,
        fecha_desde=fecha_futura,
        estado_general=EstadoPedido.CONFIRMADO,
    )
    mock_get_cupo.return_value = SimpleNamespace(cantComensales=1)
    mock_existe_duplicado.return_value = False
    mock_pertenece_sector.return_value = True

    personas_db = {
        10: SimpleNamespace(
            idPersonal=10,
            isActive=True,
            idTipoMenu=1,
            idTipoPersonal=1,
            tipo_personal=SimpleNamespace(nombre="Personal Fijo"),
        ),
        11: SimpleNamespace(
            idPersonal=11,
            isActive=True,
            idTipoMenu=2,
            idTipoPersonal=1,
            tipo_personal=SimpleNamespace(nombre="Personal Fijo"),
        ),
    }
    mock_get_personal.side_effect = lambda pid: personas_db.get(pid)

    def _registrar_limpieza(id_ped):
        orden_ejecucion.append("limpiar")

    def _registrar_guardado(pedido, nuevas):
        orden_ejecucion.append("guardar")
        return pedido

    mock_limpiar.side_effect = _registrar_limpieza
    mock_guardar_nuevas.side_effect = _registrar_guardado

    pedidos.actualizar_pedido(
        id_pedido=8,
        comidas={"1": [10, 11]},
        id_sector_jefe=1,
    )

    assert orden_ejecucion == ["limpiar", "guardar"]
    call = mock_guardar_nuevas.call_args
    nuevas = (
        call.kwargs["nuevas_solicitudes"]
        if "nuevas_solicitudes" in call.kwargs
        else call.args[1]
    )

    por_persona = {s.idPersonal: s for s in nuevas}
    assert por_persona[10].condicionCupo == CondicionCupo.REGULAR
    assert por_persona[11].condicionCupo == CondicionCupo.EXCEPCION


@patch("src.core.services.pedidos.pedidos.repo_personal.pertenece_a_sector")
@patch("src.core.services.pedidos.pedidos.repo_pedidos.get_tipo_personal_by_id")
def test_regla_residente_vs_personal_fijo(mock_get_tipo, mock_pertenece):
    """Verifica que un Residente se acepte en cualquier sector y un Fijo de otro sector falle con 400."""
    from src.core.services.pedidos.pedidos import validar_sector_personal

    persona_mock = SimpleNamespace(
        idPersonal=15, idTipoPersonal=2, tipo_personal=None
    )

    mock_get_tipo.return_value = SimpleNamespace(nombre="Residente")
    mock_pertenece.return_value = False

    validar_sector_personal(persona_mock, id_sector_jefe=1)

    mock_get_tipo.return_value = SimpleNamespace(nombre="Personal Fijo")

    with pytest.raises(Exception) as exc_info:
        validar_sector_personal(persona_mock, id_sector_jefe=1)

    assert getattr(exc_info.value, "code", None) == 400
    assert "personal fijo" in str(exc_info.value.description)

@patch("src.core.services.pedidos.pedidos.repo_personal.pertenece_a_sector")
@patch(
    "src.core.services.pedidos.pedidos.repo_pedidos.create_multiples_pedidos_con_solicitudes"
)
@patch("src.core.services.pedidos.pedidos.repo_pedidos.existe_solicitud_duplicada")
@patch("src.core.services.pedidos.pedidos.repo_personal.get_by_id")
@patch("src.core.services.pedidos.pedidos.cupos.get_by_sector_y_comida")
@patch("src.core.services.pedidos.pedidos.repo_pedidos.existe_pedido_en_sector_y_fecha")
def test_crear_pedido_semanal_genera_un_pedido_por_dia(
    mock_existe_pedido,
    mock_get_cupo,
    mock_get_personal,
    mock_existe_duplicado,
    mock_repo_multiples,
    mock_pertenece_sector,
):
    """Verifica que un pedido semanal genere 7 pedidos diarios con sus solicitudes por fecha."""
    fecha_inicio = date(2026, 11, 23)
    mock_existe_pedido.return_value = False
    mock_get_cupo.return_value = SimpleNamespace(cantComensales=2)
    mock_existe_duplicado.return_value = False
    mock_pertenece_sector.return_value = True
    mock_get_personal.return_value = SimpleNamespace(
        idPersonal=10,
        isActive=True,
        idTipoMenu=1,
        idTipoPersonal=1,
        tipo_personal=SimpleNamespace(nombre="Personal Fijo"),
    )
    mock_repo_multiples.side_effect = lambda pares: [p for p, _ in pares]

    pedidos.crear_pedido(
        id_jefe=1,
        id_sector=1,
        fecha_desde=fecha_inicio,
        periodicidad="semanal",
        comidas={"1": [10]},
    )

    mock_repo_multiples.assert_called_once()
    pares = mock_repo_multiples.call_args.args[0]
    assert len(pares) == 7

    for idx, (pedido_dia, solicitudes_dia) in enumerate(pares):
        fecha_esperada = fecha_inicio + timedelta(days=idx)
        assert pedido_dia.fecha_desde == fecha_esperada
        assert pedido_dia.fecha_hasta == fecha_esperada
        assert len(solicitudes_dia) == 1
        assert solicitudes_dia[0].fecha_vianda == fecha_esperada
        assert solicitudes_dia[0].condicionCupo == CondicionCupo.REGULAR

@patch(
    "src.core.services.pedidos.pedidos.repo_pedidos.create_multiples_pedidos_con_solicitudes"
)
@patch("src.core.services.pedidos.pedidos.repo_pedidos.create_pedido_con_solicitudes")
@patch("src.core.services.pedidos.pedidos.repo_pedidos.existe_pedido_en_sector_y_fecha")
def test_crear_pedido_semanal_conflicto_en_dia_intermedio_409(
    mock_existe_pedido,
    mock_repo_create_uno,
    mock_repo_create_multiples,
):
    """Verifica que si uno de los días del rango semanal ya tiene pedido, aborte con 409 y no guarde nada."""
    fecha_inicio = date(2026, 11, 23)
    fecha_ocupada = fecha_inicio + timedelta(days=2)

    mock_existe_pedido.side_effect = (
        lambda id_sector, fecha: fecha == fecha_ocupada
    )

    with pytest.raises(Exception) as exc_info:
        pedidos.crear_pedido(
            id_jefe=1,
            id_sector=1,
            fecha_desde=fecha_inicio,
            periodicidad="semanal",
            comidas={"1": [10]},
        )

    assert getattr(exc_info.value, "code", None) == 409
    assert fecha_ocupada.isoformat() in str(exc_info.value.description)
    mock_repo_create_uno.assert_not_called()
    mock_repo_create_multiples.assert_not_called()