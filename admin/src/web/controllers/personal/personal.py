"""Controlador para la gestión de Personal."""

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from src.core.security.permissions import require_permission
from src.core.services import configuracion as service_config
from src.core.services.personal import personal as service_personal
from src.web.validators.personal.personal import validar_datos_personal

personal_bp = Blueprint("personal", __name__, url_prefix="/personal")


def _verificar_alcance_modificacion(id_personal: int, user_id: int | None):
    """Aborta con 403 si un Jefe intenta modificar/bajar un Residente o personal de otro sector."""
    sector_forzado = service_personal.obtener_sector_forzado(user_id)
    if sector_forzado is None:
        return

    persona = service_personal.get_by_id(id_personal)
    if not persona:
        return

    sector_actual = service_personal.get_sector_asignado(id_personal)
    es_res = service_personal.es_residente(persona.idTipoPersonal)
    pertenece = (
        sector_actual is not None and sector_actual.idSector == sector_forzado
    )
    if es_res or not pertenece:
        abort(
            403,
            description="Acceso denegado: No podés modificar personal fuera de tu sector.",
        )


@personal_bp.get("")
def index():
    """Listado general de personal con filtros, orden y paginación."""
    require_permission("personal_index")

    config = service_config.obtener_configuracion()
    per_page = min(config.elementos_por_pagina, 25)

    texto_busqueda = request.args.get("q", "").strip() or None
    dni = request.args.get("dni", "").strip() or None
    id_tipo_personal = request.args.get("id_tipo_personal", type=int)
    id_sector = request.args.get("id_sector", type=int)
    estado = request.args.get("estado", "activos")
    ordenar_por = request.args.get("ordenar_por", "nombre_apellido")
    direccion = request.args.get("direccion", "asc")
    page = request.args.get("page", 1, type=int)
    user_id = session.get("user_id")

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
        user_id=user_id,
    )

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
    require_permission("personal_new")

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
    require_permission("personal_new")

    user_id = session.get("user_id")
    sector_forzado = service_personal.obtener_sector_forzado(user_id)
    tipos_personal = service_personal.get_tipos_personal()
    tipos_menu = service_personal.get_tipos_menu()
    sectores = service_personal.get_sectores()

    errores = validar_datos_personal(
        request.form,
        tipos_personal,
        tipos_menu=tipos_menu,
        sectores=sectores,
        sector_forzado=sector_forzado,
    )

    if errores:
        return (
            render_template(
                "personal/form.html",
                persona=None,
                tipos_personal=tipos_personal,
                tipos_menu=tipos_menu,
                sectores=sectores,
                errores=errores,
                valores=request.form,
            ),
            400,
        )

    id_sector = request.form.get("idSector")
    try:
        persona_creada = service_personal.create(
            dni=request.form.get("dni", "").strip(),
            nombre=request.form.get("nombre", "").strip(),
            apellido=request.form.get("apellido", "").strip(),
            id_tipo_personal=int(request.form.get("idTipoPersonal")),
            id_tipo_menu=int(request.form.get("idTipoMenu")),
            id_sector=int(id_sector) if id_sector else None,
            user_id=user_id,
        )
    except PermissionError as exc:
        abort(403, description=str(exc))
    except ValueError as exc:
        errores.append(str(exc))
        return (
            render_template(
                "personal/form.html",
                persona=None,
                tipos_personal=tipos_personal,
                tipos_menu=tipos_menu,
                sectores=sectores,
                errores=errores,
                valores=request.form,
            ),
            400,
        )

    if persona_creada is None:
        errores.append("Ya existe una persona registrada con ese DNI.")
        return (
            render_template(
                "personal/form.html",
                persona=None,
                tipos_personal=tipos_personal,
                tipos_menu=tipos_menu,
                sectores=sectores,
                errores=errores,
                valores=request.form,
            ),
            409,
        )

    flash("Personal registrado con éxito.", "success")
    return redirect(url_for("personal.index"), code=303)


