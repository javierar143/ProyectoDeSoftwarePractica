"""Controlador HTTP para el alta de usuarios."""

from flask import Blueprint, redirect, request, url_for

from src.core.security.permissions import require_permission
from src.web.controllers.usuarios.alta_acciones import (
    buscar_personal,
    crear_personal_usuario,
    crear_usuario,
    mostrar_formulario,
)

alta_controller = Blueprint("alta_usuarios", __name__)


@alta_controller.before_request
def check_permissions():
    """Garantiza autenticación y permisos para todas las acciones del alta."""
    require_permission("user_new")


@alta_controller.route("/nuevo", methods=["GET"])
def new():
    """Muestra la vista inicial del formulario de alta."""
    return mostrar_formulario()


@alta_controller.route("/buscar-personal", methods=["GET", "POST"])
def buscar():
    """Busca una persona por DNI para asociarle un usuario."""
    if request.method == "GET":
        return redirect(url_for("usuarios.alta_usuarios.new"))
    return buscar_personal(request.form)


@alta_controller.route("/crear-usuario", methods=["GET", "POST"])
def crear_usuario_existente():
    """Crea un usuario para un Personal ya existente."""
    if request.method == "GET":
        return redirect(url_for("usuarios.alta_usuarios.new"))
    return crear_usuario(request.form)


@alta_controller.route("/crear-personal-usuario", methods=["GET", "POST"])
def crear_alta_conjunta():
    """Crea simultáneamente Personal y Usuario."""
    if request.method == "GET":
        return redirect(url_for("usuarios.alta_usuarios.new"))
    return crear_personal_usuario(request.form)