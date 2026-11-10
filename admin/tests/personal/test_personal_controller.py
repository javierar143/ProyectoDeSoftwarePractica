from dotenv import load_dotenv
load_dotenv()
import pytest
from unittest.mock import patch
from src.web import create_app
from src.core.database import db
from src.core.services.personal import personal as service_personal

@pytest.fixture
def app():
    """Inicializa la app para los tests del controlador."""
    app = create_app()
    with app.app_context():
        yield app

@patch('src.web.controllers.personal.personal.require_permission')
def test_crear_personal_dni_duplicado_retorna_409(mock_require_permission, app):
    """Verifica que el controlador retorne HTTP 409 (Conflict) ante un DNI duplicado."""
    client = app.test_client()
    
    # Simulamos que el permiso pasa sin abortar
    mock_require_permission.return_value = None
    
    # Creamos la primera persona
    service_personal.create(
        dni="88888888", nombre="Original", apellido="Uno", 
        id_tipo_personal=1, id_tipo_menu=1, id_sector=1
    )
    
    # Intentamos crear con el mismo DNI
    datos_form = {
        "dni": "88888888",
        "nombre": "Copia",
        "apellido": "Dos",
        "idTipoPersonal": "1",
        "idTipoMenu": "1",
        "idSector": "1"
    }
    
    with client.session_transaction() as sess:
        sess["user_id"] = 99
        
    response = client.post('/personal/nuevo', data=datos_form)
    
    assert response.status_code == 409
    assert b"Ya existe una persona registrada con ese DNI" in response.data