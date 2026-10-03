from dotenv import load_dotenv
load_dotenv()

from src.core.repositories.usuario import get_by_email
from src.web import create_app


def test_get_by_email_usuario_inexistente(app):
    usuario = get_by_email("noexiste@example.com")

    assert usuario is None


import pytest


@pytest.fixture
def app():
    app = create_app()
    app.app_context().push()