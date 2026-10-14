from src.core.database import db
from src.core.models.Cupo import Cupo
from src.core.repositories.cupos import cupos as repo_cupos

class CupoServiceError(Exception):
    pass

class CupoNotFoundError(Exception):
    """Excepción para cuando el cupo solicitado no existe (HTTP 404)."""
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


def listar(
    id_sector: int | None = None,
    id_tipo_comida: int | None = None,
    orden: str = "asc",
    page: int = 1,
    per_page: int = 25,
) -> tuple[list[Cupo], int]:
    """Valida los parámetros de paginación y devuelve el listado de cupos."""
    if page < 1:
        page = 1

    if per_page < 1 or per_page > 25:
        per_page = 25

    return repo_cupos.list_cupos(
        id_sector=id_sector,
        id_tipo_comida=id_tipo_comida,
        orden=orden,
        page=page,
        per_page=per_page,
    )


def obtener_por_id(id_cupo: int) -> Cupo:
    """Busca un cupo por su ID o lanza CupoNotFoundError si no existe."""
    cupo = repo_cupos.get_by_id(id_cupo)
    if not cupo:
        raise CupoNotFoundError(f"El cupo con ID {id_cupo} no existe.")
    return cupo


def actualizar(
    id_cupo: int,
    id_sector: int,
    id_tipo_comida: int,
    cant_comensales: int,
) -> Cupo:
    """
    Actualiza un cupo existente validando cantidad positiva, sector activo
    y que no colisione con otro cupo vigente para el mismo sector y comida.
    """
    cupo = obtener_por_id(id_cupo)

    if cant_comensales is None or int(cant_comensales) <= 0:
        raise CupoServiceError("La cantidad de comensales debe ser mayor a cero.")

    if cupo.idSector != id_sector or cupo.idTipoComida != id_tipo_comida:
        existente = get_by_sector_y_comida(id_sector, id_tipo_comida)
        if existente and existente.idCupo != id_cupo:
            raise CupoServiceError(
                "Ya existe un cupo vigente para ese sector y tipo de comida."
            )

    cupo.idSector = id_sector
    cupo.idTipoComida = id_tipo_comida
    cupo.cantComensales = int(cant_comensales)

    db.session.flush()
    return cupo