from datetime import datetime
import pytest
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

from src.web import create_app
from src.core.database import db
from src.core.models.Personal import Personal
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.TipoMenu import TipoMenu
from src.core.repositories.personal import personal as repo_personal
from src.core.models.Sector import Sector


@pytest.fixture
def app():
    """Inicializa la app y asegura un entorno limpio para pruebas de repositorio."""
    app = create_app()

    with app.app_context():
        db.session.execute(text("""
            TRUNCATE TABLE "Personal", "TipoPersonal", "TipoMenu", "SectorCompuestoPorPersonal", "Sector" RESTART IDENTITY CASCADE;
        """))
        db.session.commit()

        # precarga de catalogos base
        db.session.add_all([
            TipoPersonal(nombre="Fijo"),
            TipoPersonal(nombre="Residente"),
            TipoMenu(nombre="General"),
            TipoMenu(nombre="Vegetariano"),
            TipoMenu(nombre="Celíaco"),
        ])
        db.session.commit()

        yield app

        db.session.rollback()


def test_repo_create_and_get_by_id(app):
    """Verifica que el repositorio inserte y recupere por ID correctamente."""
    persona = Personal(
        dni="11223344",
        nombre="Julián",
        apellido="Álvarez",
        idTipoPersonal=1,
        idTipoMenu=1,
        isActive=True,
        inserted_at=datetime.now(),
        updated_at=datetime.now(),
    )
    creada = repo_personal.create(persona)

    assert creada.idPersonal is not None

    recuperada = repo_personal.get_by_id(creada.idPersonal)
    assert recuperada is not None
    assert recuperada.dni == "11223344"
    assert recuperada.nombre == "Julián"


def test_repo_get_all_filtrado_activos(app):
    """Verifica el filtrado de solo activos en get_all."""
    ahora = datetime.now()
    p1 = Personal(
        dni="10000001",
        nombre="Ana",
        apellido="Pérez",
        idTipoPersonal=1,
        idTipoMenu=1,
        isActive=True,
        inserted_at=ahora,
        updated_at=ahora,
    )
    p2 = Personal(
        dni="10000002",
        nombre="Beto",
        apellido="Gómez",
        idTipoPersonal=2,
        idTipoMenu=2,
        isActive=False,
        inserted_at=ahora,
        updated_at=ahora,
    )
    repo_personal.create(p1)
    repo_personal.create(p2)

    todos = repo_personal.get_all(solo_activos=False)
    assert len(todos) == 2

    solo_activos = repo_personal.get_all(solo_activos=True)
    assert len(solo_activos) == 1
    assert solo_activos[0].dni == "10000001"


def test_repo_catalogos(app):
    """Verifica la recuperación de los catálogos de tipos de personal y menú."""
    tipos_p = repo_personal.get_tipos_personal()
    tipos_m = repo_personal.get_tipos_menu()

    assert len(tipos_p) == 2
    assert len(tipos_m) == 3

def test_repo_catalogos_sectores(app):
    """Verifica la recuperación únicamente de sectores activos."""
    s1 = Sector(nombre="Guardia", isActive=True)
    s2 = Sector(nombre="Inactivo", isActive=False)
    db.session.add_all([s1, s2])
    db.session.commit()

    sectores = repo_personal.get_sectores()
    assert len(sectores) == 1
    assert sectores[0].nombre == "Guardia"


def test_repo_set_and_get_sector_asignado(app):
    """Verifica la asignación, consulta y posterior desasignación de sector en la tabla intermedia."""
    sector = Sector(nombre="Cirugía", isActive=True)
    db.session.add(sector)
    db.session.commit()

    persona = Personal(
        dni="22334455",
        nombre="Martín",
        apellido="Palermo",
        idTipoPersonal=1,
        idTipoMenu=1,
        isActive=True,
        inserted_at=datetime.now(),
        updated_at=datetime.now(),
    )
    creada = repo_personal.create(persona)

    # Asignar sector y verificar recuperación
    repo_personal.set_sector(creada.idPersonal, sector.idSector)
    asignado = repo_personal.get_sector_asignado(creada.idPersonal)
    assert asignado is not None
    assert asignado.idSector == sector.idSector
    assert asignado.nombre == "Cirugía"

    # Desasignar pasando None y comprobar que no quede registro
    repo_personal.set_sector(creada.idPersonal, None)
    asignado_despues = repo_personal.get_sector_asignado(creada.idPersonal)
    assert asignado_despues is None