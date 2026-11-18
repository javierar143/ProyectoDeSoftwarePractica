"""Pruebas integrales de los endpoints REST de autorizaciones, comidas autorizadas, entregas y resúmenes."""

from datetime import date, timedelta
from types import SimpleNamespace
import pytest
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

from src.web import create_app
from src.core.database import db


@pytest.fixture
def client(monkeypatch):
    """Configura un cliente de pruebas y prepara los datos base necesarios."""
    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        # Asegurar que el modo mantenimiento esté desactivado para que no devuelva 503
        from src.core.services import configuracion as config_service
        config_service.actualizar_configuracion(10, False, "")

        db.session.execute(text("SET session_replication_role = 'replica';"))

        # Limpiar registros previos de pruebas para evitar colisiones de estado
        db.session.execute(
            text(
                'DELETE FROM "Entrega" WHERE "idSolicitud" IN '
                "(10, 11, 20, 21, 30, 31, 40, 41, 42, 50, 51, 60);"
            )
        )
        db.session.execute(
            text(
                'DELETE FROM "Solicitud" WHERE "idSolicitud" IN '
                "(10, 11, 20, 21, 30, 31, 40, 41, 42, 50, 51, 60);"
            )
        )
        db.session.execute(
            text(
                'DELETE FROM "Pedido" WHERE "idPedido" IN '
                "(100, 200, 300, 301, 400, 401, 500, 501, 600);"
            )
        )

        # Insertar Personal de prueba con todas las columnas NOT NULL del modelo Personal
        db.session.execute(
            text("""
                INSERT INTO "Personal"
                    ("idPersonal", dni, nombre, apellido, "isActive", is_deleted,
                     inserted_at, updated_at, "idTipoPersonal", "idTipoMenu")
                VALUES
                    (1, '11111111', 'Administrador', 'Prueba', true, false, NOW(), NOW(), 1, 1),
                    (2, '22222222', 'Juan', 'Perez', true, false, NOW(), NOW(), 1, 1)
                ON CONFLICT ("idPersonal") DO UPDATE SET
                    dni = EXCLUDED.dni,
                    nombre = EXCLUDED.nombre,
                    apellido = EXCLUDED.apellido,
                    "isActive" = EXCLUDED."isActive",
                    is_deleted = EXCLUDED.is_deleted;
            """)
        )

        # Insertar Usuario evaluador / operador de prueba con todas las columnas NOT NULL del modelo Usuario
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

        from src.core.services.auth import api_auth

        monkeypatch.setattr(
            api_auth,
            "get_authenticated_user_status",
            lambda _token: (SimpleNamespace(id_user=1, isActive=True), None),
        )

        with app.test_client() as test_client:
            test_client.environ_base["HTTP_AUTHORIZATION"] = "Bearer test-operational-token"
            yield test_client


def _insertar_pedido_y_solicitudes(
    id_pedido: int,
    estado_pedido: str,
    solicitudes: list[tuple],
    fecha_pedido: date | None = None,
):
    """
    Helper para insertar un Pedido y sus Solicitudes desactivando temporalmente FKs.
    solicitudes: lista de tuplas (idSolicitud, idPersonal, idTipoComida, estadoAutorizacion)
    """
    fecha_usar = fecha_pedido or date.today()
    db.session.execute(text("SET session_replication_role = 'replica';"))

    # Incluye todas las columnas NOT NULL del modelo Pedido (fecha_desde, fecha_hasta, activo, etc.)
    db.session.execute(
        text("""
            INSERT INTO "Pedido"
                ("idPedido", fecha_desde, fecha_hasta, periodicidad, estado_general,
                 "idSector", "idUser", activo, inserted_at, updated_at)
            VALUES
                (:id_pedido, :fecha_usar, :fecha_usar, 'diaria', :estado_pedido,
                 1, 1, true, NOW(), NOW())
            ON CONFLICT ("idPedido") DO UPDATE SET
                fecha_desde = EXCLUDED.fecha_desde,
                fecha_hasta = EXCLUDED.fecha_hasta,
                estado_general = EXCLUDED.estado_general,
                activo = EXCLUDED.activo,
                updated_at = NOW();
        """),
        {"id_pedido": id_pedido, "estado_pedido": estado_pedido, "fecha_usar": fecha_usar},
    )

    # Incluye todas las columnas NOT NULL del modelo Solicitud (incluyendo activo = true)
    for id_sol, id_pers, id_comida, estado_aut in solicitudes:
        db.session.execute(
            text("""
                INSERT INTO "Solicitud"
                    ("idSolicitud", "idPedido", "idPersonal", "idTipoComida", "idTipoMenu",
                     fecha_vianda, "condicionCupo", "estadoAutorizacion", activo, inserted_at, updated_at)
                VALUES
                    (:id_sol, :id_pedido, :id_pers, :id_comida, 1,
                     :fecha_usar, 'regular', :estado_aut, true, NOW(), NOW())
                ON CONFLICT ("idSolicitud") DO UPDATE SET
                    "idPedido" = EXCLUDED."idPedido",
                    fecha_vianda = EXCLUDED.fecha_vianda,
                    "estadoAutorizacion" = EXCLUDED."estadoAutorizacion",
                    activo = EXCLUDED.activo,
                    updated_at = NOW();
            """),
            {
                "id_sol": id_sol,
                "id_pedido": id_pedido,
                "id_pers": id_pers,
                "id_comida": id_comida,
                "estado_aut": estado_aut,
                "fecha_usar": fecha_usar,
            },
        )

    db.session.commit()
    db.session.execute(text("SET session_replication_role = 'origin';"))
    db.session.commit()


