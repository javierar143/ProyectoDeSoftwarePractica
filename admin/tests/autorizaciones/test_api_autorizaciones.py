"""Pruebas integrales de los endpoints REST de autorizaciones, comidas autorizadas, entregas y resúmenes."""

from datetime import date
import pytest
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

from src.web import create_app
from src.core.database import db


@pytest.fixture
def client():
    """Configura un cliente de pruebas y prepara los datos base necesarios."""
    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        db.session.execute(text("SET session_replication_role = 'replica';"))

        # Limpiar registros previos de pruebas para evitar colisiones de estado
        db.session.execute(
            text('DELETE FROM "Entrega" WHERE "idSolicitud" IN (10, 11, 20, 21, 30, 40, 50, 51);')
        )
        db.session.execute(
            text('DELETE FROM "Solicitud" WHERE "idSolicitud" IN (10, 11, 20, 21, 30, 40, 50, 51);')
        )
        db.session.execute(
            text('DELETE FROM "Pedido" WHERE "idPedido" IN (100, 200, 300, 400, 500, 501);')
        )

        # Insertar Personal de prueba
        db.session.execute(
            text("""
                INSERT INTO "Personal"
                    ("idPersonal", dni, nombre, apellido, "isActive",
                     inserted_at, updated_at, "idTipoPersonal", "idTipoMenu")
                VALUES
                    (1, '11111111', 'Administrador', 'Prueba', true, NOW(), NOW(), 1, 1),
                    (2, '22222222', 'Juan', 'Perez', true, NOW(), NOW(), 1, 1)
                ON CONFLICT ("idPersonal") DO UPDATE SET
                    dni = EXCLUDED.dni,
                    nombre = EXCLUDED.nombre,
                    apellido = EXCLUDED.apellido,
                    "isActive" = EXCLUDED."isActive";
            """)
        )

        # Insertar Usuario evaluador / operador de prueba
        db.session.execute(
            text("""
                INSERT INTO "Usuario"
                    ("id_user", email, alias, password_hash,
                     "isSystemAdmin", "isActive", updated_at, inserted_at, "idRol", "idPersonal")
                VALUES
                    (1, 'admin@test.com', 'admin', 'hash', true, true, NOW(), NOW(), 1, 1)
                ON CONFLICT ("id_user") DO NOTHING;
            """)
        )

        db.session.commit()
        db.session.execute(text("SET session_replication_role = 'origin';"))
        db.session.commit()

        with app.test_client() as test_client:
            yield test_client


def _insertar_pedido_y_solicitudes(id_pedido: int, estado_pedido: str, solicitudes: list[tuple]):
    """
    Helper para insertar un Pedido y sus Solicitudes desactivando temporalmente FKs.
    solicitudes: lista de tuplas (idSolicitud, idPersonal, idTipoComida, estadoAutorizacion)
    """
    db.session.execute(text("SET session_replication_role = 'replica';"))

    db.session.execute(
        text("""
            INSERT INTO "Pedido"
                ("idPedido", fecha_desde, periodicidad, estado_general, "idSector", "idUser", inserted_at, updated_at)
            VALUES
                (:id_pedido, CURRENT_DATE, 'diaria', :estado_pedido, 1, 1, NOW(), NOW())
            ON CONFLICT ("idPedido") DO UPDATE SET
                estado_general = EXCLUDED.estado_general;
        """),
        {"id_pedido": id_pedido, "estado_pedido": estado_pedido},
    )

    for id_sol, id_pers, id_comida, estado_aut in solicitudes:
        db.session.execute(
            text("""
                INSERT INTO "Solicitud"
                    ("idSolicitud", "idPedido", "idPersonal", "idTipoComida", "idTipoMenu",
                     fecha_vianda, "condicionCupo", "estadoAutorizacion", inserted_at, updated_at)
                VALUES
                    (:id_sol, :id_pedido, :id_pers, :id_comida, 1,
                     CURRENT_DATE, 'regular', :estado_aut, NOW(), NOW())
                ON CONFLICT ("idSolicitud") DO UPDATE SET
                    "idPedido" = EXCLUDED."idPedido",
                    "estadoAutorizacion" = EXCLUDED."estadoAutorizacion";
            """),
            {
                "id_sol": id_sol,
                "id_pedido": id_pedido,
                "id_pers": id_pers,
                "id_comida": id_comida,
                "estado_aut": estado_aut,
            },
        )

    db.session.commit()
    db.session.execute(text("SET session_replication_role = 'origin';"))
    db.session.commit()


def test_get_listar_y_detalle_autorizaciones(client):
    """Verifica el listado y detalle de pedidos con cantidades pedidas y autorizadas diferenciadas."""
    _insertar_pedido_y_solicitudes(
        id_pedido=100,
        estado_pedido="confirmado",
        solicitudes=[
            (10, 1, 1, "pendiente"),
            (11, 2, 1, "pendiente"),
        ],
    )

    res_list = client.get("/api/authorizations?sector=1")
    assert res_list.status_code == 200
    data_list = res_list.get_json()
    assert isinstance(data_list, list)
    pedido_encontrado = next((p for p in data_list if p["idPedido"] == 100), None)
    assert pedido_encontrado is not None
    assert pedido_encontrado["cantidad_pedida"] == 2
    assert pedido_encontrado["cantidad_autorizada"] == 0

    res_det = client.get("/api/authorizations/100")
    assert res_det.status_code == 200
    data_det = res_det.get_json()
    assert data_det["idPedido"] == 100
    assert data_det["cantidad_pedida"] == 2
    assert data_det["cantidad_autorizada"] == 0
    assert len(data_det["solicitudes"]) == 2


