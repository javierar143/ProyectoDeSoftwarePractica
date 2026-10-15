
"""Pruebas de los endpoints REST de autorizaciones."""

import pytest
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

from src.web import create_app
from src.core.database import db


@pytest.fixture
def client():
    """Configura un cliente de pruebas y prepara los datos necesarios."""
    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        # Se deshabilitan temporalmente las restricciones para preparar
        # los datos de prueba sin depender de registros relacionados.
        db.session.execute(
            text("SET session_replication_role = 'replica';")
        )

        db.session.execute(
            text("""
                 INSERT INTO "Personal"
                 ("idPersonal", dni, nombre, apellido, "isActive",
                  inserted_at, updated_at, "idTipoPersonal", "idTipoMenu")
                 VALUES (1, '11111111', 'Administrador', 'Prueba', true,
                         NOW(), NOW(), 1, 1) ON CONFLICT ("idPersonal") DO
                 UPDATE SET
                     dni = EXCLUDED.dni,
                     nombre = EXCLUDED.nombre,
                     apellido = EXCLUDED.apellido,
                     "isActive" = EXCLUDED."isActive";
                 """)
        )

        db.session.execute(
            text("""
                INSERT INTO "Usuario"
                    (
                        "id_user", email, alias, password_hash,
                        "isSystemAdmin", "isActive",
                        updated_at, inserted_at, "idRol", "idPersonal"
                    )
                VALUES
                    (
                        1, 'admin@test.com', 'admin', 'hash',
                        true, true, NOW(), NOW(), 1, 1
                    )
                ON CONFLICT ("id_user") DO NOTHING;
            """)
        )

        db.session.commit()

        db.session.execute(
            text("SET session_replication_role = 'origin';")
        )
        db.session.commit()

        with app.test_client() as test_client:
            yield test_client


def test_get_solicitudes_pendientes(client):
    """Comprueba que el endpoint devuelve las solicitudes pendientes."""
    db.session.execute(
        text("SET session_replication_role = 'replica';")
    )

    db.session.execute(
        text("""
            INSERT INTO "Solicitud"
                (
                    "idSolicitud", "idPedido", "idPersonal",
                    "idTipoComida", "idTipoMenu", fecha_vianda,
                    "condicionCupo", "estadoAutorizacion",
                    inserted_at, updated_at
                )
            VALUES
                (
                    10, 1, 1, 1, 1, CURRENT_DATE,
                    'regular', 'pendiente', NOW(), NOW()
                )
            ON CONFLICT ("idSolicitud") DO UPDATE SET
                "estadoAutorizacion" = 'pendiente';
        """)
    )

    db.session.commit()
    db.session.execute(
        text("SET session_replication_role = 'origin';")
    )
    db.session.commit()

    response = client.get("/api/authorizations/pending")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert any(solicitud["idSolicitud"] == 10 for solicitud in data)


def test_put_actualizar_autorizacion(client):
    """Comprueba que una solicitud pueda autorizarse."""
    db.session.execute(
        text("SET session_replication_role = 'replica';")
    )

    db.session.execute(
        text("""
            INSERT INTO "Solicitud"
                (
                    "idSolicitud", "idPedido", "idPersonal",
                    "idTipoComida", "idTipoMenu", fecha_vianda,
                    "condicionCupo", "estadoAutorizacion",
                    inserted_at, updated_at
                )
            VALUES
                (
                    20, 1, 1, 1, 1, CURRENT_DATE,
                    'regular', 'pendiente', NOW(), NOW()
                )
            ON CONFLICT ("idSolicitud") DO UPDATE SET
                "estadoAutorizacion" = 'pendiente';
        """)
    )

    db.session.commit()
    db.session.execute(
        text("SET session_replication_role = 'origin';")
    )
    db.session.commit()

    payload = {
        "estado": "AUTORIZADA",
        "id_evaluador": 1,
    }

    response = client.put(
        "/api/authorizations/20",
        json=payload,
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["mensaje"] == "Autorización actualizada correctamente"
    assert data["estadoAutorizacion"] == "AUTORIZADA"


def test_post_registrar_entrega(client):
    """Comprueba que se registre la entrega de una solicitud autorizada."""
    db.session.execute(
        text("SET session_replication_role = 'replica';")
    )

    db.session.execute(
        text("""
            INSERT INTO "Solicitud"
                (
                    "idSolicitud", "idPedido", "idPersonal",
                    "idTipoComida", "idTipoMenu", fecha_vianda,
                    "condicionCupo", "estadoAutorizacion",
                    inserted_at, updated_at
                )
            VALUES
                (
                    30, 1, 1, 1, 1, CURRENT_DATE,
                    'regular', 'autorizada', NOW(), NOW()
                )
            ON CONFLICT ("idSolicitud") DO UPDATE SET
                "estadoAutorizacion" = 'autorizada';
        """)
    )

    db.session.commit()
    db.session.execute(
        text("SET session_replication_role = 'origin';")
    )
    db.session.commit()

    payload = {
        "id_user": 1,
        "id_solicitud": 30,
        "id_personal": 1,
    }

    response = client.post(
        "/api/authorizations/deliveries",
        json=payload,
    )

    assert response.status_code in (201, 409)
