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

def test_crear_personal_dni_duplicado_retorna_409(app):
    """Verifica que el controlador retorne HTTP 409 (Conflict) ante un DNI duplicado."""
    client = app.test_client()
    
    # 1. Usamos patch nativo de Python con el bloque "with"
    with patch('src.core.services.usuarios.rol.get_by_id') as mock_rol, \
         patch('src.core.services.usuarios.usuario.get_by_id') as mock_usuario:
         
        mock_rol.return_value = type('obj', (object,), {'nombre': 'Servicio de Alimentación'})
        mock_usuario.return_value = type('obj', (object,), {'idRol': 1, 'idSector': 1})
        
        # 2. Creamos la primera persona en la base de datos de prueba
        service_personal.create(
            dni="88888888", nombre="Original", apellido="Uno", 
            id_tipo_personal=1, id_tipo_menu=1, id_sector=1
        )
        
        # 3. Preparamos el formulario intentando usar el MISMO DNI
        datos_form = {
            "dni": "88888888",
            "nombre": "Copia",
            "apellido": "Dos",
            "idTipoPersonal": "1",
            "idTipoMenu": "1",
            "idSector": "1"
        }
        
        # 4. Simulamos la sesión del usuario
        with client.session_transaction() as sess:
            sess["user_id"] = 99
            
        # 5. Hacemos el POST a la ruta
        response = client.post('/personal/nuevo', data=datos_form)
        
        # 6. VERIFICACIÓN: El servidor debe retornar 409
        assert response.status_code == 409
        assert b"Ya existe una persona registrada con ese DNI" in response.data