def test_get_listar_y_detalle_autorizaciones(client):
    """Verifica el listado, detalle de pedidos y validaciones de fechas del nuevo validator."""
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

    # Prueba del nuevo validator: rango de fechas invertido y formato inválido -> 400
    res_bad_range = client.get("/api/authorizations?fecha_desde=2026-11-20&fecha_hasta=2026-11-10")
    assert res_bad_range.status_code == 400
    res_bad_date = client.get("/api/authorizations?fecha_desde=fecha-invalida")
    assert res_bad_date.status_code == 400

    res_det = client.get("/api/authorizations/100")
    assert res_det.status_code == 200
    data_det = res_det.get_json()
    assert data_det["idPedido"] == 100
    assert data_det["cantidad_pedida"] == 2
    assert data_det["cantidad_autorizada"] == 0
    assert len(data_det["solicitudes"]) == 2


def test_put_autorizar_y_corregir_pedido_etapa2(client):
    """
    Comprueba la autorización nominada, la posibilidad de corregir un pedido ya autorizado
    de fecha actual/futura sin entregas (Etapa 2), y el bloqueo 409 si hay entregas o conflicto de versión.
    """
    _insertar_pedido_y_solicitudes(
        id_pedido=200,
        estado_pedido="confirmado",
        solicitudes=[
            (20, 1, 1, "pendiente"),
            (21, 2, 1, "pendiente"),
        ],
    )

    # 1. Primera autorización: 1 autorizada y 1 no autorizada
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

    # 2. Etapa 2: Corregir pedido ya autorizado (es de hoy y ninguna comida fue entregada aún) -> 200 OK
    payload_correccion = {
        "id_evaluador": 1,
        "solicitudes": [
            {"idSolicitud": 20, "estado": "AUTORIZADA"},
            {"idSolicitud": 21, "estado": "AUTORIZADA"},
        ],
    }
    res_correccion = client.put("/api/authorizations/200", json=payload_correccion)
    data_corr = res_correccion.get_json()
    assert res_correccion.status_code == 200
    assert data_corr["cantidad_pedida"] == 2
    assert data_corr["cantidad_autorizada"] == 2

    # 3. Etapa 2: Control de cambios simultáneos (ultima_modificacion distinta) -> 409 Conflict
    payload_desactualizado = {
        "id_evaluador": 1,
        "ultima_modificacion": "1999-01-01T00:00:00",
        "solicitudes": [{"idSolicitud": 20, "estado": "NO_AUTORIZADA"}],
    }
    res_concurrencia = client.put("/api/authorizations/200", json=payload_desactualizado)
    assert res_concurrencia.status_code == 409

    # 4. Etapa 2: Una vez entregada una comida del pedido, ya NO se puede corregir la autorización -> 409
    client.post("/api/deliveries", json={"id_user": 1, "ids_solicitudes": [20], "id_personal": 1})
    res_bloqueo_entrega = client.put("/api/authorizations/200", json=payload)
    assert res_bloqueo_entrega.status_code == 409


def test_put_autorizar_pedido_dia_anterior_bloqueado(client):
    """Comprueba que en Etapa 2 no se pueden autorizar ni corregir pedidos de días anteriores (409)."""
    ayer = date.today() - timedelta(days=1)
    _insertar_pedido_y_solicitudes(
        id_pedido=600,
        estado_pedido="confirmado",
        solicitudes=[(60, 1, 1, "pendiente")],
        fecha_pedido=ayer,
    )

    payload = {
        "id_evaluador": 1,
        "solicitudes": [{"idSolicitud": 60, "estado": "AUTORIZADA"}],
    }
    res = client.put("/api/authorizations/600", json=payload)
    assert res.status_code == 409


