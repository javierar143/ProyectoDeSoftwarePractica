
"""Controladores REST para la gestión de Personal."""

from datetime import date

from flask import Blueprint, g, jsonify, request

from src.core.services.personal import personal as service_personal
from src.core.services.usuarios import permiso as service_permiso
from src.core.services.sectores import sector as service_sector
from src.web.decorators.api import (
    permission_required,
    sector_assignment_required,
    token_required,
)
from src.web.validators.personal.personal import validar_datos_personal


api_personal_controller = Blueprint(
    "api_personal",
    __name__,
    url_prefix="/api",
)


def _serializar_persona(persona) -> dict:
    """Convierte un objeto Personal en un diccionario serializable a JSON."""
    sector = getattr(persona, "sector_asignado", None)

    if sector is None:
        sector = service_personal.get_sector_asignado(persona.idPersonal)

    return {
        "id": persona.idPersonal,
        "dni": persona.dni,
        "nombre": persona.nombre,
        "apellido": persona.apellido,
        "activo": persona.isActive,
        "id_tipo_personal": persona.idTipoPersonal,
        "id_tipo_menu": persona.idTipoMenu,
        "sector": {
            "id": sector.idSector,
            "nombre": sector.nombre,
        } if sector else None,
    }


# GET /api/personnel — Buscar y listar personal
@api_personal_controller.get("/personnel")
@token_required
@permission_required("personal_index")
@sector_assignment_required
def listar_personal():
    """Busca y lista personal con filtros y paginación (máximo 25 por página)."""
    user = g.user

    texto_busqueda = (
        request.args.get("q")
        or request.args.get("nombre")
        or request.args.get("nya")
        or ""
    ).strip() or None

    dni = (request.args.get("dni") or "").strip() or None
    estado = (request.args.get("estado") or "activos").strip().lower()

    if estado not in ("activos", "inactivos", "todos"):
        return jsonify({"error": "El filtro 'estado' es inválido"}), 400

    try:
        tipo_param = (
            request.args.get("tipo_personal")
            or request.args.get("id_tipo_personal")
        )
        id_tipo_personal = (
            int(tipo_param)
            if tipo_param is not None and tipo_param != ""
            else None
        )

        sector_param = (
            request.args.get("sector")
            or request.args.get("id_sector")
        )
        id_sector = (
            int(sector_param)
            if sector_param is not None and sector_param != ""
            else None
        )

        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 25))

    except ValueError:
        return jsonify({
            "error": "Los filtros numéricos o de paginación son inválidos"
        }), 400

    if page < 1 or per_page < 1 or per_page > 25:
        return jsonify({
            "error": "Paginación inválida (máximo 25 por página)"
        }), 400

    resultado = service_personal.search(
        texto_busqueda=texto_busqueda,
        dni=dni,
        id_tipo_personal=id_tipo_personal,
        id_sector=id_sector,
        sector_forzado_jefe=g.sector_forzado,
        estado=estado,
        page=page,
        per_page=per_page,
        user_id=None,
    )

    return jsonify({
        "items": [_serializar_persona(p) for p in resultado["items"]],
        "total": resultado["total"],
        "page": resultado["page"],
        "per_page": resultado["per_page"],
        "pages": resultado["pages"],
    }), 200


# GET /api/personnel/<int:person_id> — Obtener una persona
@api_personal_controller.get("/personnel/<int:person_id>")
@token_required
@permission_required("personal_index")
@sector_assignment_required
def obtener_persona(person_id: int):
    """Obtiene los datos completos de una persona verificando alcance por sector."""
    persona = service_personal.get_by_id(person_id)

    if persona is None:
        return jsonify({"error": "Persona no encontrada"}), 404

    sector_forzado = g.sector_forzado
    sector_persona = service_personal.get_sector_asignado(person_id)
    es_res = service_personal.es_residente(persona.idTipoPersonal)

    if sector_forzado is not None:
        pertenece_a_su_sector = (
            sector_persona is not None
            and sector_persona.idSector == sector_forzado
        )

        if not pertenece_a_su_sector and not es_res:
            return jsonify({
                "error": "No tenés permisos para consultar personal de otro sector"
            }), 403

    persona.sector_asignado = sector_persona

    return jsonify(_serializar_persona(persona)), 200


