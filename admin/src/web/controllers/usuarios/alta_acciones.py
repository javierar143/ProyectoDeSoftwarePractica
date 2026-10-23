"""Coordina las acciones disponibles en el alta de usuarios."""

from flask import current_app, redirect, render_template, url_for

from src.core.services.personal import personal as personal_service
from src.core.services.usuarios import alta_conjunta, personal, rol, usuario
from src.web.validators.usuarios.usuarios import (
    validate_alta_conjunta_data,
    validate_user_data,
)


def _obtener_datos(form) -> dict[str, str]:
    """Extrae y normaliza los datos enviados por un formulario."""
    campos = (
        "dni",
        "nombre",
        "apellido",
        "idTipoPersonal",
        "idSector",
        "idTipoMenu",
        "email",
        "alias",
        "password",
        "rol_nombre",
        "personal_id",
        "is_system_admin",
    )
    return {campo: form.get(campo, "").strip() for campo in campos}


def _obtener_catalogos() -> dict:
    """Obtiene los catálogos necesarios para los selectores del formulario."""
    return {
        "tipos_personal": personal_service.get_tipos_personal(),
        "tipos_menu": personal_service.get_tipos_menu(),
        "sectores": personal_service.get_sectores(),
        "roles": rol.get_all(),
    }


def _buscar_persona(dni: str):
    """Obtiene una persona por DNI si el valor es válido."""
    return personal.get_by_dni(dni.strip()) if dni else None


def mostrar_formulario(
    dni: str = "",
    persona_encontrada=None,
    mostrar_existente: bool = False,
    mostrar_nuevo: bool = False,
    error: str | None = None,
    form_data: dict[str, str] | None = None,
    status: int = 200,
):
    """Renderiza el formulario con sus catálogos y el estado de la operación."""
    contexto = {
        **_obtener_catalogos(),
        "dni": dni,
        "persona_encontrada": persona_encontrada,
        "mostrar_existente": mostrar_existente,
        "mostrar_nuevo": mostrar_nuevo,
        "error": error,
        "form_data": form_data or {},
    }
    return render_template("usuarios/new.html", **contexto), status


def buscar_personal(form):
    """Busca una persona por DNI para asociarle un usuario."""
    dni = form.get("dni", "").strip()
    persona = _buscar_persona(dni)

    return mostrar_formulario(
        dni=dni,
        persona_encontrada=persona,
        mostrar_existente=True,
    )


def crear_usuario(form):
    """Crea un usuario asociado a Personal que ya existe."""
    datos = _obtener_datos(form)
    dni = datos["dni"]
    persona = _buscar_persona(dni)

    if persona is None:
        return mostrar_formulario(
            dni=dni,
            mostrar_existente=True,
            error="No se encontró el Personal asociado al usuario.",
            form_data=datos,
            status=400,
        )

    if not validate_user_data(
        datos["email"],
        datos["alias"],
        datos["password"],
        datos["rol_nombre"],
    ):
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
    errores = validate_alta_conjunta_data(datos)

    if errores:
        return mostrar_formulario(
            mostrar_nuevo=True,
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
            id_sector=(
                int(datos["idSector"])
                if datos["idSector"].isdigit()
                else None),
            email=datos["email"],
            alias=datos["alias"],
            password=datos["password"],
            is_system_admin=datos["is_system_admin"] == "on",
            rol_nombre=datos["rol_nombre"],
        )
    except ValueError as excepcion:
        return mostrar_formulario(
            mostrar_nuevo=True,
            error=str(excepcion),
            form_data=datos,
            status=400,
        )
    except Exception:
        current_app.logger.exception(
            "Error al crear Personal y Usuario conjuntamente"
        )
        return mostrar_formulario(
            mostrar_nuevo=True,
            error="No se pudo completar el alta. No se guardaron los cambios.",
            form_data=datos,
            status=500,
        )

    return redirect(url_for("usuarios.listado_usuarios.index"))