
"""Pruebas para la creación de usuarios."""

from datetime import datetime

import pytest

from src.web import create_app
from src.core.database import db, reset_db
from src.core.models.Usuario import Usuario
from src.core.models.Personal import Personal
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.TipoMenu import TipoMenu
from src.core.repositories.usuarios.usuario import create, get_by_email
from src.core.security.password import hash_password


@pytest.fixture
def app():
    """Crea la aplicación y reinicia la base para la prueba."""
    app = create_app()

    with app.app_context():
        reset_db()
        yield app


def test_create_user(app):
    """Verifica que se pueda guardar un usuario nuevo."""
    tipo_personal = db.session.query(TipoPersonal).filter_by(
        nombre="Fijo"
    ).one()
    tipo_menu = db.session.query(TipoMenu).filter_by(
        nombre="General"
    ).one()

    ahora = datetime.now()
    personal = Personal(
        dni="98765432",
        nombre="Test",
        apellido="Usuario",
        isActive=True,
        idTipoPersonal=tipo_personal.idTipoPersonal,
        idTipoMenu=tipo_menu.idTipoMenu,
        inserted_at=ahora,
        updated_at=ahora,
    )
    db.session.add(personal)
    db.session.flush()

    rol = db.session.query(__import__(
        "src.core.models.Rol", fromlist=["Rol"]
    ).Rol).filter_by(nombre="Administrador").one()

    nuevo_usuario = Usuario(
        email="test@example.com",
        alias="test",
        password_hash=hash_password("Test1234"),
        isSystemAdmin=False,
        isActive=True,
        inserted_at=ahora,
        updated_at=ahora,
        idRol=rol.idRol,
        idPersonal=personal.idPersonal,
    )

    usuario_creado = create(nuevo_usuario)
    usuario_buscado = get_by_email("test@example.com")

    assert usuario_creado.email == "test@example.com"
    assert usuario_buscado is not None
    assert usuario_buscado.email == "test@example.com"
