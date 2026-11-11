"""Servicios relacionados con la gestión de personal."""

from datetime import datetime
import math

from flask import current_app

from src.core.models.Personal import Personal
from src.core.models.Sector import Sector
from src.core.models.TipoMenu import TipoMenu
from src.core.models.TipoPersonal import TipoPersonal
from src.core.repositories.personal import personal as repo_personal
from src.core.services.usuarios import permiso as service_permiso
from src.core.services.usuarios import usuario as service_usuario


def get_all(solo_activos: bool = False) -> list[Personal]:
    """Obtiene todo el personal registrado."""
    return repo_personal.get_all(solo_activos=solo_activos)


def get_by_id(id_personal: int) -> Personal | None:
    """Obtiene una persona por su identificador."""
    return repo_personal.get_by_id(id_personal)


def get_by_dni(dni: str) -> Personal | None:
    """Obtiene una persona por su número de DNI."""
    return repo_personal.get_by_dni(dni)


def get_tipos_personal() -> list[TipoPersonal]:
    """Obtiene las opciones predefinidas de tipos de personal."""
    return repo_personal.get_tipos_personal()


def get_tipos_menu() -> list[TipoMenu]:
    """Obtiene las opciones predefinidas de tipos de menú."""
    return repo_personal.get_tipos_menu()


def get_sector_asignado(id_personal: int) -> Sector | None:
    """Obtiene el sector asignado al personal."""
    return repo_personal.get_sector_asignado(id_personal)


def get_sectores() -> list[Sector]:
    """Obtiene el listado de sectores disponibles."""
    return repo_personal.get_sectores()


def _obtener_sector_forzado(user_id: int | None) -> int | None:
    """Obtiene el sector forzado si el usuario no tiene permiso de gestionar todos los sectores."""
    if not user_id:
        return None

    usuario_actual = service_usuario.get_by_id(user_id)
    if not usuario_actual:
        return None

    puede_ver_todo = service_permiso.user_has_permission(
        user_id,
        "personal_manage_all_sectors",
    )
    if not puede_ver_todo and usuario_actual.idSector is not None:
        return usuario_actual.idSector

    return None


def obtener_sector_forzado(user_id: int | None) -> int | None:
    """Expone la regla de negocio del sector forzado para los controladores."""
    return _obtener_sector_forzado(user_id)


def es_residente(id_tipo_personal: int) -> bool:
    """Indica si el tipo de personal corresponde a Residente sin acoplarse a un ID fijo."""
    tipos = {
        t.idTipoPersonal: t.nombre.lower()
        for t in repo_personal.get_tipos_personal()
    }
    return "residente" in tipos.get(id_tipo_personal, "")


def puede_gestionar_residente(user_id: int | None) -> bool:
    """Verifica si el usuario tiene permiso para crear o modificar Residentes."""
    if user_id is None:
        return True
    return service_permiso.user_has_permission(
        user_id,
        "personal_create_residente",
    )

def create(
    dni: str,
    nombre: str,
    apellido: str,
    id_tipo_personal: int,
    id_tipo_menu: int,
    id_sector: int | None = None,
    user_id: int | None = None,
) -> Personal | None:
    """Crea una persona validando DNI único, permisos de Residente y asignación de sector."""
    sector_forzado = _obtener_sector_forzado(user_id)
    if sector_forzado is not None:
        id_sector = sector_forzado

    persona_existente = repo_personal.get_by_dni(dni)
    if persona_existente is not None:
        current_app.logger.warning(
            f"Intento de registro fallido: El DNI {dni} ya existe en el sistema."
        )
        return None

    tipos = {
        t.idTipoPersonal: t.nombre.lower()
        for t in repo_personal.get_tipos_personal()
    }
    nombre_tipo = tipos.get(id_tipo_personal, "")

    if "residente" in nombre_tipo:
        if not puede_gestionar_residente(user_id):
            raise PermissionError(
                "No tenés permisos para administrar personal de tipo Residente."
            )
        id_sector = None
    elif "fijo" in nombre_tipo and id_sector is None:
        raise ValueError(
            "El personal fijo requiere un sector asignado obligatoriamente."
        )

    ahora = datetime.now()
    nueva_persona = Personal(
        dni=dni,
        nombre=nombre,
        apellido=apellido,
        idTipoPersonal=id_tipo_personal,
        idTipoMenu=id_tipo_menu,
        isActive=True,
        inserted_at=ahora,
        updated_at=ahora,
    )
    persona_creada = repo_personal.create(nueva_persona)

    if id_sector is not None:
        repo_personal.set_sector(persona_creada.idPersonal, id_sector)

    current_app.logger.info(
        f"Personal registrado exitosamente: {nombre} {apellido} (DNI: {dni})."
    )
    return persona_creada


