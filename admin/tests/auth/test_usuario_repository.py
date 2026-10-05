from datetime import datetime

import pytest
from dotenv import load_dotenv

load_dotenv()

from src.web import create_app
from src.core.database import db, reset_db
from src.core.models.Usuario import Usuario
from src.core.models.Rol import Rol
from src.core.models.PersonalTemporal import PersonalTemporal
from src.core.security.password import hash_password
from src.core.repositories.usuarios.usuario import get_by_email, get_by_id, create


@pytest.fixture(scope="module")
def app():
    app = create_app()
    app.app_context().push()
    reset_db()
    return app


@pytest.fixture(scope="module")
def usuario_existente(app):
    rol = Rol(
        idRol=1,
        nombre="Administrador"
    )

    personal = PersonalTemporal(
        idPersonal=1
    )

    usuario = Usuario(
        id_user=1,
        email="test@example.com",
        alias="test",
        password_hash=hash_password("Test1234"),
        isSystemAdmin=True,
        isActive=True,
        updated_at=datetime.now(),
        inserted_at=datetime.now(),
        idRol=1,
        idPersonal=1,
    )

    db.session.add(rol)
    db.session.add(personal)
    db.session.flush()

    create(usuario)

    return usuario


def test_get_by_id_usuario_inexistente(app):
    usuario = get_by_id(999)

    assert usuario is None


def test_get_by_id_usuario_existente(app, usuario_existente):
    usuario_buscado = get_by_id(usuario_existente.id_user)

    assert usuario_buscado is not None
    assert usuario_buscado.email == "test@example.com"


def test_get_by_email_usuario_inexistente(app):
    usuario = get_by_email("noexiste@example.com")

    assert usuario is None


def test_get_by_email_usuario_existente(app, usuario_existente):
    usuario_buscado = get_by_email(usuario_existente.email)

    assert usuario_buscado is not None
    assert usuario_buscado.id_user == 1
    assert usuario_buscado.email == "test@example.com"