from datetime import datetime
import pytest
from dotenv import load_dotenv
from sqlalchemy import text
from unittest.mock import patch

load_dotenv()

from src.web import create_app
from src.core.database import db, reset_db
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.TipoMenu import TipoMenu
from src.core.services.personal import personal as service_personal
from src.core.models.Sector import Sector


@pytest.fixture
def app():
    """Inicializa la aplicación y limpia la base antes de cada test."""
    app = create_app()

    with app.app_context():
        # limpieza aislada de las tablas de personal y catalogos relacionados para evitar conflictos con otros tests
        db.session.execute(text("""
            TRUNCATE TABLE "Personal", "TipoPersonal", "TipoMenu", "SectorCompuestoPorPersonal", "Sector" RESTART IDENTITY CASCADE;
        """))
        db.session.commit()

        # precargar catalogos obligatorios necesarios para las claves foraneas
        db.session.add_all([
            TipoPersonal(idTipoPersonal=1, nombre="Fijo"),
            TipoPersonal(idTipoPersonal=2, nombre="Residente"),
        ])

        db.session.add_all([
            TipoMenu(idTipoMenu=1, nombre="General"),
            TipoMenu(idTipoMenu=2, nombre="Vegetariano"),
            TipoMenu(idTipoMenu=3, nombre="Celíaco"),
        ])

        db.session.add(Sector(idSector=1, nombre="Guardia", isActive=True))

        db.session.commit()

        yield app

        db.session.rollback()


def test_create_personal_exitoso(app):
    """Verifica que se cree una persona correctamente cuando los datos son válidos."""
    # ejecutar la accion a traves del servicio
    persona = service_personal.create(
        dni="40123456",
        nombre="Lucía",
        apellido="Gómez",
        id_tipo_personal=1,
        id_tipo_menu=1,
        id_sector=1
    )

    # aserciones sobre el objeto retornado
    assert persona is not None
    assert persona.dni == "40123456"
    assert persona.nombre == "Lucía"
    assert persona.apellido == "Gómez"
    assert persona.isActive is True
    assert persona.idPersonal is not None

    # comprobar que realmente quedo persistido en la base
    persona_en_db = service_personal.get_by_dni("40123456")
    assert persona_en_db is not None
    assert persona_en_db.idPersonal == persona.idPersonal

    sector_asig = service_personal.get_sector_asignado(persona.idPersonal)
    assert sector_asig is not None
    assert sector_asig.idSector == 1

def test_create_personal_dni_duplicado(app):
    """Verifica que el servicio rechace la creación si el DNI ya existe."""
    # crear una primera persona valida
    primera_persona = service_personal.create(
        dni="40123456",
        nombre="Lucía",
        apellido="Gómez",
        id_tipo_personal=1,
        id_tipo_menu=1,
        id_sector=1
    )
    assert primera_persona is not None

    # intentar crear una segunda persona con el mismo DNI pero distintos datos
    persona_duplicada = service_personal.create(
        dni="40123456",
        nombre="Martín",
        apellido="López",
        id_tipo_personal=2,
        id_tipo_menu=2,
    )

    # la logica de negocio debe rechazar la operación retornando None
    assert persona_duplicada is None

    # comprobar que en la base de datos sigue existiendo unicamente el registro original
    persona_en_db = service_personal.get_by_dni("40123456")
    assert persona_en_db is not None
    assert persona_en_db.nombre == "Lucía"
    assert persona_en_db.apellido == "Gómez"

def test_update_personal_exitoso(app):
    """Verifica la actualización correcta de los datos de una persona."""
    # crear persona base
    persona = service_personal.create(
        dni="30111222",
        nombre="Carlos",
        apellido="Pérez",
        id_tipo_personal=1,
        id_tipo_menu=1,
        id_sector=1
    )
    assert persona is not None

    # modificar datos (apellido y menu)
    persona_modificada = service_personal.update(
        id_personal=persona.idPersonal,
        dni="30111222",
        nombre="Carlos",
        apellido="Pérez Ramos",
        id_tipo_personal=1,
        id_tipo_menu=2,  # cambia a Vegetariano
        id_sector=1  # mantiene el mismo sector
    )

    # comprobar retorno y persistencia
    assert persona_modificada is not None
    assert persona_modificada.apellido == "Pérez Ramos"
    assert persona_modificada.idTipoMenu == 2

    # verificar que el cambio quedo persistido en la base
    persona_db = service_personal.get_by_id(persona.idPersonal)
    assert persona_db.apellido == "Pérez Ramos"
    assert persona_db.idTipoMenu == 2


