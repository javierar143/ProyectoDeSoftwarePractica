"""Controlador para la gestión de Personal."""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    session,
    abort
)
from src.core.services.personal import personal as service_personal
from src.core.services import configuracion as service_config
from src.web.validators.personal.personal import validar_datos_personal
from src.core.services.usuarios import usuario as service_usuario
from src.core.services.usuarios import rol as service_rol
from src.core.security.session import require_authentication
import csv, io

personal_bp = Blueprint("personal", __name__, url_prefix="/personal")

@personal_bp.before_request
def require_auth():
    """Exige autenticación para cualquier ruta dentro del módulo personal."""
    require_authentication()


@personal_bp.get("")
def index():
    """Listado general de personal con filtros, orden y paginación."""
    # configuracion de paginado del sistema
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

    user_id = session.get("user_id")
    sector_forzado_jefe = None
    
    if user_id:
        usuario_actual = service_usuario.get_by_id(user_id)
        if usuario_actual and usuario_actual.idRol:
            rol_usuario = service_rol.get_by_id(usuario_actual.idRol)
            if rol_usuario:
                nombre_rol = rol_usuario.nombre.strip().lower()
                # si es Jefe, fuerzo su sector asignado
                if "jefe" in nombre_rol:
                    sector_forzado_jefe = usuario_actual.idSector
                    id_sector = sector_forzado_jefe

    # consulta al servicio 
    resultado_paginado = service_personal.search(
        texto_busqueda=texto_busqueda,
        dni=dni,
        id_tipo_personal=id_tipo_personal,
        id_sector=id_sector,
        sector_forzado_jefe=sector_forzado_jefe, 
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

    user_id = session.get("user_id")
    if user_id:
        usuario_actual = service_usuario.get_by_id(user_id) 
        rol_usuario = service_rol.get_by_id(usuario_actual.idRol)

        id_tipo_personal_form = int(request.form.get("idTipoPersonal"))
        
        nombre_rol = rol_usuario.nombre.strip().lower()
        es_servicio_alimentacion = nombre_rol == "Alimentación"
        if id_tipo_personal_form == 2 and not es_servicio_alimentacion:
            # si el usuario no tiene el rol de Servicio de Alimentacion y esta intentando crear un personal de tipo Residente denegamos el acceso
            abort(403, description="Acceso denegado: Solo el Servicio de Alimentación puede administrar Residentes.")

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
        ), 409

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
        ), 409

    flash("Datos actualizados correctamente.", "success")
    return redirect(url_for("personal.index"), code=303)


@personal_bp.post("/<int:id>/eliminar")
def eliminar(id: int):
    """Elimina al personal o lo desactiva si tiene historial asociado."""
    exito, accion = service_personal.eliminar_personal(id)
    
    if exito:
        if accion == "eliminado":
            flash("Personal eliminado correctamente.", "success")
        elif accion == "inactivado":
            flash("El personal no pudo eliminarse porque tiene historial de viandas. Fue marcado como inactivo.", "warning")
    else:
        flash("No se encontró el registro solicitado.", "danger")

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

@personal_bp.get("/importar")
def importar_form():
    """Muestra el formulario para subir el archivo CSV."""
    return render_template("personal/importar.html")

