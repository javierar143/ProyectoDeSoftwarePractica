import pytest
from dotenv import load_dotenv
from sqlalchemy import text
from datetime import date

load_dotenv()

from src.web import create_app
from src.core.database import db

@pytest.fixture
def client():
    """Configura un cliente de pruebas de Flask."""

    app = create_app()
    app.config["TESTING"] = True
    
    with app.test_client() as client:
        with app.app_context():
            # Aseguramos el Personal y Usuario base globales para que no fallen las FKs
            db.session.execute(text("SET session_replication_role = 'replica';"))
            db.session.execute(text('INSERT INTO "Personal" ("idPersonal") VALUES (1) ON CONFLICT DO NOTHING;'))
            db.session.execute(text('''
                INSERT INTO "Usuario" ("id_user", email, alias, password_hash, "isSystemAdmin", "isActive", updated_at, inserted_at, "idRol", "idPersonal")
                VALUES (1, 'admin@test.com', 'admin', 'hash', true, true, NOW(), NOW(), 1, 1)
                ON CONFLICT DO NOTHING;
            '''))
            db.session.commit()
            db.session.execute(text("SET session_replication_role = 'origin';"))
            
            yield client

def test_get_solicitudes_pendientes(client):
    """Prueba que el endpoint GET /pending funcione correctamente."""

    db.session.execute(text("SET session_replication_role = 'replica';"))
    db.session.execute(text('''
        INSERT INTO "Solicitud" ("idSolicitud", "idPedido", "idPersonal", "idTipoComida", "idTipoMenu", fecha_vianda, "condicionCupo", "estadoAutorizacion", inserted_at, updated_at)
        VALUES (10, 1, 1, 1, 1, CURRENT_DATE, 'regular', 'pendiente', NOW(), NOW())
        ON CONFLICT ("idSolicitud") DO UPDATE SET "estadoAutorizacion" = 'pendiente';
    '''))
    db.session.commit()
    db.session.execute(text("SET session_replication_role = 'origin';"))

    response = client.get("/api/authorizations/pending")
    data = response.get_json()
    
    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(s["idSolicitud"] == 10 for s in data)


def test_put_actualizar_autorizacion(client):
    """Prueba que el endpoint PUT actualice el estado a AUTORIZADA."""

    db.session.execute(text("SET session_replication_role = 'replica';"))
    db.session.execute(text('''
        INSERT INTO "Solicitud" ("idSolicitud", "idPedido", "idPersonal", "idTipoComida", "idTipoMenu", fecha_vianda, "condicionCupo", "estadoAutorizacion", inserted_at, updated_at)
        VALUES (20, 1, 1, 1, 1, CURRENT_DATE, 'regular', 'pendiente', NOW(), NOW())
        ON CONFLICT ("idSolicitud") DO UPDATE SET "estadoAutorizacion" = 'pendiente';
    '''))
    db.session.commit()
    db.session.execute(text("SET session_replication_role = 'origin';"))

    payload = {
        "estado": "AUTORIZADA",
        "id_evaluador": 1
    }
    
    response = client.put("/api/authorizations/20", json=payload)
    data = response.get_json()
    
    assert response.status_code == 200
    assert data["mensaje"] == "Autorización actualizada correctamente"
    assert data["estadoAutorizacion"] == "AUTORIZADA"


def test_post_registrar_entrega(client):
    """Prueba que el endpoint POST registre la entrega en el comedor."""
    
    db.session.execute(text("SET session_replication_role = 'replica';"))
    db.session.execute(text('''
        INSERT INTO "Solicitud" ("idSolicitud", "idPedido", "idPersonal", "idTipoComida", "idTipoMenu", fecha_vianda, "condicionCupo", "estadoAutorizacion", inserted_at, updated_at)
        VALUES (30, 1, 1, 1, 1, CURRENT_DATE, 'regular', 'autorizada', NOW(), NOW())
        ON CONFLICT ("idSolicitud") DO UPDATE SET "estadoAutorizacion" = 'autorizada';
    '''))
    db.session.commit()
    db.session.execute(text("SET session_replication_role = 'origin';"))

    payload = {
        "id_user": 1,
        "id_solicitud": 30,
        "id_personal": 1
    }
    
    response = client.post("/api/authorizations/deliveries", json=payload)
    assert response.status_code in [201, 409]