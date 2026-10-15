"""Repositorio para la persistencia y consulta de sectores."""

from sqlalchemy import exists, func, select

from src.core.database import db
from src.core.models.Cupo import Cupo
from src.core.models.Pedido import Pedido
from src.core.models.SectorCompuestoPorPersonal import SectorCompuestoPorPersonal
from src.core.models.Sector import Sector
from src.core.models.Usuario import Usuario

ORDER_COLUMNS = {
    "nombre": Sector.nombre,
    "fecha": Sector.inserted_at,
}


def search(
    nombre: str | None,
    activo: bool | None,
    id_jefe: int | None,
    order_by: str,
    direction: str,
    page: int,
    per_page: int,
) -> tuple[list[Sector], int]:
    """Busca sectores con filtros combinables, orden y paginado; devuelve la página y el total."""
    statement = select(Sector)

    if nombre:
        statement = statement.where(Sector.nombre.ilike(f"%{nombre}%")) # Evito inyecciones SQL usando ilike() con parámetros
    if activo is not None:
        statement = statement.where(Sector.isActive.is_(activo))
    if id_jefe is not None:
        statement = statement.where(
            Sector.idSector.in_(select(Usuario.idSector).where(Usuario.id_user == id_jefe))
        )

    total = db.session.execute(
        select(func.count()).select_from(statement.subquery())
    ).scalar_one()

    column = ORDER_COLUMNS[order_by]
    statement = statement.order_by(
        column.desc() if direction == "desc" else column.asc(),
        Sector.idSector,
    )
    statement = statement.limit(per_page).offset((page - 1) * per_page)

    sectores = db.session.execute(statement).scalars().all()
    return sectores, total


def get_all(solo_activos: bool = False) -> list[Sector]:
    """Obtiene todos los sectores ordenados por nombre."""
    statement = select(Sector).order_by(Sector.nombre)
    if solo_activos:
        statement = statement.where(Sector.isActive.is_(True))
    return db.session.execute(statement).scalars().all()


def get_by_id(id_sector: int) -> Sector | None:
    """Obtiene un sector a partir de su identificador."""
    statement = select(Sector).where(Sector.idSector == id_sector)
    return db.session.execute(statement).scalar_one_or_none()


def get_by_nombre(nombre: str) -> Sector | None:
    """Obtiene un sector por nombre sin distinguir mayúsculas de minúsculas."""
    statement = select(Sector).where(func.lower(Sector.nombre) == nombre.lower())
    return db.session.execute(statement).scalar_one_or_none()


def create(sector: Sector) -> Sector:
    """Persiste un nuevo sector."""
    db.session.add(sector)
    db.session.commit()
    return sector


def update(sector: Sector) -> Sector:
    """Persiste los cambios realizados sobre un sector existente."""
    db.session.commit()
    return sector


def delete(sector: Sector) -> None:
    """Elimina físicamente un sector."""
    db.session.delete(sector)
    db.session.commit()


def has_associations(id_sector: int) -> bool:
    """Indica si el sector tiene usuarios, personal, pedidos o cupos asociados."""
    for model in (Usuario, SectorCompuestoPorPersonal, Pedido, Cupo):
        statement = select(exists().where(model.idSector == id_sector))
        if db.session.execute(statement).scalar():
            return True
    return False


def has_active_users(id_sector: int) -> bool:
    """Indica si el sector tiene usuarios activos asociados."""
    statement = select(
        exists().where(Usuario.idSector == id_sector, Usuario.isActive.is_(True))
    )
    return db.session.execute(statement).scalar()


def get_jefes(id_sector: int, id_rol_jefe: int) -> list[Usuario]:
    """Obtiene los Jefes de Servicio asociados a un sector."""
    statement = (
        select(Usuario)
        .where(Usuario.idSector == id_sector, Usuario.idRol == id_rol_jefe)
        .order_by(Usuario.alias)
    )
    return db.session.execute(statement).scalars().all()


def get_jefes_sin_sector(id_rol_jefe: int) -> list[Usuario]:
    """Obtiene los Jefes de Servicio activos que todavía no tienen sector."""
    statement = (
        select(Usuario)
        .where(
            Usuario.idRol == id_rol_jefe,
            Usuario.idSector.is_(None),
            Usuario.isActive.is_(True),
        )
        .order_by(Usuario.alias)
    )
    return db.session.execute(statement).scalars().all()


def get_all_jefes(id_rol_jefe: int) -> list[Usuario]:
    """Obtiene todos los Jefes de Servicio, para el filtro del listado."""
    statement = select(Usuario).where(Usuario.idRol == id_rol_jefe).order_by(Usuario.alias)
    return db.session.execute(statement).scalars().all()