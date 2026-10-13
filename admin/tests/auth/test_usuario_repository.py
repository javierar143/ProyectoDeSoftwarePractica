
"""Pruebas del repositorio de usuarios."""

import pytest

from src.web import create_app
from src.core.database import reset_db
from src.core.repositories.usuarios.usuario import get_by_email, get_by_id


@pytest.fixture(scope="module")
def app():
    """Crea la aplicación y carga los datos iniciales."""
    app = create_app()

    with app.app_context():
        reset_db()
        yield app


def test_get_by_id_usuario_inexistente(app):
    """Devuelve None cuando el identificador no existe."""
    assert get_by_id(999999) is None


def test_get_by_id_usuario_existente(app):
    """Busca un usuario creado por los datos iniciales."""
    usuario = get_by_email("admin@temporal.com")

    assert usuario is not None
    usuario_buscado = get_by_id(usuario.id_user)

    assert usuario_buscado is not None
    assert usuario_buscado.email == "admin@temporal.com"


def test_get_by_email_usuario_inexistente(app):
    """Devuelve None cuando el correo no existe."""
    usuario = get_by_email("noexiste@example.com")

    assert usuario is None


def test_get_by_email_usuario_existente(app):
    """Busca un usuario existente por su correo."""
    usuario = get_by_email("admin@temporal.com")

    assert usuario is not None
    assert usuario.email == "admin@temporal.com"
