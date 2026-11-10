"""Controlador para la importación masiva de personal."""

from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from src.core.services.personal import csv_service
from src.core.security.permissions import require_permission

personal_csv_bp = Blueprint("personal_csv", __name__, url_prefix="/personal")

@personal_csv_bp.get("/importar")
def importar_form():
    """Muestra el formulario para subir el archivo CSV."""
    require_permission("personal_import")
    return render_template("personal/importar.html")

@personal_csv_bp.post("/importar")
def importar_procesar():
    """Recibe el archivo, lo pasa a texto y delega el procesamiento al servicio."""
    require_permission("personal_import")
    
    archivo = request.files.get("archivo_csv")
    
    if not archivo or archivo.filename == "":
        flash("No se seleccionó ningún archivo.", "danger")
        return redirect(url_for("personal_csv.importar_form"), code=303)

    if not archivo.filename.endswith('.csv'):
        flash("El archivo debe tener extensión .csv", "danger")
        return redirect(url_for("personal_csv.importar_form"), code=303)

    # Leo el archivo en memoria y lo decodificamos a string
    contenido_csv = archivo.stream.read().decode("UTF8")
    
    # Obtengo el user_id para enviarlo al servicio (por la regla del Jefe de Sector)
    user_id = session.get("user_id")

    resultados = csv_service.procesar_csv(contenido_csv, user_id)

    return render_template("personal/importar_resultados.html", resultados=resultados)