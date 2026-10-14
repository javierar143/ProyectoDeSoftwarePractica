from flask import Blueprint, render_template, request, flash, redirect, url_for
from src.core.services import configuracion as config_service

config_controller = Blueprint("config", __name__, url_prefix="/config")

@config_controller.route("/", methods=["GET"])
def mostrar_config():
    """Obtiene y muestra la configuracion actual del sistema"""

    config = config_service.obtener_configuracion()
    return render_template("config/config.html", config=config)

@config_controller.route("/guardar", methods=["POST"])
def actualizar_config():
    """Obtiene la configuracion actual de elementos por pagina, actualiza y redirige a controller de vista"""
    
    elementos = request.form.get("elementos_por_pagina", type=int)
    # Si el checkbox esta tildado llega 'on', sino None
    mantenimiento = request.form.get("modo_mantenimiento") == "on"

    try:
        config_service.actualizar_configuracion(elementos, mantenimiento)
        flash("Los ajustes del sistema se actualizaron correctamente.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash("Ocurrió un error inesperado.", "danger")

    return redirect(url_for("config.mostrar_config"))