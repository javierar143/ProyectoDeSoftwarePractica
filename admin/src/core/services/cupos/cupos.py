"""Servicio de lógica de negocio para la administración de cupos por sector."""

from src.core.models.Cupo import Cupo
from src.core.repositories.cupos import cupos as repo_cupos
from src.core.repositories.sectores import sector as repo_sector
from src.core.services.configuracion import obtener_configuracion


class CupoServiceError(Exception):
    """Excepción de validación para errores de negocio de cupos (HTTP 400)."""

    pass


class CupoNotFoundError(Exception):
    """Excepción para cuando el cupo solicitado no existe o fue dado de baja (HTTP 404)."""

    pass


def validar_reglas_negocio_cupo(
    id_sector: int,
    id_tipo_comida: int,
    id_cupo_actual: int | None = None,
) -> None:
    """
    Valida las reglas de dominio de un cupo:
    - Que el sector exista y esté activo en la BD.
    - Que no exista otro cupo vigente para el mismo sector y tipo de comida.
    """
    sector = repo_sector.get_by_id(id_sector)
    if not sector or not sector.isActive:
        raise CupoServiceError("El sector no existe o está inactivo.")

    existente = repo_cupos.get_by_sector_y_comida(id_sector, id_tipo_comida)
    if existente and existente.idCupo != id_cupo_actual:
        raise CupoServiceError(
            "Ya existe un cupo vigente para ese sector y tipo de comida."
        )


def create(id_sector: int, id_tipo_comida: int, cant_comensales: int) -> Cupo:
    """Valida las reglas de negocio y coordina la creación de un nuevo cupo vigente."""
    validar_reglas_negocio_cupo(id_sector, id_tipo_comida)

    nuevo_cupo = Cupo(
        idSector=id_sector,
        idTipoComida=id_tipo_comida,
        cantComensales=cant_comensales,
        activo=True,
    )

    return repo_cupos.create(nuevo_cupo)


def get_by_sector_y_comida(id_sector: int, id_tipo_comida: int) -> Cupo | None:
    """Obtiene el cupo vigente apoyándose en el repositorio."""
    return repo_cupos.get_by_sector_y_comida(id_sector, id_tipo_comida)


def listar(
    id_sector: int | None = None,
    id_tipo_comida: int | None = None,
    orden: str = "asc",
    page: int = 1,
) -> tuple[list[Cupo], int, int]:
    """Obtiene la paginación global del sistema y devuelve el listado de cupos."""
    if page < 1:
        page = 1

    config = obtener_configuracion()
    per_page = config.elementos_por_pagina

    items, total = repo_cupos.list_cupos(
        id_sector=id_sector,
        id_tipo_comida=id_tipo_comida,
        orden=orden,
        page=page,
        per_page=per_page,
    )
    return items, total, per_page


def obtener_por_id(id_cupo: int) -> Cupo:
    """Busca un cupo vigente por su ID o lanza CupoNotFoundError si no existe."""
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
    """Actualiza un cupo existente sin alterar retroactivamente pedidos ya registrados."""
    cupo = obtener_por_id(id_cupo)

    validar_reglas_negocio_cupo(id_sector=id_sector, id_tipo_comida=id_tipo_comida, id_cupo_actual=id_cupo)

    cupo.idSector = id_sector
    cupo.idTipoComida = id_tipo_comida
    cupo.cantComensales = cant_comensales

    return repo_cupos.update(cupo)


def eliminar(id_cupo: int) -> Cupo:
    """Realiza la baja lógica de un cupo existente."""
    cupo = obtener_por_id(id_cupo)
    return repo_cupos.soft_delete(cupo)