# GET /api/sectors/<int:sector_id>/personnel — Listar personal de un sector
@api_personal_controller.get("/sectors/<int:sector_id>/personnel")
@token_required
@permission_required("personal_index")
@sector_assignment_required
def listar_personal_de_sector(sector_id: int):
    """Lista el personal activo perteneciente a un sector específico."""
    sector_forzado = g.sector_forzado

    if sector_forzado is not None and sector_forzado != sector_id:
        return jsonify({
            "error": "No tenés permisos para consultar el personal de otro sector"
        }), 403

    sector = service_sector.get_by_id(sector_id)

    if sector is None:
        return jsonify({"error": "El sector indicado no existe"}), 404

    fecha_str = request.args.get("fecha")

    if fecha_str:
        try:
            date.fromisoformat(fecha_str)
        except ValueError:
            return jsonify({
                "error": "Formato de fecha inválido. Use YYYY-MM-DD"
            }), 400

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 25))
    except ValueError:
        return jsonify({
            "error": "Parámetros de paginación inválidos"
        }), 400

    if page < 1 or per_page < 1 or per_page > 25:
        return jsonify({
            "error": "Paginación inválida (máximo 25 por página)"
        }), 400

    resultado = service_personal.search(
        id_sector=sector_id,
        estado="activos",
        page=page,
        per_page=per_page,
        user_id=None,
    )

    return jsonify({
        "items": [_serializar_persona(p) for p in resultado["items"]],
        "total": resultado["total"],
        "page": resultado["page"],
        "per_page": resultado["per_page"],
        "pages": resultado["pages"],
    }), 200


