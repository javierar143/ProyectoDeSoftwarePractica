from dotenv import load_dotenv

load_dotenv()

import pytest

from src.web import create_app

from src.core.database import db, reset_db
from src.core.models.Usuario import Usuario
from src.core.security.password import hash_password


from src.core.models.Rol import Rol
from src.core.models.Personal import Personal 
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.TipoMenu import TipoMenu

from src.core.repositories.usuarios.usuario import create, get_by_email


from datetime import datetime


@pytest.fixture
def app():
    """Crea la aplicación Flask y prepara una base limpia para las pruebas."""
    app = create_app()

    with app.app_context():
        reset_db()
        yield app

    return None

def test_create_user(app):
    rol = Rol(idRol=1, nombre="Administrador")
    tipo_p = TipoPersonal(idTipoPersonal=1, nombre="Fijo")
    tipo_m = TipoMenu(idTipoMenu=1, nombre="General")
    personal = Personal(
        idPersonal=1,
        dni="12345678",
        nombre="Test",
        apellido="Usuario",
        isActive=True,
        idTipoPersonal=1,
        idTipoMenu=1,
        inserted_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.session.add(rol)
    db.session.add(tipo_p)
    db.session.add(tipo_m)
    db.session.flush()
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

    usuario_creado = create(usuario)

    usuario_buscado = get_by_email("test@example.com")

    assert usuario_creado.email == "test@example.com"
    assert usuario_buscado is not None
    assert usuario_buscado.email == "test@example.com"