@personal_bp.get("/<int:id>/editar")
def editar_form(id: int):
    """Muestra el formulario para modificar datos de una persona."""
    require_permission("personal_update")

    persona = service_personal.get_by_id(id)
    if not persona:
        flash("La persona solicitada no existe.", "danger")
        return redirect(url_for("personal.index"), code=303)

    _verificar_alcance_modificacion(id, session.get("user_id"))

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
    require_permission("personal_update")

    persona = service_personal.get_by_id(id)
    if not persona:
        flash("La persona solicitada no existe.", "danger")
        return redirect(url_for("personal.index"), code=303)

    user_id = session.get("user_id")
    _verificar_alcance_modificacion(id, user_id)

    sector_forzado = service_personal.obtener_sector_forzado(user_id)
    tipos_personal = service_personal.get_tipos_personal()
    tipos_menu = service_personal.get_tipos_menu()
    sectores = service_personal.get_sectores()
    sector_actual = service_personal.get_sector_asignado(id)

    errores = validar_datos_personal(
        request.form,
        tipos_personal,
        tipos_menu=tipos_menu,
        sectores=sectores,
        sector_forzado=sector_forzado,
    )

    if errores:
        return (
            render_template(
                "personal/form.html",
                persona=persona,
                sector_actual=sector_actual,
                tipos_personal=tipos_personal,
                tipos_menu=tipos_menu,
                sectores=sectores,
                errores=errores,
                valores=request.form,
            ),
            400,
        )

    id_sector = request.form.get("idSector")
    try:
        persona_actualizada = service_personal.update(
            id_personal=id,
            dni=request.form.get("dni", "").strip(),
            nombre=request.form.get("nombre", "").strip(),
            apellido=request.form.get("apellido", "").strip(),
            id_tipo_personal=int(request.form.get("idTipoPersonal")),
            id_tipo_menu=int(request.form.get("idTipoMenu")),
            id_sector=int(id_sector) if id_sector else None,
            user_id=user_id,
        )
    except PermissionError as exc:
        abort(403, description=str(exc))
    except ValueError as exc:
        errores.append(str(exc))
        return (
            render_template(
                "personal/form.html",
                persona=persona,
                sector_actual=sector_actual,
                tipos_personal=tipos_personal,
                tipos_menu=tipos_menu,
                sectores=sectores,
                errores=errores,
                valores=request.form,
            ),
            400,
        )

    if persona_actualizada is None:
        errores.append("El DNI ingresado ya pertenece a otra persona.")
        return (
            render_template(
                "personal/form.html",
                persona=persona,
                sector_actual=sector_actual,
                tipos_personal=tipos_personal,
                tipos_menu=tipos_menu,
                sectores=sectores,
                errores=errores,
                valores=request.form,
            ),
            409,
        )

    flash("Datos actualizados correctamente.", "success")
    return redirect(url_for("personal.index"), code=303)


@personal_bp.post("/<int:id>/eliminar")
def eliminar(id: int):
    """Elimina al personal o lo desactiva si tiene historial asociado."""
    require_permission("personal_destroy")

    _verificar_alcance_modificacion(id, session.get("user_id"))

    exito, accion = service_personal.eliminar_personal(id)
    if exito:
        if accion == "eliminado":
            flash("Personal eliminado correctamente.", "success")
        elif accion == "inactivado":
            flash(
                "El personal no pudo eliminarse porque tiene historial de viandas. Fue marcado como inactivo.",
                "warning",
            )
    else:
        flash("No se encontró el registro solicitado.", "danger")
    return redirect(url_for("personal.index"), code=303)


@personal_bp.post("/<int:id>/activar")
def activar(id: int):
    """Reactivación de personal inactivo."""
    require_permission("personal_update")

    _verificar_alcance_modificacion(id, session.get("user_id"))

    exito = service_personal.set_active(id_personal=id, is_active=True)
    if exito:
        flash("Se activó al personal correctamente.", "success")
    else:
        flash("No se encontró el registro.", "danger")
    return redirect(url_for("personal.index"), code=303)