from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from src.core.services import configuracion as config_service
from src.core.security.permissions import require_permission
from src.core.security.session import require_authentication


config_controller = Blueprint("config", __name__, url_prefix="/config")
api_configuration_controller = Blueprint("api_configuration", __name__, url_prefix="/api")


@api_configuration_controller.get("/configuration")
def obtener_configuracion_publica():
    """Expone solo el estado y mensaje de mantenimiento, también durante el 503."""
    config = config_service.obtener_configuracion()
    return jsonify({
        "modo_mantenimiento": bool(config.modo_mantenimiento),
        "mensaje_mantenimiento": config.mensaje_mantenimiento,
    }), 200

@config_controller.before_request
def require_auth():
    """Exige autenticación para cualquier ruta dentro del módulo personal."""
    require_authentication()


@config_controller.route("/", methods=["GET"])
def mostrar_config():
    """Obtiene y muestra la configuración actual del sistema"""
    require_permission("user_index") # O aseguramos rol administrador
    config = config_service.obtener_configuracion()
    return render_template("config/config.html", config=config)

@config_controller.route("/guardar", methods=["POST"])
def actualizar_config():
    """Actualiza la configuración del sistema (elementos, mantenimiento y mensaje)"""
    require_permission("user_index")
    
    elementos = request.form.get("elementos_por_pagina", type=int)
    mantenimiento = request.form.get("modo_mantenimiento") == "on"
    mensaje = request.form.get("mensaje_mantenimiento", "").strip()

    try:
        config_service.actualizar_configuracion(elementos, mantenimiento, mensaje)
        flash("Los ajustes del sistema se actualizaron correctamente.", "success")
    except ValueError as e:
        current_app.logger.warning(f"Validación fallida al actualizar la configuración: {str(e)}")
        flash(str(e), "danger")
    except Exception as e:
        current_app.logger.error(f"Error inesperado al actualizar la configuración del sistema: {str(e)}")
        flash("Ocurrió un error inesperado.", "danger")

    return redirect(url_for("config.mostrar_config"))
