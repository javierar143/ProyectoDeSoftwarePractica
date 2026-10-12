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
