"""Reglas de negocio del módulo de sectores."""

from src.core.models.Sector import Sector
from src.core.models.Usuario import Usuario
from src.core.repositories.sectores import sector as repo_sector
from src.core.repositories.usuarios import rol as repo_rol
from src.core.repositories.usuarios import usuario as repo_usuario

ROL_JEFE = "Jefe de Servicio"


class SectorError(Exception):
    """Error de regla de negocio del módulo de sectores."""


def search(**filtros) -> tuple[list[Sector], int]:
    """Busca sectores aplicando filtros, orden y paginado."""
    return repo_sector.search(**filtros)


def get_all(solo_activos: bool = False) -> list[Sector]:
    """Obtiene todos los sectores, opcionalmente solo los activos."""
    return repo_sector.get_all(solo_activos=solo_activos)


def get_by_id(id_sector: int) -> Sector | None:
    """Obtiene un sector por su identificador."""
    return repo_sector.get_by_id(id_sector)


def _get_id_rol_jefe() -> int:
    """Obtiene el id del rol Jefe de Servicio o falla si no fue cargado."""
    rol = repo_rol.get_by_name(ROL_JEFE)
    if rol is None:
        raise SectorError("No existe el rol Jefe de Servicio en la base de datos.")
    return rol.idRol


def get_jefes(id_sector: int) -> list[Usuario]:
    """Obtiene los Jefes de Servicio asignados a un sector."""
    return repo_sector.get_jefes(id_sector, _get_id_rol_jefe())


def get_jefes_disponibles() -> list[Usuario]:
    """Obtiene los Jefes de Servicio que todavía no tienen sector."""
    return repo_sector.get_jefes_sin_sector(_get_id_rol_jefe())


def get_todos_los_jefes() -> list[Usuario]:
    """Obtiene todos los Jefes de Servicio para el filtro de búsqueda."""
    return repo_sector.get_all_jefes(_get_id_rol_jefe())


def _validar_jefes(ids_jefes: list[int], id_sector: int | None, sector_activo: bool) -> list[Usuario]:
    """Verifica que cada usuario exista, sea Jefe de Servicio y no pertenezca a otro sector."""
    if ids_jefes and not sector_activo:
        raise SectorError("No se pueden asignar Jefes de Servicio a un sector inactivo.")

    id_rol_jefe = _get_id_rol_jefe()
    jefes = []
    for id_user in ids_jefes:
        usuario = repo_usuario.get_by_id(id_user)
        if usuario is None:
            raise SectorError(f"El usuario con id {id_user} no existe.")
        if usuario.idRol != id_rol_jefe:
            raise SectorError(f"{usuario.alias} no tiene rol Jefe de Servicio.")
        if usuario.idSector is not None and usuario.idSector != id_sector:
            raise SectorError(f"{usuario.alias} ya está asociado a otro sector.")
        jefes.append(usuario)
    return jefes


def _sincronizar_jefes(sector: Sector, jefes_nuevos: list[Usuario]) -> None:
    """Deja en el sector exactamente los jefes indicados (asigna y desasigna)."""
    ids_nuevos = {jefe.id_user for jefe in jefes_nuevos}

    # Sacá a los que estaban y ya no vienen en el form
    for jefe in get_jefes(sector.idSector):
        if jefe.id_user not in ids_nuevos:
            jefe.idSector = None
            repo_usuario.update(jefe)

    # Asigná a los seleccionados
    for jefe in jefes_nuevos:
        jefe.idSector = sector.idSector
        repo_usuario.update(jefe)

def create(nombre: str, descripcion: str, ids_jefes: list[int]) -> Sector:
    """Crea un sector validando la unicidad del nombre y los Jefes asignados."""
    if repo_sector.get_by_nombre(nombre) is not None:
        raise SectorError("Ya existe un sector con ese nombre.")

    jefes = _validar_jefes(ids_jefes, id_sector=None, sector_activo=True)

    sector = repo_sector.create(
        Sector(nombre=nombre, descripcion=descripcion or None, isActive=True)
    )
    _sincronizar_jefes(sector, jefes)
    return sector


def update(id_sector: int, nombre: str, descripcion: str, ids_jefes: list[int]) -> Sector:
    """Modifica un sector validando la unicidad del nombre y los Jefes asignados."""
    sector = repo_sector.get_by_id(id_sector)
    if sector is None:
        raise SectorError("El sector no existe.")

    mismo_nombre = repo_sector.get_by_nombre(nombre)
    if mismo_nombre is not None and mismo_nombre.idSector != id_sector:
        raise SectorError("Ya existe otro sector con ese nombre.")

    jefes = _validar_jefes(ids_jefes, id_sector=id_sector, sector_activo=sector.isActive)

    sector.nombre = nombre
    sector.descripcion = descripcion or None
    repo_sector.update(sector)
    _sincronizar_jefes(sector, jefes)
    return sector


def activar(id_sector: int) -> Sector:
    """Reactiva un sector inactivo."""
    sector = repo_sector.get_by_id(id_sector)
    if sector is None:
        raise SectorError("El sector no existe.")
    sector.isActive = True
    return repo_sector.update(sector)


def desactivar(id_sector: int) -> Sector:
    """Desactiva un sector siempre que no tenga usuarios activos."""
    sector = repo_sector.get_by_id(id_sector)
    if sector is None:
        raise SectorError("El sector no existe.")
    if repo_sector.has_active_users(id_sector):
        raise SectorError("No se puede desactivar un sector con usuarios activos.")
    sector.isActive = False
    return repo_sector.update(sector)


def eliminar(id_sector: int) -> str:
    """Elimina el sector, o lo desactiva si tiene registros asociados; devuelve la acción realizada."""
    sector = repo_sector.get_by_id(id_sector)
    if sector is None:
        raise SectorError("El sector no existe.")

    if repo_sector.has_associations(id_sector):
        desactivar(id_sector)
        return "desactivado"

    repo_sector.delete(sector)
    return "eliminado"


def seed(nombres: list[str]) -> int:
    """Crea los sectores indicados que todavía no existan y devuelve cuántos creó."""
    creados = 0
    for nombre in nombres:
        if repo_sector.get_by_nombre(nombre) is None:
            repo_sector.create(Sector(nombre=nombre, isActive=True))
            creados += 1
    return creados