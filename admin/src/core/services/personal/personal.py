"""Servicios relacionados con la gestión de personal."""

from datetime import datetime

from src.core.models.Personal import Personal
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.TipoMenu import TipoMenu
from src.core.repositories.personal import personal as repo_personal
from src.core.models.SectorTemporal import SectorTemporal


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

def get_sector_asignado(id_personal: int) -> SectorTemporal | None:
    """Obtiene el sector asignado al personal."""
    return repo_personal.get_sector_asignado(id_personal)


def get_sectores() -> list[SectorTemporal]:
    """Obtiene el listado de sectores disponibles."""
    return repo_personal.get_sectores()