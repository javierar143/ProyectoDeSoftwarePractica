from dotenv import load_dotenv

load_dotenv()

import pytest

from src.web import create_app

from src.core.database import db
from src.core.models.Usuario import Usuario
from src.core.security.password import hash_password

from src.core.models.Rol import Rol
from src.core.models.PersonalTemporal import PersonalTemporal #cuando este hecho Personal reemplazar esto
from datetime import datetime


@pytest.fixture
def app():
    app = create_app()
    app.app_context().push()
    return app

def test_create_user(app):
    rol = Rol(idRol=1, nombre="Administrador")
    personal = PersonalTemporal(idPersonal=1)

    db.session.add(rol)
    db.session.add(personal)
    db.session.flush()

    usuario = Usuario(
        id_user=1,
        email="test@example.com",
        alias="test",
        password_hash=hash_password("Test1234"),
        isSystemAdmin=True,
        isActive=True,
        updated_at=datetime.now(),
        inserted_at=datetime.now(),
        idRol=rol.idRol,
        idPersonal=personal.idPersonal,
    )

    db.session.add(usuario)
    db.session.commit()