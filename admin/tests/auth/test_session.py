"""Pruebas de la gestión de sesiones y autenticación web."""

import pytest

from dotenv import load_dotenv

load_dotenv()

from src.web import create_app
from src.core.database import reset_db
from src.core.security.session import (
    set_authenticated_user,
    get_authenticated_user_id,
    clear_session,
    is_authenticated,
    require_authentication,
)


@pytest.fixture(scope="module")
def app():
    """Crea la aplicación y prepara la base de datos para las pruebas."""
    app = create_app()

    with app.app_context():
        reset_db()
        yield app


@pytest.fixture(scope="module")
def usuario(app):
    """Obtiene el usuario administrador creado por los datos iniciales."""
    from src.core.repositories.usuarios import usuario as usuario_repo

    usuario_existente = usuario_repo.get_by_email("admin@temporal.com")

    assert usuario_existente is not None

    return usuario_existente


def test_session_user(app):
    """Comprueba que se almacene el identificador del usuario."""
    with app.test_request_context():
        set_authenticated_user(10)

        user_id = get_authenticated_user_id()

        assert user_id == 10


def test_clear_session(app):
    """Comprueba que se elimine el identificador de la sesión."""
    with app.test_request_context():
        set_authenticated_user(10)

        clear_session()

        user_id = get_authenticated_user_id()

        assert user_id is None


def test_logout(app):
    """Comprueba que cerrar sesión elimine al usuario autenticado."""
    client = app.test_client()

    with client.session_transaction() as session:
        session["user_id"] = 10

    response = client.post("/logout")

    assert response.status_code == 302

    with client.session_transaction() as session:
        assert "user_id" not in session


def test_login_creates_session(app, usuario):
    """Comprueba que iniciar sesión cree la sesión autenticada."""
    client = app.test_client()

    response = client.post(
        "/login",
        data={
            "email": usuario.email,
            "password": "1234",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with client.session_transaction() as session:
        assert session["user_id"] == usuario.id_user


def test_is_authenticated(app):
    """Comprueba que se reconozca una sesión autenticada."""
    with app.test_request_context():
        set_authenticated_user(1)

        assert is_authenticated() is True


def test_require_authentication(app):
    """Comprueba el comportamiento de la función de autenticación."""
    with app.test_request_context():
        set_authenticated_user(1)

        require_authentication()

