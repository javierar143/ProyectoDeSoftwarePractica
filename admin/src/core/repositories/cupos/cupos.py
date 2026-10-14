from sqlalchemy import select, func

from src.core.models.Cupo import Cupo
from src.core.database import db

def create(nuevo_cupo: Cupo) -> Cupo:
    """Guarda un nuevo cupo en la base de datos."""
    db.session.add(nuevo_cupo)
    return nuevo_cupo

def get_by_sector_y_comida(id_sector: int, id_tipo_comida: int) -> Cupo | None:
    """Busca un cupo filtrando por sector y comida."""
    stmt = db.select(Cupo).filter_by(
        idSector=id_sector,
        idTipoComida=id_tipo_comida
    )
    return db.session.scalar(stmt)

def get_by_id(id_cupo: int) -> Cupo | None:
    """Recupera un cupo por su id."""
    return db.session.get(Cupo, id_cupo)

def list_cupos(
    id_sector: int | None = None,
    id_tipo_comida: int | None = None,
    orden: str = "asc",
    page: int = 1,
    per_page: int = 25,
) -> tuple[list[Cupo], int]:
    """
    Lista cupos filtrando y paginando en el motor de la base de datos.
    Devuelve la tupla (items, total).
    """
    stmt = select(Cupo)

    if id_sector is not None:
        stmt = stmt.where(Cupo.idSector == id_sector)

    if id_tipo_comida is not None:
        stmt = stmt.where(Cupo.idTipoComida == id_tipo_comida)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.session.scalar(count_stmt) or 0

    if orden.lower() == "desc":
        stmt = stmt.order_by(Cupo.idSector.desc(), Cupo.idCupo.desc())
    else:
        stmt = stmt.order_by(Cupo.idSector.asc(), Cupo.idCupo.asc())

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    items = list(db.session.scalars(stmt).all())
    return items, total