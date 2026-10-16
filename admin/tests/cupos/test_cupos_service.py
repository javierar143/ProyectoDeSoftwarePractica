"""Pruebas unitarias para el servicio de cupos."""

from dotenv import load_dotenv

load_dotenv()

from types import SimpleNamespace
from unittest.mock import patch
import pytest

from src.core.services.cupos import cupos


@patch("src.core.services.cupos.cupos.repo_sector.get_by_id")
@patch("src.core.services.cupos.cupos.repo_cupos.create")
@patch("src.core.services.cupos.cupos.repo_cupos.get_by_sector_y_comida")
def test_crear_cupo_exitoso(
    mock_get_existente, mock_repo_create, mock_get_sector
):
    """Verifica que se cree un cupo activo cuando los datos son válidos."""
    mock_get_sector.return_value = SimpleNamespace(isActive=True)
    mock_get_existente.return_value = None
    mock_repo_create.side_effect = lambda nuevo_cupo: nuevo_cupo

    cupo = cupos.create(id_sector=1, id_tipo_comida=1, cant_comensales=10)

    assert cupo.cantComensales == 10
    assert cupo.idSector == 1
    assert cupo.idTipoComida == 1
    assert cupo.activo is True


@patch("src.core.services.cupos.cupos.repo_sector.get_by_id")
@patch("src.core.services.cupos.cupos.repo_cupos.get_by_sector_y_comida")
def test_crear_cupo_duplicado(mock_get_existente, mock_get_sector):
    """Verifica que rechace con 400 crear un cupo si ya existe uno vigente para ese sector y comida."""
    mock_get_sector.return_value = SimpleNamespace(isActive=True)

    class MockCupo:
        idCupo = 99

    mock_get_existente.return_value = MockCupo()

    with pytest.raises(Exception) as exc_info:
        cupos.create(id_sector=1, id_tipo_comida=1, cant_comensales=10)

    assert getattr(exc_info.value, "code", None) == 400
    assert "Ya existe un cupo vigente" in str(exc_info.value.description)


@patch("src.core.services.cupos.cupos.repo_sector.get_by_id")
def test_crear_cupo_sector_inactivo(mock_get_sector):
    """Verifica que rechace con 400 crear un cupo para un sector inexistente o inactivo."""
    mock_get_sector.return_value = SimpleNamespace(isActive=False)

    with pytest.raises(Exception) as exc_info:
        cupos.create(id_sector=1, id_tipo_comida=1, cant_comensales=10)

    assert getattr(exc_info.value, "code", None) == 400
    assert "inactivo" in str(exc_info.value.description)


def test_crear_cupo_cantidad_invalida():
    """Verifica que rechace con 400 cantidades menores o iguales a cero."""
    with pytest.raises(Exception) as exc_info:
        cupos.create(id_sector=1, id_tipo_comida=1, cant_comensales=-5)

    assert getattr(exc_info.value, "code", None) == 400
    assert "mayor a cero" in str(exc_info.value.description)


@patch("src.core.services.cupos.cupos.obtener_configuracion")
@patch("src.core.services.cupos.cupos.repo_cupos.list_cupos")
def test_listar_cupos_usa_configuracion_global(mock_list, mock_config):
    """Verifica que el listado de cupos respete la paginación global del sistema."""

    class MockConfig:
        elementos_por_pagina = 15

    mock_config.return_value = MockConfig()
    mock_list.return_value = ([], 0)

    items, total, per_page = cupos.listar(page=1)

    assert per_page == 15
    mock_list.assert_called_once_with(
        id_sector=None, id_tipo_comida=None, orden="asc", page=1, per_page=15
    )


@patch("src.core.services.cupos.cupos.repo_cupos.get_by_id")
def test_obtener_cupo_inexistente(mock_get_by_id):
    """Verifica que aborte con 404 si el cupo no existe."""
    mock_get_by_id.return_value = None

    with pytest.raises(Exception) as exc_info:
        cupos.obtener_por_id(999)

    assert getattr(exc_info.value, "code", None) == 404


@patch("src.core.services.cupos.cupos.repo_cupos.soft_delete")
@patch("src.core.services.cupos.cupos.repo_cupos.get_by_id")
def test_eliminar_cupo_baja_logica(mock_get_by_id, mock_soft_delete):
    """Verifica que eliminar un cupo realice la baja lógica a través del repositorio."""
    cupo_mock = SimpleNamespace(
        idCupo=3, idSector=1, idTipoComida=1, cantComensales=10, activo=True
    )
    mock_get_by_id.return_value = cupo_mock

    def _inactivar(c):
        c.activo = False
        return c

    mock_soft_delete.side_effect = _inactivar

    eliminado = cupos.eliminar(3)
    assert eliminado.activo is False
    mock_soft_delete.assert_called_once_with(cupo_mock)