# POST /api/personnel — Crear una persona
@api_personal_controller.post("/personnel")
@token_required
@permission_required("personal_new")
@sector_assignment_required
def crear_persona():
    """Crea una persona validando permisos de rol, sector y unicidad de DNI."""
    user = g.user
    sector_forzado = g.sector_forzado

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "El cuerpo de la solicitud debe ser JSON"
        }), 400

    tipo_personal_raw = (
        data.get("idTipoPersonal")
        if "idTipoPersonal" in data
        else data.get("tipo_personal")
    )

    tipo_menu_raw = (
        data.get("idTipoMenu")
        if "idTipoMenu" in data
        else data.get("tipo_menu")
    )

    sector_raw = (
        data.get("idSector")
        if "idSector" in data
        else data.get("sector")
    )

    tipos_personal = service_personal.get_tipos_personal()
    ids_tipos_validos = {t.idTipoPersonal for t in tipos_personal}

    try:
        id_tipo_personal = int(tipo_personal_raw)
    except (ValueError, TypeError):
        return jsonify({
            "error": "El tipo de personal es obligatorio y debe ser válido"
        }), 400

    if id_tipo_personal not in ids_tipos_validos:
        return jsonify({
            "error": "El tipo de personal indicado no existe"
        }), 400

    es_res = service_personal.es_residente(id_tipo_personal)

    if es_res and not service_permiso.user_has_role_permission(
        user.id_user,
        "personal_create_residente",
    ):
        return jsonify({
            "error": "No tenés permisos para crear personas de tipo Residente"
        }), 403

    if sector_forzado is not None:
        if sector_raw is not None and str(sector_raw).strip() != "":
            try:
                if int(sector_raw) != sector_forzado:
                    return jsonify({
                        "error": "No tenés permisos para crear personal fuera de tu sector"
                    }), 403
            except ValueError:
                return jsonify({
                    "error": "El sector indicado es inválido"
                }), 400

        id_sector_final = sector_forzado
    else:
        id_sector_final = None if es_res else sector_raw

    datos_formulario = {
        "dni": str(data.get("dni") or "").strip(),
        "nombre": str(data.get("nombre") or "").strip(),
        "apellido": str(data.get("apellido") or "").strip(),
        "idTipoPersonal": str(id_tipo_personal),
        "idTipoMenu": (
            str(tipo_menu_raw) if tipo_menu_raw is not None else ""
        ),
        "idSector": (
            str(id_sector_final)
            if id_sector_final is not None and str(id_sector_final) != ""
            else ""
        ),
    }

    errores = validar_datos_personal(datos_formulario, tipos_personal)

    if errores:
        return jsonify({
            "error": errores[0],
            "errores": errores,
        }), 400

    id_tipo_menu = int(datos_formulario["idTipoMenu"])
    ids_menus_validos = {
        m.idTipoMenu for m in service_personal.get_tipos_menu()
    }

    if id_tipo_menu not in ids_menus_validos:
        return jsonify({
            "error": "El tipo de menú indicado no existe"
        }), 400

    id_sector_int = (
        int(datos_formulario["idSector"])
        if datos_formulario["idSector"]
        else None
    )

    if (
        id_sector_int is not None
        and service_sector.get_by_id(id_sector_int) is None
    ):
        return jsonify({
            "error": "El sector indicado no existe"
        }), 400

    try:
        nueva_persona = service_personal.create(
            dni=datos_formulario["dni"],
            nombre=datos_formulario["nombre"],
            apellido=datos_formulario["apellido"],
            id_tipo_personal=id_tipo_personal,
            id_tipo_menu=id_tipo_menu,
            id_sector=id_sector_int,
            user_id=None,
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    if nueva_persona is None:
        return jsonify({
            "error": (
                "Ya existe una persona registrada con ese DNI o fue utilizada "
                "anteriormente en el sistema"
            )
        }), 409

    return jsonify(_serializar_persona(nueva_persona)), 201


# PUT /api/personnel/<int:person_id> — Modificar una persona
@api_personal_controller.put("/personnel/<int:person_id>")
@token_required
@permission_required("personal_update")
@sector_assignment_required
def modificar_persona(person_id: int):
    """Modifica los datos de una persona existente validando alcance y transiciones."""
    user = g.user
    sector_forzado = g.sector_forzado

    persona_actual = service_personal.get_by_id(person_id)

    if persona_actual is None:
        return jsonify({"error": "Persona no encontrada"}), 404

    sector_actual = service_personal.get_sector_asignado(person_id)
    era_residente = service_personal.es_residente(
        persona_actual.idTipoPersonal
    )

    if sector_forzado is not None:
        pertenece_a_su_sector = (
            sector_actual is not None
            and sector_actual.idSector == sector_forzado
        )

        if era_residente or not pertenece_a_su_sector:
            return jsonify({
                "error": "No tenés permisos para modificar esta persona"
            }), 403

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "El cuerpo de la solicitud debe ser JSON"
        }), 400

    tipo_personal_raw = (
        data.get("idTipoPersonal")
        if "idTipoPersonal" in data
        else data.get("tipo_personal")
    )

    tipo_menu_raw = (
        data.get("idTipoMenu")
        if "idTipoMenu" in data
        else data.get("tipo_menu")
    )

    sector_raw = (
        data.get("idSector")
        if "idSector" in data
        else data.get("sector")
    )

    tipos_personal = service_personal.get_tipos_personal()
    ids_tipos_validos = {t.idTipoPersonal for t in tipos_personal}

    try:
        id_tipo_personal = int(tipo_personal_raw)
    except (ValueError, TypeError):
        return jsonify({
            "error": "El tipo de personal es obligatorio y debe ser válido"
        }), 400

    if id_tipo_personal not in ids_tipos_validos:
        return jsonify({
            "error": "El tipo de personal indicado no existe"
        }), 400

    pasa_a_residente = service_personal.es_residente(id_tipo_personal)

    if pasa_a_residente and not service_permiso.user_has_role_permission(
        user.id_user,
        "personal_create_residente",
    ):
        return jsonify({
            "error": "No tenés permisos para asignar el tipo Residente"
        }), 403

    if sector_forzado is not None:
        if sector_raw is not None and str(sector_raw).strip() != "":
            try:
                if int(sector_raw) != sector_forzado:
                    return jsonify({
                        "error": "No tenés permisos para trasladar personal a otro sector"
                    }), 403
            except ValueError:
                return jsonify({
                    "error": "El sector indicado es inválido"
                }), 400

        id_sector_final = sector_forzado
    else:
        id_sector_final = None if pasa_a_residente else sector_raw

    datos_formulario = {
        "dni": str(data.get("dni") or "").strip(),
        "nombre": str(data.get("nombre") or "").strip(),
        "apellido": str(data.get("apellido") or "").strip(),
        "idTipoPersonal": str(id_tipo_personal),
        "idTipoMenu": (
            str(tipo_menu_raw) if tipo_menu_raw is not None else ""
        ),
        "idSector": (
            str(id_sector_final)
            if id_sector_final is not None and str(id_sector_final) != ""
            else ""
        ),
    }

    errores = validar_datos_personal(datos_formulario, tipos_personal)

    if errores:
        return jsonify({
            "error": errores[0],
            "errores": errores,
        }), 400

    id_tipo_menu = int(datos_formulario["idTipoMenu"])
    ids_menus_validos = {
        m.idTipoMenu for m in service_personal.get_tipos_menu()
    }

    if id_tipo_menu not in ids_menus_validos:
        return jsonify({
            "error": "El tipo de menú indicado no existe"
        }), 400

    id_sector_int = (
        int(datos_formulario["idSector"])
        if datos_formulario["idSector"]
        else None
    )

    if (
        id_sector_int is not None
        and service_sector.get_by_id(id_sector_int) is None
    ):
        return jsonify({
            "error": "El sector indicado no existe"
        }), 400

    try:
        persona_actualizada = service_personal.update(
            id_personal=person_id,
            dni=datos_formulario["dni"],
            nombre=datos_formulario["nombre"],
            apellido=datos_formulario["apellido"],
            id_tipo_personal=id_tipo_personal,
            id_tipo_menu=id_tipo_menu,
            id_sector=id_sector_int,
            user_id=None,
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    if persona_actualizada is None:
        return jsonify({
            "error": "El DNI ingresado ya corresponde a otra persona registrada"
        }), 409

    return jsonify(_serializar_persona(persona_actualizada)), 200


# DELETE /api/personnel/<int:person_id> — Eliminar o desactivar una persona
@api_personal_controller.delete("/personnel/<int:person_id>")
@token_required
@permission_required("personal_destroy")
@sector_assignment_required
def eliminar_persona(person_id: int):
    """Elimina o desactiva lógicamente a una persona según su historial."""
    sector_forzado = g.sector_forzado

    persona_actual = service_personal.get_by_id(person_id)

    if persona_actual is None:
        return jsonify({"error": "Persona no encontrada"}), 404

    sector_actual = service_personal.get_sector_asignado(person_id)
    es_res = service_personal.es_residente(persona_actual.idTipoPersonal)

    if sector_forzado is not None:
        pertenece_a_su_sector = (
            sector_actual is not None
            and sector_actual.idSector == sector_forzado
        )

        if es_res or not pertenece_a_su_sector:
            return jsonify({
                "error": "No tenés permisos para eliminar o desactivar esta persona"
            }), 403

    exito, accion = service_personal.eliminar_personal(person_id)

    if not exito:
        return jsonify({"error": "Persona no encontrada"}), 404

    return jsonify({
        "message": f"Persona {accion} correctamente",
        "accion": accion,
        "id": person_id,
    }), 200


# GET /api/menu-types — Listar tipos de menú
@api_personal_controller.get("/menu-types")
@token_required
@permission_required("personal_index")
@sector_assignment_required
def listar_tipos_menu():
    """Devuelve el catálogo completo de tipos de menú predefinidos."""
    tipos_menu = service_personal.get_tipos_menu()

    return jsonify([
        {
            "id": tm.idTipoMenu,
            "nombre": tm.nombre,
        }
        for tm in tipos_menu
    ]), 200


# GET /api/personnel-types — Listar tipos de personal
@api_personal_controller.get("/personnel-types")
@token_required
@permission_required("personal_index")
@sector_assignment_required
def listar_tipos_personal():
    """Devuelve el catálogo completo de tipos de personal predefinidos."""
    tipos_personal = service_personal.get_tipos_personal()

    return jsonify([
        {
            "id": tp.idTipoPersonal,
            "nombre": tp.nombre,
        }
        for tp in tipos_personal
    ]), 200