@personal_bp.post("/importar")
def importar_procesar():
    """Procesa el archivo CSV subido traduciendo nombres a IDs."""
    archivo = request.files.get("archivo_csv")
    
    if not archivo or archivo.filename == "":
        flash("No se seleccionó ningún archivo.", "danger")
        return redirect(url_for("personal.importar_form"), code=303)

    if not archivo.filename.endswith('.csv'):
        flash("El archivo debe tener extensión .csv", "danger")
        return redirect(url_for("personal.importar_form"), code=303)

    stream = io.StringIO(archivo.stream.read().decode("UTF8"), newline=None)
    csv_reader = csv.DictReader(stream)

    # traer catalogos del servicio
    tipos_personal = service_personal.get_tipos_personal()
    tipos_menu = service_personal.get_tipos_menu()
    sectores = service_personal.get_sectores()

    # crear diccionarios de traduccion (nombre en minuscula -> ID)
    map_tipos_personal = {t.nombre.strip().lower(): t.idTipoPersonal for t in tipos_personal}
    map_tipos_menu = {m.nombre.strip().lower(): m.idTipoMenu for m in tipos_menu}
    map_sectores = {s.nombre.strip().lower(): s.idSector for s in sectores}

    resultados = {
        "total": 0,
        "exitosos": 0,
        "fallidos": 0,
        "detalles_errores": [],
        "detalles_exitosos": []  
    }

    # procesar fila por fila
    for fila_num, fila in enumerate(csv_reader, start=2):
        resultados["total"] += 1
        
        # quito espacios y saltos de línea (\r) de las columnas y valores
        fila_limpia = {str(k).strip().lower(): str(v).strip() for k, v in fila.items() if k is not None}

        nombre_tipo = fila_limpia.get("tipo_personal", "").lower()
        nombre_menu = fila_limpia.get("tipo_menu", "").lower()
        nombre_sector = fila_limpia.get("sector", "").lower()

        # traduzco a IDs y fuerzo a string (para que el validador lo vea igual que un formulario web)
        id_tipo_pers = str(map_tipos_personal.get(nombre_tipo, ""))
        id_tipo_menu = str(map_tipos_menu.get(nombre_menu, ""))
        id_sec = str(map_sectores.get(nombre_sector, "")) if nombre_sector else ""

        datos_validacion = {
            "dni": fila_limpia.get("dni", ""),
            "nombre": fila_limpia.get("nombre", ""),
            "apellido": fila_limpia.get("apellido", ""),
            "idTipoPersonal": id_tipo_pers,
            "idTipoMenu": id_tipo_menu,
            "idSector": id_sec
        }

        errores_fila = validar_datos_personal(datos_validacion, tipos_personal)

        if errores_fila:
            resultados["fallidos"] += 1
            resultados["detalles_errores"].append({
                "fila": fila_num,
                "persona": f"{datos_validacion['nombre']} {datos_validacion['apellido']} (DNI: {datos_validacion['dni']})",
                "errores": errores_fila
            })
            continue

        try:
            persona_creada = service_personal.create(
                dni=datos_validacion["dni"],
                nombre=datos_validacion["nombre"],
                apellido=datos_validacion["apellido"],
                id_tipo_personal=int(id_tipo_pers),
                id_tipo_menu=int(id_tipo_menu),
                id_sector=int(id_sec) if id_sec else None
            )
            
            if persona_creada is None:
                resultados["fallidos"] += 1
                resultados["detalles_errores"].append({
                    "fila": fila_num,
                    "persona": f"{datos_validacion['nombre']} {datos_validacion['apellido']} (DNI: {datos_validacion['dni']})",
                    "errores": ["Ya existe una persona registrada con este DNI."]
                })
            else:
                resultados["exitosos"] += 1
                resultados["detalles_exitosos"].append(
                    f"{datos_validacion['nombre']} {datos_validacion['apellido']} (DNI: {datos_validacion['dni']})"
                )
                
        except Exception as e:
            current_app.logger.error(f"Error inesperado al importar personal DNI {datos_validacion['dni']}: {str(e)}")
            
            resultados["fallidos"] += 1
            resultados["detalles_errores"].append({
                "fila": fila_num,
                "persona": f"DNI: {datos_validacion['dni']}",
                "errores": ["Error interno al guardar en la base de datos."]
            })

    # log informativo al terminar todo el CSV
    current_app.logger.info(f"Importación CSV de personal finalizada: {resultados['exitosos']} exitosos, {resultados['fallidos']} rechazados.")

    return render_template("personal/importar_resultados.html", resultados=resultados)