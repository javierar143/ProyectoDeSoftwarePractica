from types import SimpleNamespace

import pytest

from src.core.services import configuracion as config_service
from src.core.repositories import configuracion as config_repository
from src.web import create_app
from src.web.handlers import maintenance


@pytest.fixture
def app():
    app = create_app(
        env="testing",
        test_config={"SQLALCHEMY_ENGINES": {"default": "sqlite://"}},
    )
    app.add_url_rule(
        "/test-backoffice",
        endpoint="test_backoffice",
        view_func=lambda: "backoffice ok",
    )
    return app


def test_configuration_endpoint_is_public_during_maintenance(app, monkeypatch):
    message = "Mensaje personalizado guardado"
    monkeypatch.setattr(
        config_service,
        "obtener_configuracion",
        lambda: SimpleNamespace(modo_mantenimiento=True, mensaje_mantenimiento=message),
    )

    response = app.test_client().get("/api/configuration")

    assert response.status_code == 200
    assert response.json == {
        "modo_mantenimiento": True,
        "mensaje_mantenimiento": message,
    }


def test_public_configuration_reports_disabled_mode_and_keeps_custom_message(app, monkeypatch):
    message = "Mensaje personalizado"
    monkeypatch.setattr(
        config_service,
        "obtener_configuracion",
        lambda: SimpleNamespace(modo_mantenimiento=False, mensaje_mantenimiento=message),
    )

    response = app.test_client().get("/api/configuration")

    assert response.status_code == 200
    assert response.json["modo_mantenimiento"] is False
    assert response.json["mensaje_mantenimiento"] == message


def test_maintenance_returns_503_for_regular_api_routes(app, monkeypatch):
    message = "Mantenimiento activo de prueba"
    monkeypatch.setattr(
        config_service,
        "obtener_configuracion",
        lambda: SimpleNamespace(
            modo_mantenimiento=True,
            mensaje_mantenimiento=message,
        ),
    )

    response = app.test_client().get("/api/roles/operational")

    assert response.status_code == 503
    assert message.encode() in response.data


def test_options_preflight_is_not_blocked_or_consulting_configuration(app, monkeypatch):
    config_calls = []
    monkeypatch.setattr(
        config_service,
        "obtener_configuracion",
        lambda: config_calls.append(True),
    )

    response = app.test_client().options("/api/roles/operational")

    assert response.status_code == 200
    assert config_calls == []


@pytest.mark.parametrize(
    ("system_admin", "has_user_index"),
    [(True, False), (False, True)],
)
def test_administrators_keep_backoffice_access_during_maintenance(
    app, monkeypatch, system_admin, has_user_index
):
    from types import SimpleNamespace

    monkeypatch.setattr(
        config_service,
        "obtener_configuracion",
        lambda: SimpleNamespace(modo_mantenimiento=True, mensaje_mantenimiento="Mantenimiento"),
    )
    monkeypatch.setattr(maintenance, "get_authenticated_user_id", lambda: 42)
    monkeypatch.setattr(
        maintenance.usuario_service,
        "get_by_id",
        lambda _user_id: SimpleNamespace(isSystemAdmin=system_admin),
    )
    monkeypatch.setattr(
        maintenance.permiso_service,
        "user_has_permission",
        lambda _user_id, permission: permission == "user_index" and has_user_index,
    )

    response = app.test_client().get("/test-backoffice")

    assert response.status_code == 200
    assert response.text == "backoffice ok"


def test_disabled_maintenance_does_not_intercept_api(app, monkeypatch):
    monkeypatch.setattr(
        config_service,
        "obtener_configuracion",
        lambda: SimpleNamespace(modo_mantenimiento=False, mensaje_mantenimiento=""),
    )

    response = app.test_client().get("/api/roles/operational")

    assert response.status_code == 401


def test_login_validation_exposes_field_error_map(app, monkeypatch):
    monkeypatch.setattr(
        config_service,
        "obtener_configuracion",
        lambda: SimpleNamespace(modo_mantenimiento=False, mensaje_mantenimiento=""),
    )

    response = app.test_client().post("/api/auth/login", json={"email": "", "password": ""})

    assert response.status_code == 400
    assert response.json["field_errors"] == {"email": "El email es obligatorio."}


def test_invalid_login_remains_401(app, monkeypatch):
    from src.core.services.auth import api_auth

    monkeypatch.setattr(
        config_service,
        "obtener_configuracion",
        lambda: SimpleNamespace(modo_mantenimiento=False, mensaje_mantenimiento=""),
    )
    monkeypatch.setattr(api_auth, "login", lambda _email, _password: None)

    response = app.test_client().post(
        "/api/auth/login", json={"email": "nobody@example.test", "password": "wrong"}
    )

    assert response.status_code == 401


def test_unknown_resource_remains_404(app, monkeypatch):
    monkeypatch.setattr(
        config_service,
        "obtener_configuracion",
        lambda: SimpleNamespace(modo_mantenimiento=False, mensaje_mantenimiento=""),
    )

    response = app.test_client().get("/api/no-such-resource")

    assert response.status_code == 404


def test_default_maintenance_message_fits_existing_column_and_is_used_for_blank_values(monkeypatch):
    assert len(config_service.MENSAJE_MANTENIMIENTO_DEFAULT) <= 255

    config = SimpleNamespace(
        elementos_por_pagina=10,
        modo_mantenimiento=False,
        mensaje_mantenimiento=" ",
    )
    updated = []

    def capture_update(elements, maintenance, message):
        updated.append((elements, maintenance, message))
        config.mensaje_mantenimiento = message
        return config

    monkeypatch.setattr(config_repository, "obtener_configuracion", lambda: config)
    monkeypatch.setattr(config_repository, "actualizar_configuracion", capture_update)
    result = config_service.obtener_configuracion()

    assert result.mensaje_mantenimiento == config_service.MENSAJE_MANTENIMIENTO_DEFAULT
    assert updated == [(10, False, config_service.MENSAJE_MANTENIMIENTO_DEFAULT)]


def test_previous_unmodified_default_is_replaced_but_custom_message_is_preserved(monkeypatch):
    previous_default = SimpleNamespace(
        elementos_por_pagina=10,
        modo_mantenimiento=False,
        mensaje_mantenimiento=config_service.MENSAJE_MANTENIMIENTO_ANTERIOR,
    )
    saved = []
    monkeypatch.setattr(config_repository, "obtener_configuracion", lambda: previous_default)

    def capture_update(elements, maintenance, message):
        saved.append(message)
        previous_default.mensaje_mantenimiento = message
        return previous_default

    monkeypatch.setattr(config_repository, "actualizar_configuracion", capture_update)
    config_service.obtener_configuracion()

    assert saved == [config_service.MENSAJE_MANTENIMIENTO_DEFAULT]

    custom = SimpleNamespace(
        elementos_por_pagina=10,
        modo_mantenimiento=False,
        mensaje_mantenimiento="Mantenimiento coordinado con el equipo.",
    )
    monkeypatch.setattr(config_repository, "obtener_configuracion", lambda: custom)
    saved.clear()
    result = config_service.obtener_configuracion()

    assert result.mensaje_mantenimiento == custom.mensaje_mantenimiento
    assert saved == []


def test_admin_configuration_update_persists_mode_and_custom_message(monkeypatch):
    writes = []
    monkeypatch.setattr(
        config_repository,
        "actualizar_configuracion",
        lambda elements, enabled, message: writes.append((elements, enabled, message)),
    )
    custom_message = "El mantenimiento finalizará a las 18:00."

    config_service.actualizar_configuracion(10, True, custom_message)

    assert writes == [(10, True, custom_message)]