def update(
    id_personal: int,
    dni: str,
    nombre: str,
    apellido: str,
    id_tipo_personal: int,
    id_tipo_menu: int,
    id_sector: int | None = None,
    user_id: int | None = None,
) -> Personal | None:
    """Modifica los datos de una persona y actualiza su asignación de sector."""
    sector_forzado = _obtener_sector_forzado(user_id)
    if sector_forzado is not None:
        id_sector = sector_forzado

    persona_actual = repo_personal.get_by_id(id_personal)
    if persona_actual is None:
        return None

    persona_con_mismo_dni = repo_personal.get_by_dni(dni)
    if (
        persona_con_mismo_dni is not None
        and persona_con_mismo_dni.idPersonal != id_personal
    ):
        return None

    tipos = {
        t.idTipoPersonal: t.nombre.lower()
        for t in repo_personal.get_tipos_personal()
    }
    nombre_tipo = tipos.get(id_tipo_personal, "")

    if "residente" in nombre_tipo:
        if not puede_gestionar_residente(user_id):
            raise PermissionError(
                "No tenés permisos para administrar personal de tipo Residente."
            )
        id_sector = None
    elif "fijo" in nombre_tipo and id_sector is None:
        raise ValueError(
            "El personal fijo requiere un sector asignado obligatoriamente."
        )

    persona_actual.dni = dni
    persona_actual.nombre = nombre
    persona_actual.apellido = apellido
    persona_actual.idTipoPersonal = id_tipo_personal
    persona_actual.idTipoMenu = id_tipo_menu
    persona_actual.updated_at = datetime.now()

    personal_actualizada = repo_personal.update(persona_actual)
    repo_personal.set_sector(id_personal, id_sector)

    return personal_actualizada


def set_active(id_personal: int, is_active: bool) -> Personal | None:
    """Activa o desactiva lógicamente una persona sin borrar historial."""
    persona_actual = repo_personal.get_by_id(id_personal)
    if persona_actual is None:
        return None

    persona_actual.isActive = is_active
    persona_actual.updated_at = datetime.now()
    return repo_personal.update(persona_actual)


def search(
    texto_busqueda: str | None = None,
    dni: str | None = None,
    id_tipo_personal: int | None = None,
    id_sector: int | None = None,
    sector_forzado_jefe: int | None = None,
    estado: str | None = "activos",
    ordenar_por: str = "nombre_apellido",
    direccion: str = "asc",
    page: int = 1,
    per_page: int = 10,
    user_id: int | None = None,
) -> dict:
    """Orquesta la búsqueda delegando en el repositorio y limitando a 25 por página."""
    if user_id is not None:
        sector_forzado_jefe = _obtener_sector_forzado(user_id)

    page_segura = max(1, page)
    per_page_seguro = max(1, min(per_page, 25))

    elementos, total = repo_personal.search(
        texto_busqueda=texto_busqueda,
        dni=dni,
        id_tipo_personal=id_tipo_personal,
        id_sector=id_sector,
        sector_forzado_jefe=sector_forzado_jefe,
        estado=estado,
        ordenar_por=ordenar_por,
        direccion=direccion,
        page=page_segura,
        per_page=per_page_seguro,
    )

    total_pages = (
        math.ceil(total / per_page_seguro) if per_page_seguro > 0 else 1
    )

    return {
        "items": elementos,
        "total": total,
        "page": page_segura,
        "per_page": per_page_seguro,
        "pages": total_pages,
        "has_prev": page_segura > 1,
        "has_next": page_segura < total_pages,
        "prev_num": page_segura - 1 if page_segura > 1 else None,
        "next_num": page_segura + 1 if page_segura < total_pages else None,
    }


def eliminar_personal(id_personal: int) -> tuple[bool, str]:
    """
    Aplica la regla de negocio para la eliminación:
    Si tiene historial (solicitudes o entregas), se desactiva (baja lógica).
    Si no tiene historial, se oculta permanentemente (soft delete).
    """
    persona = repo_personal.get_by_id(id_personal)
    if not persona:
        current_app.logger.warning(
            f"Intento de eliminación fallido: Personal con ID {id_personal} no encontrado."
        )
        return False, "no_encontrado"

    if repo_personal.tiene_historial(id_personal):
        repo_personal.deactivate(persona)
        current_app.logger.info(
            f"Personal desactivado exitosamente: {persona.nombre} {persona.apellido} (DNI: {persona.dni})."
        )
        return True, "inactivado"

    repo_personal.eliminar(persona)
    current_app.logger.info(
        f"Personal eliminado exitosamente: {persona.nombre} {persona.apellido} (DNI: {persona.dni})."
    )
    return True, "eliminado"