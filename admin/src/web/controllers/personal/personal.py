"""Controlador para la gestión de Personal."""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from src.core.services.personal import personal as service_personal
from src.core.services import configuracion as service_config
from src.web.validators.personal.personal import validar_datos_personal

personal_bp = Blueprint("personal", __name__, url_prefix="/personal")

@personal_bp.get("")
def index():
    """Listado general de personal con filtros, orden y paginación."""
    # configuración de paginado del sistema
    config = service_config.obtener_configuracion()
    per_page = config.elementos_por_pagina

    # lectura de parametros de busqueda y filtros
    texto_busqueda = request.args.get("q", "").strip() or None
    dni = request.args.get("dni", "").strip() or None
    id_tipo_personal = request.args.get("id_tipo_personal", type=int)
    id_sector = request.args.get("id_sector", type=int)
    estado = request.args.get("estado", "activos")
    ordenar_por = request.args.get("ordenar_por", "nombre_apellido")
    direccion = request.args.get("direccion", "asc")
    page = request.args.get("page", 1, type=int)

    # consulta al servicio
    resultado_paginado = service_personal.search(
        texto_busqueda=texto_busqueda,
        dni=dni,
        id_tipo_personal=id_tipo_personal,
        id_sector=id_sector,
        estado=estado,
        ordenar_por=ordenar_por,
        direccion=direccion,
        page=page,
        per_page=per_page,
    )

    # catalogos para los selectores del formulario de filtros
    tipos_personal = service_personal.get_tipos_personal()
    sectores = service_personal.get_sectores()

    return render_template(
        "personal/index.html",
        personal_paginado=resultado_paginado,
        personal=resultado_paginado["items"],
        tipos_personal=tipos_personal,
        sectores=sectores,
        filtros={
            "q": texto_busqueda or "",
            "dni": dni or "",
            "id_tipo_personal": id_tipo_personal,
            "id_sector": id_sector,
            "estado": estado,
            "ordenar_por": ordenar_por,
            "direccion": direccion,
        },
    )


@personal_bp.get("/nuevo")
def nuevo_form():
    """Muestra el formulario vacío para cargar un nuevo empleado."""
    tipos_personal = service_personal.get_tipos_personal()
    tipos_menu = service_personal.get_tipos_menu()
    sectores = service_personal.get_sectores()
    return render_template(
        "personal/form.html",
        persona=None,
        tipos_personal=tipos_personal,
        tipos_menu=tipos_menu,
        sectores=sectores,
    )


@personal_bp.post("/nuevo")
def nuevo():
    """Procesa el formulario y da de alta a la persona mediante el servicio."""
    tipos_personal = service_personal.get_tipos_personal()
    
    # validacion delegada al modulo correspondiente
    errores = validar_datos_personal(request.form, tipos_personal)

    tipos_menu = service_personal.get_tipos_menu()
    sectores = service_personal.get_sectores()

    # si hay errores de validacion, volvemos al formulario
    if errores:
        return render_template(
            "personal/form.html",
            persona=None,
            tipos_personal=tipos_personal,
            tipos_menu=tipos_menu,
            sectores=sectores,
            errores=errores,
            valores=request.form,
        ), 400

    # inserción a traves del servicio
    id_sector = request.form.get("idSector")
    persona_creada = service_personal.create(
        dni=request.form.get("dni", "").strip(),
        nombre=request.form.get("nombre", "").strip(),
        apellido=request.form.get("apellido", "").strip(),
        id_tipo_personal=int(request.form.get("idTipoPersonal")),
        id_tipo_menu=int(request.form.get("idTipoMenu")),
        id_sector=int(id_sector) if id_sector else None,
    )

    if persona_creada is None:
        errores.append("Ya existe una persona registrada con ese DNI.")
        return render_template(
            "personal/form.html",
            persona=None,
            tipos_personal=tipos_personal,
            tipos_menu=tipos_menu,
            sectores=sectores,
            errores=errores,
            valores=request.form,
        ), 400

    flash("Personal registrado con éxito.", "success")
    return redirect(url_for("personal.index"), code=303)


@personal_bp.get("/<int:id>/editar")
def editar_form(id: int):
    """Muestra el formulario para modificar datos de una persona."""
    persona = service_personal.get_by_id(id)
    if not persona:
        flash("La persona solicitada no existe.", "danger")
        return redirect(url_for("personal.index"), code=303)

    sector_actual = service_personal.get_sector_asignado(id)
    tipos_personal = service_personal.get_tipos_personal()
    tipos_menu = service_personal.get_tipos_menu()
    sectores = service_personal.get_sectores()

    return render_template(
        "personal/form.html",
        persona=persona,
        sector_actual=sector_actual,
        tipos_personal=tipos_personal,
        tipos_menu=tipos_menu,
        sectores=sectores,
    )


@personal_bp.post("/<int:id>/editar")
def editar(id: int):
    """Aplica las modificaciones llamando al servicio."""
    persona = service_personal.get_by_id(id)
    if not persona:
        flash("La persona solicitada no existe.", "danger")
        return redirect(url_for("personal.index"), code=303)

    tipos_personal = service_personal.get_tipos_personal()
    
    # validacion delegada al modulo aparte
    errores = validar_datos_personal(request.form, tipos_personal)

    tipos_menu = service_personal.get_tipos_menu()
    sectores = service_personal.get_sectores()
    sector_actual = service_personal.get_sector_asignado(id)

    if errores:
        return render_template(
            "personal/form.html",
            persona=persona,
            sector_actual=sector_actual,
            tipos_personal=tipos_personal,
            tipos_menu=tipos_menu,
            sectores=sectores,
            errores=errores,
            valores=request.form,
        ), 400

    # actualizacion a traves del servicio
    id_sector = request.form.get("idSector")
    persona_actualizada = service_personal.update(
        id_personal=id,
        dni=request.form.get("dni", "").strip(),
        nombre=request.form.get("nombre", "").strip(),
        apellido=request.form.get("apellido", "").strip(),
        id_tipo_personal=int(request.form.get("idTipoPersonal")),
        id_tipo_menu=int(request.form.get("idTipoMenu")),
        id_sector=int(id_sector) if id_sector else None
    )

    if persona_actualizada is None:
        errores.append("El DNI ingresado ya pertenece a otra persona.")
        return render_template(
            "personal/form.html",
            persona=persona,
            sector_actual=sector_actual,
            tipos_personal=tipos_personal,
            tipos_menu=tipos_menu,
            sectores=sectores,
            errores=errores,
            valores=request.form,
        ), 400

    flash("Datos actualizados correctamente.", "success")
    return redirect(url_for("personal.index"), code=303)


@personal_bp.post("/<int:id>/desactivar")
def desactivar(id: int):
    """Baja lógica delegada al servicio."""
    exito = service_personal.set_active(id_personal=id, is_active=False)
    if exito:
        flash("Se desactivó al personal correctamente.", "info")
    else:
        flash("No se encontró el registro.", "danger")

    return redirect(url_for("personal.index"), code=303)

@personal_bp.post("/<int:id>/activar")
def activar(id: int):
    """Reactivación de personal inactivo."""
    exito = service_personal.set_active(id_personal=id, is_active=True)
    if exito:
        flash("Se activó al personal correctamente.", "success")
    else:
        flash("No se encontró el registro.", "danger")

    return redirect(url_for("personal.index"), code=303)