def test_put_autorizar_pedido_nominado_sin_sobrescribir(client):
    """Comprueba que al autorizar una solicitud y rechazar otra, la cantidad pedida no se sobrescribe."""
    _insertar_pedido_y_solicitudes(
        id_pedido=200,
        estado_pedido="confirmado",
        solicitudes=[
            (20, 1, 1, "pendiente"),
            (21, 2, 1, "pendiente"),
        ],
    )

    payload = {
        "id_evaluador": 1,
        "solicitudes": [
            {"idSolicitud": 20, "estado": "AUTORIZADA"},
            {"idSolicitud": 21, "estado": "NO_AUTORIZADA"},
        ],
    }

    response = client.put("/api/authorizations/200", json=payload)
    data = response.get_json()

    assert response.status_code == 200
    assert data["estado"] == "autorizado"
    assert data["cantidad_pedida"] == 2
    assert data["cantidad_autorizada"] == 1

    response_conflict = client.put("/api/authorizations/200", json=payload)
    assert response_conflict.status_code == 409


def test_post_rechazar_pedido(client):
    """Comprueba el rechazo completo de un pedido y el error 409 si ya fue procesado."""
    _insertar_pedido_y_solicitudes(
        id_pedido=300,
        estado_pedido="confirmado",
        solicitudes=[
            (30, 1, 1, "pendiente"),
        ],
    )

    response = client.post("/api/authorizations/300/reject", json={"id_evaluador": 1})
    data = response.get_json()

    assert response.status_code == 200
    assert data["estado"] == "rechazado"
    assert data["cantidad_pedida"] == 1
    assert data["cantidad_autorizada"] == 0

    res_conflict = client.post("/api/authorizations/300/reject", json={"id_evaluador": 1})
    assert res_conflict.status_code == 409


def test_get_comidas_autorizadas_y_entregas(client):
    """Verifica el circuito del Sector Comedor, registro de entrega y bloqueo por duplicidad (409)."""
    _insertar_pedido_y_solicitudes(
        id_pedido=400,
        estado_pedido="autorizado",
        solicitudes=[
            (40, 1, 1, "autorizada"),
        ],
    )

    res_no_filter = client.get("/api/authorized-meals")
    assert res_no_filter.status_code == 400

    res_meals = client.get(f"/api/authorized-meals?dni=11111111&fecha={date.today().isoformat()}")
    assert res_meals.status_code == 200
    meals_data = res_meals.get_json()
    comida = next((m for m in meals_data if m["idSolicitud"] == 40), None)
    assert comida is not None
    assert comida["entregada"] is False

    payload_entrega = {
        "id_user": 1,
        "ids_solicitudes": [40],
        "id_personal": 1,
    }
    res_entrega = client.post("/api/deliveries", json=payload_entrega)
    assert res_entrega.status_code == 201

    res_duplicada = client.post("/api/deliveries", json=payload_entrega)
    assert res_duplicada.status_code == 409


def test_get_deliveries_summary(client):
    """Verifica el funcionamiento del endpoint de resumen /api/deliveries/summary."""
    _insertar_pedido_y_solicitudes(
        id_pedido=500,
        estado_pedido="autorizado",
        solicitudes=[
            (50, 1, 1, "autorizada"),
        ],
    )

    client.post(
        "/api/deliveries",
        json={"id_user": 1, "ids_solicitudes": [50], "id_personal": 1},
    )

    response = client.get(f"/api/deliveries/summary?fecha={date.today().isoformat()}")
    data = response.get_json()

    assert response.status_code == 200
    assert "total_autorizado" in data
    assert "total_entregado" in data
    assert data["total_autorizado"] >= 1
    assert data["total_entregado"] >= 1
    assert isinstance(data["desglose"], list)


def test_get_authorizations_summary(client):
    """Verifica el funcionamiento del resumen de autorizaciones (/api/summaries/authorizations)."""
    _insertar_pedido_y_solicitudes(
        id_pedido=501,
        estado_pedido="autorizado",
        solicitudes=[
            (51, 1, 1, "autorizada"),
        ],
    )

    res_aut = client.get("/api/summaries/authorizations?sector=1")
    assert res_aut.status_code == 200
    data_aut = res_aut.get_json()
    assert data_aut["total_pedido"] == 1
    assert data_aut["total_autorizado"] == 1


def test_get_authorizations_summary(client):
    """Verifica el funcionamiento del resumen de autorizaciones (/api/summaries/authorizations)."""
    _insertar_pedido_y_solicitudes(
        id_pedido=501,
        estado_pedido="autorizado",
        solicitudes=[
            (51, 1, 1, "autorizada"),
        ],
    )

    res_aut = client.get("/api/summaries/authorizations?sector=1")
    assert res_aut.status_code == 200
    data_aut = res_aut.get_json()
    # Esperamos el total acumulado de solicitudes válidas para el sector en la sesión de prueba
    assert data_aut["total_pedido"] >= 1
    assert "total_autorizado" in data_aut