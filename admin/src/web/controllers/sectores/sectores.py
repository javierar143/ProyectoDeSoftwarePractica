"""Controlador para la gestión de sectores."""

import math

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from src.core.security.session import get_authenticated_user_id, require_authentication
from src.core.services import configuracion as config_service
from src.core.services.sectores import sector as sector_service
from src.core.services.sectores.sector import SectorError
from src.core.services.usuarios import usuario as usuario_service
from src.web.validators.sectores.sectores import (
    parse_search_params,
    validate_jefes_ids,
    validate_sector_data,
)

MAX_POR_PAGINA = 25

sectores_bp = Blueprint("sectores", __name__, url_prefix="/sectores")


@sectores_bp.before_request
def require_admin():
    """Exige un administrador autenticado para cualquier ruta del módulo."""
    require_authentication()
    usuario_actual = usuario_service.get_by_id(get_authenticated_user_id())
    if usuario_actual is None or not usuario_actual.isSystemAdmin:
        abort(403)


def _render_form(sector, errores=None, valores=None, status=200):
    """Renderiza el formulario de sector con sus datos auxiliares."""
    jefes_actuales = sector_service.get_jefes(sector.idSector) if sector else []
    return render_template(
        "sectores/form.html",
        sector=sector,
        errores=errores or [],
        valores=valores or {},
        jefes_actuales=jefes_actuales,
        jefes_disponibles=sector_service.get_jefes_disponibles(),
    ), status


def _leer_formulario():
    """Obtiene y valida los datos enviados en el formulario de sector."""
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    ids_jefes, errores = validate_jefes_ids(request.form.getlist("jefes"))
    errores += validate_sector_data(nombre, descripcion)
    return nombre, descripcion, ids_jefes, errores


@sectores_bp.get("")
def index():
    """Lista los sectores aplicando búsqueda, orden y paginado."""
    filtros = parse_search_params(request.args)
    por_pagina = min(config_service.obtener_configuracion().elementos_por_pagina, MAX_POR_PAGINA)
    sectores, total = sector_service.search(**filtros, per_page=por_pagina)
    total_paginas = max(1, math.ceil(total / por_pagina))

    query_args = request.args.to_dict()
    query_args.pop("page", None)

    return render_template(
        "sectores/index.html",
        sectores=sectores,
        total=total,
        filtros=filtros,
        pagina=filtros["page"],
        total_paginas=total_paginas,
        query_args=query_args,
        jefes=sector_service.get_todos_los_jefes(),
    )


@sectores_bp.get("/nuevo")
def nuevo_form():
    """Muestra el formulario vacío de alta de sector."""
    return _render_form(sector=None)


@sectores_bp.post("/nuevo")
def nuevo():
    """Procesa el alta de un sector."""
    nombre, descripcion, ids_jefes, errores = _leer_formulario()
    if errores:
        return _render_form(None, errores, request.form, 400)

    try:
        sector_service.create(nombre, descripcion, ids_jefes)
    except SectorError as error:
        return _render_form(None, [str(error)], request.form, 400)

    flash("Sector creado correctamente.", "success")
    return redirect(url_for("sectores.index"), code=303)


@sectores_bp.get("/<int:id>/editar")
def editar_form(id: int):
    """Muestra el formulario de edición de un sector."""
    sector = sector_service.get_by_id(id)
    if sector is None:
        abort(404)
    return _render_form(sector)


@sectores_bp.post("/<int:id>/editar")
def editar(id: int):
    """Procesa la modificación de un sector."""
    sector = sector_service.get_by_id(id)
    if sector is None:
        abort(404)

    nombre, descripcion, ids_jefes, errores = _leer_formulario()
    if errores:
        return _render_form(sector, errores, request.form, 400)

    try:
        sector_service.update(id, nombre, descripcion, ids_jefes)
    except SectorError as error:
        return _render_form(sector, [str(error)], request.form, 400)

    flash("Sector actualizado correctamente.", "success")
    return redirect(url_for("sectores.index"), code=303)


@sectores_bp.post("/<int:id>/activar")
def activar(id: int):
    """Reactiva un sector."""
    try:
        sector_service.activar(id)
        flash("Sector activado.", "success")
    except SectorError as error:
        flash(str(error), "danger")
    return redirect(url_for("sectores.index"), code=303)


@sectores_bp.post("/<int:id>/desactivar")
def desactivar(id: int):
    """Desactiva un sector."""
    try:
        sector_service.desactivar(id)
        flash("Sector desactivado.", "info")
    except SectorError as error:
        flash(str(error), "danger")
    return redirect(url_for("sectores.index"), code=303)


@sectores_bp.post("/<int:id>/eliminar")
def eliminar(id: int):
    """Elimina un sector o lo desactiva si tiene registros asociados."""
    try:
        resultado = sector_service.eliminar(id)
        if resultado == "eliminado":
            flash("Sector eliminado.", "success")
        else:
            flash("El sector tiene registros asociados: se desactivó en lugar de eliminarse.", "warning")
    except SectorError as error:
        flash(str(error), "danger")
    return redirect(url_for("sectores.index"), code=303)