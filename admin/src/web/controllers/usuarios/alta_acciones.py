"""Coordina las acciones disponibles en el alta de usuarios."""

from flask import abort, current_app, redirect, render_template, url_for

from src.core.services.personal import personal as personal_service
from src.core.services.usuarios import alta_conjunta, personal, usuario, rol
from src.web.validators.usuarios.usuarios import validate_user_data


def _obtener_datos(form) -> dict[str, str]:
    """Extrae y normaliza los datos enviados por un formulario."""
    campos = (
        "dni",
        "nombre",
        "apellido",
        "idTipoPersonal",
        "idTipoMenu",
        "email",
        "alias",
        "password",
        "rol_nombre",
        "personal_id",
        "is_system_admin",
    )
    datos = {campo: form.get(campo, "").strip() for campo in campos}
    return datos


def mostrar_formulario(
    dni: str = "",
    persona_encontrada=None,
    mostrar_existente: bool = False,
    error: str | None = None,
    form_data: dict[str, str] | None = None,
    status: int = 200,
):
    """Renderiza el formulario con sus catálogos y el estado de la operación."""
    respuesta = render_template(
        "usuarios/new.html",
        dni=dni,
        persona_encontrada=persona_encontrada,
        mostrar_existente=mostrar_existente,
        error=error,
        form_data=form_data or {},
        tipos_personal=personal_service.get_tipos_personal(),
        tipos_menu=personal_service.get_tipos_menu(),
        roles=rol.get_all(),
    )
    return respuesta, status


def buscar_personal(form):
    """Busca una persona por DNI para asociarle un usuario."""
    dni = form.get("dni", "").strip()
    persona = personal.get_by_dni(dni) if dni else None

    return mostrar_formulario(
        dni=dni,
        persona_encontrada=persona,
        mostrar_existente=True,
    )


def crear_usuario(form):
    """Crea un usuario asociado a Personal que ya existe."""
    datos = _obtener_datos(form)
    dni = datos["dni"]
    persona = personal.get_by_dni(dni) if dni else None

    if persona is None:
        return mostrar_formulario(
            dni=dni,
            mostrar_existente=True,
            error="No se encontró el Personal asociado al usuario.",
            form_data=datos,
            status=400,
        )

    datos_validos = validate_user_data(
        datos["email"],
        datos["alias"],
        datos["password"],
        datos["rol_nombre"],
    )

    if not datos_validos:
        return mostrar_formulario(
            dni=dni,
            persona_encontrada=persona,
            mostrar_existente=True,
            error="Completá correctamente todos los campos obligatorios.",
            form_data=datos,
            status=400,
        )

    try:
        usuario.create(
            email=datos["email"],
            alias=datos["alias"],
            password=datos["password"],
            is_system_admin=datos["is_system_admin"] == "on",
            rol_nombre=datos["rol_nombre"],
            personal_id=persona.idPersonal,
        )
    except ValueError as excepcion:
        return mostrar_formulario(
            dni=dni,
            persona_encontrada=persona,
            mostrar_existente=True,
            error=str(excepcion),
            form_data=datos,
            status=400,
        )
    except Exception:
        current_app.logger.exception("Error al crear un usuario")
        return mostrar_formulario(
            dni=dni,
            persona_encontrada=persona,
            mostrar_existente=True,
            error="No se pudo crear el usuario.",
            form_data=datos,
            status=500,
        )

    return redirect(url_for("usuarios.listado_usuarios.index"))


def crear_personal_usuario(form):
    """Valida y solicita el alta conjunta y transaccional de Personal y Usuario."""
    datos = _obtener_datos(form)
    errores = []

    if not datos["dni"].isdigit():
        errores.append("El DNI es obligatorio y debe contener solo números.")

    if not datos["nombre"]:
        errores.append("El nombre es obligatorio.")

    if not datos["apellido"]:
        errores.append("El apellido es obligatorio.")

    if not datos["idTipoPersonal"].isdigit():
        errores.append("Debe seleccionar un tipo de personal.")

    if not datos["idTipoMenu"].isdigit():
        errores.append("Debe seleccionar un tipo de menú.")

    usuario_valido = validate_user_data(
        datos["email"],
        datos["alias"],
        datos["password"],
        datos["rol_nombre"],
    )

    if not usuario_valido:
        errores.append(
            "Completá correctamente los datos obligatorios del usuario."
        )

    if errores:
        return mostrar_formulario(
            error=" ".join(errores),
            form_data=datos,
            status=400,
        )

    try:
        alta_conjunta.create(
            dni=datos["dni"],
            nombre=datos["nombre"],
            apellido=datos["apellido"],
            id_tipo_personal=int(datos["idTipoPersonal"]),
            id_tipo_menu=int(datos["idTipoMenu"]),
            email=datos["email"],
            alias=datos["alias"],
            password=datos["password"],
            is_system_admin=datos["is_system_admin"] == "on",
            rol_nombre=datos["rol_nombre"],
        )
    except ValueError as excepcion:
        return mostrar_formulario(
            error=str(excepcion),
            form_data=datos,
            status=400,
        )
    except Exception:
        current_app.logger.exception(
            "Error al crear Personal y Usuario conjuntamente"
        )
        return mostrar_formulario(
            error="No se pudo completar el alta. No se guardaron los cambios.",
            form_data=datos,
            status=500,
        )

    return redirect(url_for("usuarios.listado_usuarios.index"))


def procesar_alta(form):
    """Deriva el formulario a la acción solicitada y devuelve su respuesta HTTP."""
    acciones = {
        "buscar_personal": buscar_personal,
        "crear_usuario": crear_usuario,
        "crear_personal_usuario": crear_personal_usuario,
    }

    accion = acciones.get(form.get("accion", ""))

    if accion is None:
        abort(400, description="Acción no válida")

    return accion(form)
