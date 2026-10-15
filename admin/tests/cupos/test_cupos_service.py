"""Pruebas unitarias para el servicio de cupos."""

from dotenv import load_dotenv

load_dotenv()

from unittest.mock import patch
import pytest

from src.core.services.cupos import cupos
from src.core.services.cupos.cupos import CupoNotFoundError, CupoServiceError


from types import SimpleNamespace


@patch("src.core.services.cupos.cupos.repo_sector.get_by_id")
@patch("src.core.services.cupos.cupos.repo_cupos.create")
@patch("src.core.services.cupos.cupos.repo_cupos.get_by_sector_y_comida")
def test_crear_cupo_exitoso(mock_get_existente, mock_repo_create, mock_get_sector):
    """Verifica que se cree un cupo cuando los datos son válidos."""
    mock_get_sector.return_value = SimpleNamespace(isActive=True)
    mock_get_existente.return_value = None
    mock_repo_create.side_effect = lambda nuevo_cupo: nuevo_cupo

    cupo = cupos.create(id_sector=1, id_tipo_comida=1, cant_comensales=10)

    assert cupo.cantComensales == 10
    assert cupo.idSector == 1
    assert cupo.idTipoComida == 1


@patch("src.core.services.cupos.cupos.repo_sector.get_by_id")
@patch("src.core.services.cupos.cupos.repo_cupos.get_by_sector_y_comida")
def test_crear_cupo_duplicado(mock_get_existente, mock_get_sector):
    """Verifica que rechace crear un cupo si ya existe para ese sector y comida."""
    mock_get_sector.return_value = SimpleNamespace(isActive=True)

    class MockCupo:
        idCupo = 99

    mock_get_existente.return_value = MockCupo()

    with pytest.raises(CupoServiceError, match="Ya existe un cupo vigente"):
        cupos.create(id_sector=1, id_tipo_comida=1, cant_comensales=10)


@patch("src.core.services.cupos.cupos.repo_sector.get_by_id")
def test_crear_cupo_sector_inactivo(mock_get_sector):
    """Verifica que rechace crear un cupo para un sector inexistente o inactivo."""
    mock_get_sector.return_value = SimpleNamespace(isActive=False)

    with pytest.raises(CupoServiceError, match="inactivo"):
        cupos.create(id_sector=1, id_tipo_comida=1, cant_comensales=10)


def test_crear_cupo_cantidad_invalida():
    """Verifica que rechace cantidades menores o iguales a cero."""
    with pytest.raises(CupoServiceError, match="mayor a cero"):
        cupos.create(id_sector=1, id_tipo_comida=1, cant_comensales=-5)


@patch("src.core.services.cupos.cupos.repo_cupos.get_by_sector_y_comida")
def test_crear_cupo_duplicado(mock_get_existente):
    """Verifica que rechace crear un cupo si ya existe para ese sector y comida."""
    class MockCupo:
        idCupo = 99

    mock_get_existente.return_value = MockCupo()

    with pytest.raises(CupoServiceError, match="Ya existe un cupo vigente"):
        cupos.create(id_sector=1, id_tipo_comida=1, cant_comensales=10)


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
    """Verifica que lance CupoNotFoundError si el cupo no existe."""
    mock_get_by_id.return_value = None

    with pytest.raises(CupoNotFoundError):
        cupos.obtener_por_id(999)