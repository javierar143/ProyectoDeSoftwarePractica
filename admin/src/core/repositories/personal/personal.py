"""Repositorio para la persistencia y consulta de personal."""

from datetime import datetime
from sqlalchemy import select, delete, or_, asc, desc, func
from sqlalchemy import select, delete, exists

from src.core.database import db
from src.core.models.Personal import Personal
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.TipoMenu import TipoMenu
from src.core.models.SectorCompuestoPorPersonal import SectorCompuestoPorPersonal
from src.core.models.Sector import Sector
from src.core.models.Solicitud import Solicitud
from src.core.models.Entrega import Entrega


def get_all(solo_activos: bool = False) -> list[Personal]:
    """Obtiene todo el personal ordenado por apellido y nombre."""
    statement = select(Personal).where(Personal.is_deleted.is_(False)).order_by(Personal.apellido, Personal.nombre)
    if solo_activos:
        statement = statement.where(Personal.isActive.is_(True))
    return db.session.execute(statement).scalars().all()


def get_by_id(id_personal: int) -> Personal | None:
    """Obtiene un personal a partir de su identificador."""
    statement = select(Personal).where(
        Personal.idPersonal == id_personal,
        Personal.is_deleted.is_(False)
    )
    return db.session.execute(statement).scalar_one_or_none()


def get_by_dni(dni: str) -> Personal | None:
    """Obtiene un personal a partir de su DNI para validar duplicados."""
    statement = select(Personal).where(
        Personal.dni == dni,
        Personal.is_deleted.is_(False)
    )
    return db.session.execute(statement).scalar_one_or_none()


def create(personal: Personal) -> Personal:
    """Persiste un nuevo personal en la base de datos."""
    db.session.add(personal)
    db.session.commit()
    return personal


def update(personal: Personal) -> Personal:
    """Persiste los cambios realizados sobre un personal existente."""
    personal.updated_at = datetime.now()
    db.session.commit()
    return personal


def deactivate(personal: Personal) -> Personal:
    """Realiza la baja lógica cambiando isActive a False."""
    personal.isActive = False
    personal.updated_at = datetime.now()
    db.session.commit()
    return personal

def eliminar(personal: Personal) -> None:
    """Simula un borrado físico ocultando permanentemente el registro."""
    personal.is_deleted = True
    personal.updated_at = datetime.now()
    db.session.commit()


def get_tipos_personal() -> list[TipoPersonal]:
    """Obtiene el catálogo de tipos de personal para los formularios."""
    statement = select(TipoPersonal).order_by(TipoPersonal.nombre)
    return db.session.execute(statement).scalars().all()


def get_tipos_menu() -> list[TipoMenu]:
    """Obtiene el catálogo de tipos de menú para los formularios."""
    statement = select(TipoMenu).order_by(TipoMenu.nombre)
    return db.session.execute(statement).scalars().all()

def get_sector_asignado(id_personal: int) -> Sector | None:
    """Obtiene el sector asignado al personal si existe en la tabla intermedia."""
    statement = (
        select(Sector)
        .join(SectorCompuestoPorPersonal, SectorCompuestoPorPersonal.idSector == Sector.idSector)
        .where(SectorCompuestoPorPersonal.idPersonal == id_personal)
    )
    return db.session.execute(statement).scalar_one_or_none()

def pertenece_a_sector(id_personal: int, id_sector: int) -> bool:
    """Indica si la persona está asociada al sector en la tabla intermedia."""
    statement = select(
        exists().where(
            SectorCompuestoPorPersonal.idPersonal == id_personal,
            SectorCompuestoPorPersonal.idSector == id_sector,
        )
    )
    return bool(db.session.execute(statement).scalar())

def set_sector(id_personal: int, id_sector: int | None) -> None:
    """Asigna o quita el sector de un personal en SectorCompuestoPorPersonal."""
    # elimina asignacion previa si existiera
    db.session.execute(
        delete(SectorCompuestoPorPersonal).where(SectorCompuestoPorPersonal.idPersonal == id_personal)
    )
    # si viene un id_sector (es PersonalFijo), inserta el vinculo
    if id_sector is not None:
        nueva_asociacion = SectorCompuestoPorPersonal(idSector=id_sector, idPersonal=id_personal)
        db.session.add(nueva_asociacion)
    db.session.commit()


def get_sectores() -> list[Sector]:
    """Obtiene el catálogo de sectores activos para los desplegables."""
    statement = select(Sector).where(Sector.isActive.is_(True)).order_by(Sector.nombre)
    return db.session.execute(statement).scalars().all()

from sqlalchemy import select, or_, desc, asc, func
from src.core.database import db
from src.core.models.Personal import Personal
from src.core.models.SectorCompuestoPorPersonal import SectorCompuestoPorPersonal

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
) -> tuple[list[Personal], int]:
    """Ejecuta la consulta SQL con filtros y paginado."""
    statement = (
        select(Personal)
        .outerjoin(SectorCompuestoPorPersonal, SectorCompuestoPorPersonal.idPersonal == Personal.idPersonal)
        .where(Personal.is_deleted.is_(False))
        .distinct()
    )

    if texto_busqueda:
        termino = f"%{texto_busqueda.strip()}%"
        statement = statement.where(
            or_(Personal.nombre.ilike(termino), Personal.apellido.ilike(termino))
        )

    if dni:
        statement = statement.where(Personal.dni.ilike(f"%{dni.strip()}%"))

    if id_tipo_personal:
        statement = statement.where(Personal.idTipoPersonal == id_tipo_personal)

    if sector_forzado_jefe is not None:
        statement = statement.where(
            or_(
                SectorCompuestoPorPersonal.idSector == sector_forzado_jefe,
                Personal.idTipoPersonal == 2
            )
        )
    elif id_sector:
        statement = statement.where(SectorCompuestoPorPersonal.idSector == id_sector)

    if estado == "activos":
        statement = statement.where(Personal.isActive.is_(True))
    elif estado == "inactivos":
        statement = statement.where(Personal.isActive.is_(False))

    count_statement = select(func.count()).select_from(statement.subquery())
    total = db.session.execute(count_statement).scalar_one()

    es_desc = direccion.lower() == "desc"
    if ordenar_por == "dni":
        criterios = [desc(Personal.dni) if es_desc else asc(Personal.dni)]
    elif ordenar_por == "fecha":
        criterios = [desc(Personal.inserted_at) if es_desc else asc(Personal.inserted_at)]
    else:
        criterios = [desc(Personal.apellido), desc(Personal.nombre)] if es_desc else [asc(Personal.apellido), asc(Personal.nombre)]

    statement = statement.order_by(*criterios)

    offset_val = (page - 1) * per_page
    statement = statement.limit(per_page).offset(offset_val)

    elementos = list(db.session.execute(statement).scalars().all())

    for persona in elementos:
        persona.sector_asignado = get_sector_asignado(persona.idPersonal)

    return elementos, total

def tiene_historial(id_personal: int) -> bool:
    """Verifica si una persona tiene solicitudes o entregas asociadas.
    Retorna True si tiene historial, False en caso contrario. """
    # buscamos si tiene al menos una solicitud
    solicitud = db.session.execute(
        select(Solicitud).where(Solicitud.idPersonal == id_personal)
    ).scalar_one_or_none()
    
    if solicitud is not None:
        return True
        
    # buscamos si tiene al menos una entrega
    entrega = db.session.execute(
        select(Entrega).where(Entrega.idPersonal == id_personal)
    ).scalar_one_or_none()
    
    if entrega is not None:
        return True
        
    return False