from src.core.models.Cupo import Cupo
from src.core.repositories.cupos import cupos as repo_cupos

class CupoServiceError(Exception):
    pass

def create(id_sector: int, id_tipo_comida: int, cant_comensales: int) -> Cupo:
    """
    Servicio para orquestar la creación de un nuevo cupo.
    """
    # TODO: Descomentar cuando Santi suba el modelo y repositorio de Sector
    # from src.core.repositories import sectores as repo_sectores
    # sector = repo_sectores.get_by_id(id_sector)
    # if not sector or not sector.isActive:
    #     raise CupoServiceError("El sector no existe o está inactivo.")

    nuevo_cupo = Cupo(
        idSector=id_sector,
        idTipoComida=id_tipo_comida,
        cantComensales=cant_comensales
    )

    return repo_cupos.create(nuevo_cupo)

def get_by_sector_y_comida(id_sector: int, id_tipo_comida: int) -> Cupo | None:
    """Obtiene el cupo apoyándose en el repositorio."""
    return repo_cupos.get_by_sector_y_comida(id_sector, id_tipo_comida)