def test_post_rechazar_pedido(client):
    """Comprueba el rechazo con motivo obligatorio (Etapa 2), bloqueo por día anterior y error 409."""
    _insertar_pedido_y_solicitudes(
        id_pedido=300,
        estado_pedido="confirmado",
        solicitudes=[
            (30, 1, 1, "pendiente"),
        ],
    )

    # 1. Etapa 2: Rechazar sin motivo debe devolver 400 Bad Request
    res_sin_motivo = client.post("/api/authorizations/300/reject", json={"id_evaluador": 1})
    assert res_sin_motivo.status_code == 400

    # 2. Rechazar con motivo obligatorio -> 200 OK
    response = client.post(
        "/api/authorizations/300/reject",
        json={"id_evaluador": 1, "motivo": "Exceso de cupo sin justificación"},
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["estado"] == "rechazado"
    assert data["cantidad_pedida"] == 1
    assert data["cantidad_autorizada"] == 0

    # 3. Intentar rechazar un pedido ya rechazado -> 409 Conflict
    res_conflict = client.post(
        "/api/authorizations/300/reject",
        json={"id_evaluador": 1, "motivo": "Intento duplicado"},
    )
    assert res_conflict.status_code == 409

    # 4. Etapa 2: Intentar rechazar un pedido de un día anterior -> 409 Conflict
    ayer = date.today() - timedelta(days=1)
    _insertar_pedido_y_solicitudes(
        id_pedido=301,
        estado_pedido="confirmado",
        solicitudes=[(31, 1, 1, "pendiente")],
        fecha_pedido=ayer,
    )
    res_ayer = client.post(
        "/api/authorizations/301/reject",
        json={"id_evaluador": 1, "motivo": "Pedido vencido"},
    )
    assert res_ayer.status_code == 409


def test_get_comidas_autorizadas_y_entregas(client):
    """
    Verifica el circuito del Sector Comedor: validación de filtros, responsable por defecto (1 persona),
    responsable obligatorio o tercero en retiros múltiples (Etapa 2) y bloqueo por duplicidad (409).
    """
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

    # Etapa 2: Si retira 1 sola persona y no se envía id_personal, esa persona es responsable por defecto
    payload_entrega = {
        "id_user": 1,
        "ids_solicitudes": [40],
    }
    res_entrega = client.post("/api/deliveries", json=payload_entrega)
    assert res_entrega.status_code == 201
    entregas_creadas = res_entrega.get_json()["entregas"]
    assert entregas_creadas[0]["idPersonalResponsable"] == 1

    # Duplicada -> 409
    res_duplicada = client.post("/api/deliveries", json=payload_entrega)
    assert res_duplicada.status_code == 409

    # Etapa 2: Retiro para múltiples personas exige indicar responsable o tercero válido
    _insertar_pedido_y_solicitudes(
        id_pedido=401,
        estado_pedido="autorizado",
        solicitudes=[
            (41, 1, 2, "autorizada"),
            (42, 2, 2, "autorizada"),
        ],
    )
    # Sin responsable siendo 2 personas distintas -> 400
    res_multi_sin_resp = client.post(
        "/api/deliveries",
        json={"id_user": 1, "ids_solicitudes": [41, 42]},
    )
    assert res_multi_sin_resp.status_code == 400

    # Con tercero válido -> 201
    res_multi_tercero = client.post(
        "/api/deliveries",
        json={
            "id_user": 1,
            "ids_solicitudes": [41, 42],
            "tercero": {"dni": "33444555", "nombre_apellido": "Carlos Gomez"},
        },
    )
    assert res_multi_tercero.status_code == 201

    # Verificamos listado y detalle de entregas a través del nuevo servicio
    res_list_del = client.get(f"/api/deliveries?fecha={date.today().isoformat()}")
    assert res_list_del.status_code == 200
    id_entrega_creada = entregas_creadas[0]["idEntrega"]
    res_det_del = client.get(f"/api/deliveries/{id_entrega_creada}")
    assert res_det_del.status_code == 200


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
    """Verifica el funcionamiento del resumen de autorizaciones y filtro de condición (Etapa 2)."""
    _insertar_pedido_y_solicitudes(
        id_pedido=501,
        estado_pedido="autorizado",
        solicitudes=[
            (51, 1, 1, "autorizada"),
        ],
    )

    res_aut = client.get("/api/summaries/authorizations?sector=1&condicion=regular")
    assert res_aut.status_code == 200
    data_aut = res_aut.get_json()
    assert data_aut["total_pedido"] >= 1
    assert "total_autorizado" in data_aut

    # Condición inválida en validator -> 400
    res_bad_cond = client.get("/api/summaries/authorizations?condicion=invalida")
    assert res_bad_cond.status_code == 400
