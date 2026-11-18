"""Pruebas del service de sectores."""

from dotenv import load_dotenv

load_dotenv()

from unittest.mock import patch

import pytest

from src.core.models.Sector import Sector
from src.core.services.sectores import sector as sector_service
from src.core.services.sectores.sector import SectorError


def test_assert_sector_usable_ok():
    """Un sector activo se puede usar."""
    sector = Sector(idSector=1, nombre="Guardia", isActive=True)

    with patch(
        "src.core.services.sectores.sector.repo_sector.get_by_id",
        return_value=sector,
    ):
        resultado = sector_service.assert_sector_usable(1)

    assert resultado is sector


def test_assert_sector_usable_no_existe():
    """Si el id no existe, lanza SectorError."""
    with patch(
        "src.core.services.sectores.sector.repo_sector.get_by_id",
        return_value=None,
    ):
        with pytest.raises(SectorError, match="no existe"):
            sector_service.assert_sector_usable(999)


def test_assert_sector_usable_inactivo():
    """Un sector inactivo no se puede usar."""
    sector = Sector(idSector=2, nombre="Viejo", isActive=False)

    with patch(
        "src.core.services.sectores.sector.repo_sector.get_by_id",
        return_value=sector,
    ):
        with pytest.raises(SectorError, match="inactivo"):
            sector_service.assert_sector_usable(2)