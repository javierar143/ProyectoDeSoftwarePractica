"""Controlador para la página principal y vistas generales."""

from flask import Blueprint, render_template

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def home():
    """Renderiza la página principal de la aplicación."""
    return render_template("home.html")