def test_set_active(app):
    """Verifica la baja lógica y posterior reactivación del personal."""
    # crear persona activa por defecto
    persona = service_personal.create(
        dni="35999888",
        nombre="Ana",
        apellido="Sosa",
        id_tipo_personal=2,
        id_tipo_menu=3,
        id_sector=1
    )
    assert persona.isActive is True

    # desactivar (baja logica)
    persona_inactiva = service_personal.set_active(persona.idPersonal, is_active=False)
    assert persona_inactiva is not None
    assert persona_inactiva.isActive is False

    # verificar que sigue existiendo en la base (no se borro fisicamente)
    persona_db = service_personal.get_by_id(persona.idPersonal)
    assert persona_db is not None
    assert persona_db.isActive is False

    # reactivar
    persona_reactivada = service_personal.set_active(persona.idPersonal, is_active=True)
    assert persona_reactivada is not None
    assert persona_reactivada.isActive is True


def test_create_personal_fijo_sin_sector_lanza_error(app):
    """Regla de negocio: El Personal Fijo exige obligatoriamente un sector."""
    with pytest.raises(ValueError, match="requiere un sector asignado"):
        service_personal.create(
            dni="41000111",
            nombre="Esteban",
            apellido="Quito",
            id_tipo_personal=1,  # Fijo
            id_tipo_menu=1,
            id_sector=None,
        )


def test_create_personal_residente_no_tiene_sector(app):
    """Regla de negocio: El Residente no tiene sector asignado aunque se intente enviar uno."""
    persona = service_personal.create(
        dni="42000222",
        nombre="Camila",
        apellido="Ríos",
        id_tipo_personal=2,  # Residente
        id_tipo_menu=1,
        id_sector=1,  # Intentamos mandarle sector
    )
    assert persona is not None

    # Debe persistir sin asociacion en la tabla intermedia
    sector = service_personal.get_sector_asignado(persona.idPersonal)
    assert sector is None


def test_transicion_fijo_a_residente_remueve_sector(app):
    """Transición: Si un Fijo pasa a ser Residente, se debe eliminar su sector asignado."""
    persona = service_personal.create(
        dni="43000333",
        nombre="Franco",
        apellido="Armani",
        id_tipo_personal=1,  # Fijo
        id_tipo_menu=1,
        id_sector=1,
    )
    assert service_personal.get_sector_asignado(persona.idPersonal) is not None

    # Lo actualizamos a Residente
    service_personal.update(
        id_personal=persona.idPersonal,
        dni="43000333",
        nombre="Franco",
        apellido="Armani",
        id_tipo_personal=2,  # Residente
        id_tipo_menu=1,
        id_sector=None,
    )

    sector_despues = service_personal.get_sector_asignado(persona.idPersonal)
    assert sector_despues is None


def test_transicion_residente_a_fijo_asigna_sector(app):
    """Transición: Si un Residente pasa a Fijo, se le asocia el nuevo sector."""
    persona = service_personal.create(
        dni="44000444",
        nombre="Enzo",
        apellido="Fernández",
        id_tipo_personal=2,  # Residente
        id_tipo_menu=1,
    )
    assert service_personal.get_sector_asignado(persona.idPersonal) is None

    # Lo actualizamos a Fijo con sector
    service_personal.update(
        id_personal=persona.idPersonal,
        dni="44000444",
        nombre="Enzo",
        apellido="Fernández",
        id_tipo_personal=1,  # Fijo
        id_tipo_menu=1,
        id_sector=1,
    )

    sector_despues = service_personal.get_sector_asignado(persona.idPersonal)
    assert sector_despues is not None
    assert sector_despues.idSector == 1

