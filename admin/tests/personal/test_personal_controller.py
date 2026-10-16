import pytest
from src.web import create_app
from src.core.database import db
from src.core.services.personal import personal as service_personal

@pytest.fixture
def app():
    """Inicializa la app para los tests del controlador."""
    app = create_app()
    with app.app_context():
        yield app

def test_crear_personal_dni_duplicado_retorna_409(app, mocker):
    """Verifica que el controlador retorne HTTP 409 (Conflict) ante un DNI duplicado."""
    client = app.test_client()
    
    # 1. Usamos mocker para simular que el que hace la petición es del Servicio de Alimentación
    # (Así pasamos la validación del 403 sin depender de IDs reales de la BD)
    mocker.patch('src.core.services.usuarios.rol.get_by_id', return_value=type('obj', (object,), {'nombre': 'Servicio de Alimentación'}))
    mocker.patch('src.core.services.usuarios.usuario.get_by_id', return_value=type('obj', (object,), {'idRol': 1, 'idSector': 1}))
    
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
    
    # 4. Simulamos la sesión del usuario (el ID no importa porque está mockeado)
    with client.session_transaction() as sess:
        sess["user_id"] = 99
        
    # 5. Hacemos el POST a la ruta
    response = client.post('/personal/nuevo', data=datos_form)
    
    # 6. VERIFICACIÓN: El servidor debe retornar 409
    assert response.status_code == 409
    assert b"Ya existe una persona registrada con ese DNI" in response.data