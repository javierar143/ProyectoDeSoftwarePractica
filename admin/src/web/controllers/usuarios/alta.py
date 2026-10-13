"""Controlador HTTP para el alta de usuarios."""

from flask import Blueprint, request

from src.core.security.permissions import require_permission
from src.web.controllers.usuarios.alta_acciones import (
    mostrar_formulario,
    procesar_alta,
)


alta_controller = Blueprint("alta_usuarios", __name__)


@alta_controller.route("/nuevo", methods=["GET", "POST"])
def new():
    """Muestra el formulario o procesa la acción solicitada."""
    require_permission("user_new")

    if request.method == "GET":
        return mostrar_formulario()

    return procesar_alta(request.form)
