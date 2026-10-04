from dotenv import load_dotenv

load_dotenv()

import pytest

from src.web import create_app
from src.core.security.session import (
    set_authenticated_user,
    get_authenticated_user_id,
    clear_session,
    is_authenticated,
    require_authentication,
)


@pytest.fixture
def app():
    app = create_app()
    app.app_context().push()
    return app


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

def test_login_creates_session(app):
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