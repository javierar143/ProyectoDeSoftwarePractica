"""Repositorio para la persistencia y consulta de personal."""

from datetime import datetime
from sqlalchemy import select, delete

from src.core.database import db
from src.core.models.Personal import Personal
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.TipoMenu import TipoMenu
from src.core.models.SectorCompuestoPorPersonal import SectorCompuestoPorPersonal
from src.core.models.SectorTemporal import SectorTemporal


def get_all(solo_activos: bool = False) -> list[Personal]:
    """Obtiene todo el personal ordenado por apellido y nombre."""
    statement = select(Personal).order_by(Personal.apellido, Personal.nombre)
    if solo_activos:
        statement = statement.where(Personal.isActive.is_(True))
    return db.session.execute(statement).scalars().all()


def get_by_id(id_personal: int) -> Personal | None:
    """Obtiene un personal a partir de su identificador."""
    statement = select(Personal).where(Personal.idPersonal == id_personal)
    return db.session.execute(statement).scalar_one_or_none()


def get_by_dni(dni: str) -> Personal | None:
    """Obtiene un personal a partir de su DNI para validar duplicados."""
    statement = select(Personal).where(Personal.dni == dni)
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


def get_tipos_personal() -> list[TipoPersonal]:
    """Obtiene el catálogo de tipos de personal para los formularios."""
    statement = select(TipoPersonal).order_by(TipoPersonal.nombre)
    return db.session.execute(statement).scalars().all()


def get_tipos_menu() -> list[TipoMenu]:
    """Obtiene el catálogo de tipos de menú para los formularios."""
    statement = select(TipoMenu).order_by(TipoMenu.nombre)
    return db.session.execute(statement).scalars().all()

def get_sector_asignado(id_personal: int) -> SectorTemporal | None:
    """Obtiene el sector asignado al personal si existe en la tabla intermedia."""
    statement = (
        select(SectorTemporal)
        .join(SectorCompuestoPorPersonal, SectorCompuestoPorPersonal.idSector == SectorTemporal.idSector)
        .where(SectorCompuestoPorPersonal.idPersonal == id_personal)
    )
    return db.session.execute(statement).scalar_one_or_none()


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


def get_sectores() -> list[SectorTemporal]:
    """Obtiene el catálogo de sectores activos para los desplegables."""
    statement = select(SectorTemporal).where(SectorTemporal.isActive.is_(True)).order_by(SectorTemporal.nombre)
    return db.session.execute(statement).scalars().all()