from datetime import datetime
import pytest
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

from src.web import create_app
from src.core.database import db, reset_db
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.TipoMenu import TipoMenu
from src.core.services.personal import personal as service_personal


@pytest.fixture
def app():
    """Inicializa la aplicación y limpia la base antes de cada test."""
    app = create_app()

    with app.app_context():
        # limpieza aislada de las tablas de personal y catalogos relacionados para evitar conflictos con otros tests
        db.session.execute(text("""
            TRUNCATE TABLE "Personal", "TipoPersonal", "TipoMenu" RESTART IDENTITY CASCADE;
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

def test_create_personal_dni_duplicado(app):
    """Verifica que el servicio rechace la creación si el DNI ya existe."""
    # crear una primera persona valida
    primera_persona = service_personal.create(
        dni="40123456",
        nombre="Lucía",
        apellido="Gómez",
        id_tipo_personal=1,
        id_tipo_menu=1,
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
    )

    # comprobar retorno y persistencia
    assert persona_modificada is not None
    assert persona_modificada.apellido == "Pérez Ramos"
    assert persona_modificada.idTipoMenu == 2

    # verificar que el cambio quedo persistido en la base
    persona_db = service_personal.get_by_id(persona.idPersonal)
    assert persona_db.apellido == "Pérez Ramos"
    assert persona_db.idTipoMenu == 2


def test_set_active_soft_delete(app):
    """Verifica la baja lógica y posterior reactivación del personal."""
    # crear persona activa por defecto
    persona = service_personal.create(
        dni="35999888",
        nombre="Ana",
        apellido="Sosa",
        id_tipo_personal=2,
        id_tipo_menu=3,
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