def test_eliminar_personal_sin_historial(app):
    """Prueba que si la persona NO tiene historial, se oculta físicamente (Soft Delete)."""
    # crear persona
    persona = service_personal.create(
        dni="55555555",
        nombre="Fisico",
        apellido="Borrado",
        id_tipo_personal=1,
        id_tipo_menu=1,
        id_sector=1
    )
    id_pers = persona.idPersonal

    # ejecutar eliminación
    exito, accion = service_personal.eliminar_personal(id_pers)

    # verificaciones de la lógica
    assert exito is True
    assert accion == "eliminado"
    
    # verificación en base de datos: Ya no debe ser accesible por las funciones normales
    assert service_personal.get_by_id(id_pers) is None
    
    # comprobación de integridad: Verificamos con SQL puro que sigue en la BD pero oculta
    with app.app_context():
        resultado = db.session.execute(
            text('SELECT is_deleted FROM "Personal" WHERE "idPersonal" = :id'),
            {"id": id_pers}
        ).fetchone()
        assert resultado is not None
        assert resultado[0] is True  # is_deleted es True


@patch("src.core.services.personal.personal.repo_personal.tiene_historial")
def test_eliminar_personal_con_historial(mock_tiene_historial, app):
    """Prueba que si la persona TIENE historial, solo se desactiva (Baja lógica)."""
    # Forzamos a que el sistema crea que tiene historial para no tener que crear pedidos falsos
    mock_tiene_historial.return_value = True

    # crear persona
    persona = service_personal.create(
        dni="66666666",
        nombre="Logica",
        apellido="Baja",
        id_tipo_personal=1,
        id_tipo_menu=1,
        id_sector=1
    )
    id_pers = persona.idPersonal

    # ejecutar eliminación (con historial forzado)
    exito, accion = service_personal.eliminar_personal(id_pers)

    # verificaciones de la lógica
    assert exito is True
    assert accion == "inactivado"
    
    # verificación en base de datos: A diferencia del borrado, acá SÍ debe aparecer, pero inactiva
    persona_db = service_personal.get_by_id(id_pers)
    assert persona_db is not None
    assert persona_db.isActive is False
    
    # comprobación de integridad
    with app.app_context():
        resultado = db.session.execute(
            text('SELECT is_deleted FROM "Personal" WHERE "idPersonal" = :id'),
            {"id": id_pers}
        ).fetchone()
        assert resultado[0] is False  # is_deleted es False

def test_search_alcance_jefe_sector(app):
    """Verifica que si se pasa sector_forzado_jefe, devuelva sus fijos y todos los residentes."""
    # crear Fijo en Sector 1 (Guardia) -> EL JEFE DEL SECTOR 1 LO DEBE VER
    service_personal.create(dni="11111111", nombre="Fijo", apellido="Guardia", id_tipo_personal=1, id_tipo_menu=1, id_sector=1)
    
    # crear Fijo en Sector 2 (Ej: Pediatría) -> EL JEFE DEL SECTOR 1 NO LO DEBE VER
    db.session.add(Sector(idSector=2, nombre="Pediatría", isActive=True))
    db.session.commit()
    service_personal.create(dni="22222222", nombre="Fijo", apellido="Pediatria", id_tipo_personal=1, id_tipo_menu=1, id_sector=2)
    
    # crear Residente (Sector None) -> EL JEFE DEL SECTOR 1 LO DEBE VER (Todos ven residentes)
    service_personal.create(dni="33333333", nombre="Resi", apellido="Dente", id_tipo_personal=2, id_tipo_menu=1)

    # ejecutamos la búsqueda forzando el sector 1 (simulando al Jefe de Guardia)
    resultado_paginado = service_personal.search(sector_forzado_jefe=1)
    resultados = resultado_paginado["items"]
    total = resultado_paginado["total"]
    
    #aserciones
    assert total == 2  # debe traer solo 2 personas de las 3 creadas
    dnis_encontrados = [p.dni for p in resultados]
    assert "11111111" in dnis_encontrados # Ve al fijo de Guardia
    assert "33333333" in dnis_encontrados # Ve al residente
    assert "22222222" not in dnis_encontrados # NO ve al fijo de Pediatría