"""Repositorio para las consultas y operaciones en base de datos de Cupos."""

from datetime import datetime

from sqlalchemy import func, select

from src.core.database import db
from src.core.models.Cupo import Cupo
from src.core.models.Sector import Sector


def create(nuevo_cupo: Cupo) -> Cupo:
    """Guarda un nuevo cupo en la sesión de la base de datos."""
    db.session.add(nuevo_cupo)
    db.session.commit()
    return nuevo_cupo


def update(cupo: Cupo) -> Cupo:
    """Persiste los cambios de un cupo existente en la sesión."""
    cupo.updated_at = datetime.now()
    db.session.add(cupo)
    db.session.commit()
    return cupo


def soft_delete(cupo: Cupo) -> Cupo:
    """Realiza la baja lógica del cupo marcándolo como inactivo y registrando deleted_at."""
    cupo.activo = False
    cupo.deleted_at = datetime.now()
    cupo.updated_at = datetime.now()
    db.session.add(cupo)
    db.session.commit()
    return cupo


def get_by_sector_y_comida(id_sector: int, id_tipo_comida: int) -> Cupo | None:
    """Busca un cupo vigente (activo=True) filtrando por sector y tipo de comida."""
    stmt = select(Cupo).where(
        Cupo.idSector == id_sector,
        Cupo.idTipoComida == id_tipo_comida,
        Cupo.activo.is_(True),
    )
    return db.session.scalar(stmt)


def get_by_id(id_cupo: int) -> Cupo | None:
    """Recupera un cupo vigente por su clave primaria."""
    cupo = db.session.get(Cupo, id_cupo)
    if cupo is not None and cupo.activo:
        return cupo
    return None


def list_cupos(
    page: int,
    per_page: int,
    id_sector: int | None = None,
    id_tipo_comida: int | None = None,
    orden: str = "asc",
) -> tuple[list[Cupo], int]:
    """
    Lista los cupos vigentes filtrando por sector y comida, ordenando por Sector
    y paginando en el motor de la base de datos con el per_page recibido del servicio.
    Devuelve la tupla (items, total).
    """
    stmt = (
        select(Cupo)
        .outerjoin(Sector, Cupo.idSector == Sector.idSector)
        .where(Cupo.activo.is_(True))
    )

    if id_sector is not None:
        stmt = stmt.where(Cupo.idSector == id_sector)

    if id_tipo_comida is not None:
        stmt = stmt.where(Cupo.idTipoComida == id_tipo_comida)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.session.scalar(count_stmt) or 0

    if orden.lower() == "desc":
        stmt = stmt.order_by(
            Sector.nombre.desc(), Cupo.idSector.desc(), Cupo.idCupo.desc()
        )
    else:
        stmt = stmt.order_by(
            Sector.nombre.asc(), Cupo.idSector.asc(), Cupo.idCupo.asc()
        )

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    items = list(db.session.scalars(stmt).all())
    return items, total