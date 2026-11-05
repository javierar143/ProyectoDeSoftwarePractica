
"""Coordina las acciones disponibles en el alta de usuarios."""

from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)

from src.core.security.session import get_authenticated_user_id
from src.core.services.personal import personal as personal_service
from src.core.services.usuarios import alta_conjunta, personal, rol, usuario
from src.web.validators.usuarios.usuarios import (
    validate_alta_conjunta_data,
    validate_user_data,
)


def _obtener_datos(form) -> dict[str, str]:
    """Extrae los datos del formulario sin modificar las contraseñas."""
    campos_texto = (
        "dni",
        "nombre",
        "apellido",
        "idTipoPersonal",
        "idSector",
        "idTipoMenu",
        "email",
        "alias",
        "rol_nombre",
        "personal_id",
        "is_system_admin",
    )

    datos = {
        campo: form.get(campo, "").strip()
        for campo in campos_texto
    }

    datos["password"] = form.get("password", "")
    datos["confirmar_password"] = form.get("confirmar_password", "")

    return datos


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


def _puede_asignar_privilegios_administrador() -> bool:
    """Comprueba si el usuario autenticado es administrador del sistema."""
    user_id = get_authenticated_user_id()

    if user_id is None:
        return False

    usuario_actual = usuario.get_by_id(user_id)

    return (
        usuario_actual is not None
        and usuario_actual.isActive
        and usuario_actual.isSystemAdmin
    )


def _validar_asignacion_administrador(datos: dict[str, str]) -> None:
    """Impide conceder privilegios de administrador sin autorización."""
    solicita_admin_sistema = datos.get("is_system_admin") == "on"
    solicita_rol_administrador = (
        datos.get("rol_nombre", "").strip() == "Administrador"
    )

    if (
        solicita_admin_sistema or solicita_rol_administrador
    ) and not _puede_asignar_privilegios_administrador():
        abort(
            403,
            description=(
                "No tenés autorización para asignar privilegios "
                "de administrador."
            ),
        )


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
            status=422,
        )

    if datos["password"] != datos["confirmar_password"]:
        return mostrar_formulario(
            dni=dni,
            persona_encontrada=persona,
            mostrar_existente=True,
            error="Las contraseñas no coinciden.",
            form_data=datos,
            status=422,
        )

    if not validate_user_data(
        datos["email"],
        datos["alias"],
        datos["password"],
        datos["confirmar_password"],
        datos["rol_nombre"],
    ):
        mensaje = (
            "La contraseña debe tener al menos 8 caracteres."
            if len(datos["password"]) < 8
            else "Completá correctamente todos los campos obligatorios."
        )

        return mostrar_formulario(
            dni=dni,
            persona_encontrada=persona,
            mostrar_existente=True,
            error=mensaje,
            form_data=datos,
            status=422,
        )

    _validar_asignacion_administrador(datos)

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
            status=422,
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

    flash("El usuario se creó correctamente.", "success")

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
            status=422,
        )

    _validar_asignacion_administrador(datos)

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
                else None
            ),
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
            status=422,
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

    flash(
        "El Personal y el usuario se crearon correctamente.",
        "success",
    )

    return redirect(url_for("usuarios.listado_usuarios.index"))
