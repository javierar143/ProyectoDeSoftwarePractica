"""Servicios relacionados con la gestión de personal."""

from datetime import datetime

from src.core.models.Personal import Personal
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.TipoMenu import TipoMenu
from src.core.repositories.personal import personal as repo_personal
from src.core.models.Sector import Sector
import math
from flask import current_app

def get_all(solo_activos: bool = False) -> list[Personal]:
    """Obtiene todo el personal registrado."""
    return repo_personal.get_all(solo_activos=solo_activos)


def get_by_id(id_personal: int) -> Personal | None:
    """Obtiene una persona por su identificador."""
    return repo_personal.get_by_id(id_personal)


def get_by_dni(dni: str) -> Personal | None:
    """Obtiene una persona por su número de DNI."""
    return repo_personal.get_by_dni(dni)


def create(
    dni: str,
    nombre: str,
    apellido: str,
    id_tipo_personal: int,
    id_tipo_menu: int,
    id_sector: int | None = None,
) -> Personal | None:
    """Crea una persona validando previamente la unicidad del DNI y gestionando la asignacion de sector si corresponde."""
    persona_existente = repo_personal.get_by_dni(dni)
    if persona_existente is not None:
        current_app.logger.warning(f"Intento de registro fallido: El DNI {dni} ya existe en el sistema.")
        return None

    # si es Residente no debe tener sector asignado
    tipos = {t.idTipoPersonal: t.nombre.lower() for t in repo_personal.get_tipos_personal()}
    nombre_tipo = tipos.get(id_tipo_personal, "")

    if "fijo" in nombre_tipo and id_sector is None:
        raise ValueError("El personal fijo requiere un sector asignado obligatoriamente.")

    if "residente" in nombre_tipo:
        id_sector = None
    
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

    # si se proporciono un sector, se asigna al personal creado
    if id_sector is not None:
        repo_personal.set_sector(persona_creada.idPersonal, id_sector)

    current_app.logger.info(f"Personal registrado exitosamente: {nombre} {apellido} (DNI: {dni}).")
    return persona_creada


def update(
    id_personal: int,
    dni: str,
    nombre: str,
    apellido: str,
    id_tipo_personal: int,
    id_tipo_menu: int,
    id_sector: int | None = None,
) -> Personal | None:
    """Modifica los datos de una persona y actualiza su asignacion de sector."""
    persona_actual = repo_personal.get_by_id(id_personal)
    if persona_actual is None:
        return None

    persona_con_mismo_dni = repo_personal.get_by_dni(dni)
    if persona_con_mismo_dni is not None and persona_con_mismo_dni.idPersonal != id_personal:
        return None

    tipos = {t.idTipoPersonal: t.nombre.lower() for t in repo_personal.get_tipos_personal()}
    nombre_tipo = tipos.get(id_tipo_personal, "")

    if "fijo" in nombre_tipo and id_sector is None:
        raise ValueError("El personal fijo requiere un sector asignado obligatoriamente.")

    if "residente" in nombre_tipo:
        id_sector = None

    persona_actual.dni = dni
    persona_actual.nombre = nombre
    persona_actual.apellido = apellido
    persona_actual.idTipoPersonal = id_tipo_personal
    persona_actual.idTipoMenu = id_tipo_menu
    persona_actual.updated_at = datetime.now()

    personal_actualizada = repo_personal.update(persona_actual)

    # actualiza la asociacion (si id_sector es None, se elimina la asociacion previa)
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

def search(
    texto_busqueda: str | None = None,
    dni: str | None = None,
    id_tipo_personal: int | None = None,
    id_sector: int | None = None,
    estado: str | None = "activos",
    ordenar_por: str = "nombre_apellido",
    direccion: str = "asc",
    page: int = 1,
    per_page: int = 10,
) -> dict:
    """Coordina la búsqueda paginada y ordenada de personal."""
    elementos, total = repo_personal.search(
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

    # adjuntamos el sector asignado a cada persona recuperada
    for persona in elementos:
        persona.sector_asignado = repo_personal.get_sector_asignado(persona.idPersonal)

    total_paginas = math.ceil(total / per_page) if per_page > 0 else 1

    return {
        "items": elementos,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": total_paginas,
        "has_prev": page > 1,
        "has_next": page < total_paginas,
        "prev_num": page - 1 if page > 1 else None,
        "next_num": page + 1 if page < total_paginas else None,
    }

def eliminar_personal(id_personal: int) -> tuple[bool, str]:
    """
    Aplica la regla de negocio para la eliminación:
    Si tiene historial (solicitudes o entregas), se desactiva (baja lógica).
    Si no tiene historial, se elimina "físicamente" (soft delete oculto).
    Retorna (éxito, accion_realizada).
    """
    persona = repo_personal.get_by_id(id_personal)
    if not persona:
        current_app.logger.warning(f"Intento de eliminación fallido: Personal con ID {id_personal} no encontrado.")
        return False, "no_encontrado"

    if repo_personal.tiene_historial(id_personal):
        repo_personal.deactivate(persona)
        current_app.logger.info(f"Personal desactivado exitosamente: {persona.nombre} {persona.apellido} (DNI: {persona.dni}).")
        return True, "inactivado"
    else:
        repo_personal.eliminar(persona)
        current_app.logger.info(f"Personal eliminado exitosamente: {persona.nombre} {persona.apellido} (DNI: {persona.dni}).")
        return True, "eliminado"