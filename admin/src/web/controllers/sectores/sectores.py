"""Controlador para la gestión de sectores"""

from flask import Blueprint, render_template

sectores_bp = Blueprint("sectores", __name__, url_prefix="/sectores")


@sectores_bp.get("")
def index():
    """Muestra el listado de sectores."""
    return render_template("sectores/index.html")