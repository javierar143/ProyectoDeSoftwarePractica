
"""Registro centralizado de las rutas de administración de usuarios."""

from flask import Blueprint

from src.web.controllers.usuarios.alta import alta_controller
from src.web.controllers.usuarios.edicion import edicion_controller
from src.web.controllers.usuarios.listado import listado_controller


usuarios_controller = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/usuarios",
)

usuarios_controller.register_blueprint(
    listado_controller,
    url_prefix="",
)

usuarios_controller.register_blueprint(
    alta_controller,
    url_prefix="",
)

usuarios_controller.register_blueprint(
    edicion_controller,
    url_prefix="",
)
