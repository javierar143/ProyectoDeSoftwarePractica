from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from src.core.database import db, reset_db
from src.core.models.PersonalTemporal import PersonalTemporal
from src.core.models.Rol import Rol
from src.core.models.Usuario import Usuario
from src.core.security.password import hash_password

import pytest

from src.web import create_app
from src.core.security.session import (
    set_authenticated_user,
    get_authenticated_user_id,
    clear_session,
    is_authenticated,
    require_authentication,
)


@pytest.fixture(scope="module")
def app():
    """Crea la aplicación y prepara la base de datos para los tests."""
    app = create_app()

    with app.app_context():
        reset_db()
        yield app

@pytest.fixture(scope="module")
def usuario(app):
    """Crea el usuario necesario para probar el inicio de sesión."""
    rol = Rol(
        idRol=1,
        nombre="Administrador",
    )

    personal = PersonalTemporal(
        idPersonal=1,
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
    db.session.add(usuario)
    db.session.commit()

    return usuario

def test_session_user(app):
    with app.test_request_context():
        set_authenticated_user(10)

        user_id = get_authenticated_user_id()

        assert user_id == 10


def test_clear_session(app):
    with app.test_request_context():
        set_authenticated_user(10)

        clear_session()

        user_id = get_authenticated_user_id()

        assert user_id is None

def test_logout(app):
    client = app.test_client()

    with client.session_transaction() as session:
        session["user_id"] = 10

    response = client.post("/logout")

    assert response.status_code == 200

    with client.session_transaction() as session:
        assert "user_id" not in session

def test_login_creates_session(app, usuario):
    client = app.test_client()

    response = client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "Test1234",
        },
    )

    assert response.status_code == 200

    with client.session_transaction() as session:
        assert session["user_id"] == 1

def test_is_authenticated(app):
    with app.test_request_context():
        set_authenticated_user(1)

        assert is_authenticated() is True

def test_require_authentication(app):
    with app.test_request_context():
        set_authenticated_user(1)

        require_authentication()