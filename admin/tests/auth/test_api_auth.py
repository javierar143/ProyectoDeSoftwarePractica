"""Pruebas de autenticación de la API."""
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

import pytest


from src.web import create_app
from src.core.database import db, reset_db
from src.core.models.Personal import Personal
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.TipoMenu import TipoMenu
from src.core.models.Rol import Rol
from src.core.models.Usuario import Usuario
from src.core.security.password import hash_password



@pytest.fixture(scope="module")
def app():
    """Crea la aplicación Flask para las pruebas."""
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



def test_api_login(app, usuario):
    """Verifica que el login API genere un token."""
    client = app.test_client()

    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@temporal.com",
            "password": "1234",
        },
    )

    assert response.status_code == 200
    assert "token" in response.json


def test_api_login_credenciales_invalidas(app, usuario):
    """Verifica que credenciales inválidas sean rechazadas."""
    client = app.test_client()

    response = client.post(
        "/api/auth/login",
        json={
            "email": "api@test.com",
            "password": "PasswordIncorrecto",
        },
    )

    assert response.status_code == 401


def test_api_me(app, usuario):
    """Verifica que /me devuelva el usuario autenticado."""
    client = app.test_client()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@temporal.com",
            "password": "1234",
        },
    )

    token = login_response.json["token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json["id"] == usuario.id_user
    assert response.json["email"] == usuario.email


def test_api_me_sin_token(app):
    """Verifica que /me rechace una petición sin token."""
    client = app.test_client()

    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_api_logout(app, usuario):
    """Verifica que logout revoque el token."""
    client = app.test_client()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@temporal.com",
            "password": "1234",
        },
    )

    token = login_response.json["token"]

    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 401