"""Controlador API para la gestión y consulta de cupos por sector."""

from flask import Blueprint, abort, current_app, g, jsonify, request

from src.core.services.cupos import cupos
from src.web.decorators.api import token_required, permission_required, sector_assignment_required
from src.web.validators.cupos.cupos_validator import (
    validar_entrada_cupo,
    validar_filtros_listado_cupos,
)

bp_cupos = Blueprint("cupos", __name__, url_prefix="/api/quotas")

@bp_cupos.route("", methods=["GET"])
@token_required
@permission_required("quotas_index")
@sector_assignment_required
def listar_cupos():
    """Endpoint para listar cupos filtrados por sector y tipo de comida."""
    user = g.user
    sector_forzado = getattr(g, "sector_forzado", None)

    es_valido, resultado = validar_filtros_listado_cupos(request.args)
    if not es_valido:
        current_app.logger.warning(
            f"Filtros inválidos al listar cupos: {resultado}"
        )
        abort(400, description=str(resultado))

    filtros = resultado  # type: ignore[assignment]
    id_sector_param = filtros["id_sector"]

    if sector_forzado is not None:
        if id_sector_param is not None and id_sector_param != sector_forzado:
            current_app.logger.warning(
                f"Usuario ID {user.id_user} (sector {sector_forzado}) intentó consultar cupos del sector {id_sector_param}"
            )
            abort(
                403,
                description="Solo puede consultar cupos de su propio sector",
            )
        id_sector_filtro = sector_forzado
    else:
        id_sector_filtro = id_sector_param

    items, total, per_page = cupos.listar(
        id_sector=id_sector_filtro,
        id_tipo_comida=filtros["id_tipo_comida"],
        orden=filtros["orden"],
        page=filtros["page"],
    )

    return (
        jsonify(
            {
                "items": [
                    {
                        "idCupo": c.idCupo,
                        "idSector": c.idSector,
                        "idTipoComida": c.idTipoComida,
                        "cantComensales": c.cantComensales,
                        "activo": c.activo,
                    }
                    for c in items
                ],
                "total": total,
                "page": filtros["page"],
                "per_page": per_page,
            }
        ),
        200,
    )


@bp_cupos.route("/<int:quota_id>", methods=["GET"])
@token_required
@permission_required("quotas_index")
@sector_assignment_required
def obtener_cupo(quota_id: int):
    """Endpoint para consultar el detalle de un cupo por su ID."""
    user = g.user
    sector_forzado = getattr(g, "sector_forzado", None)

    cupo = cupos.obtener_por_id(quota_id)

    if sector_forzado is not None and cupo.idSector != sector_forzado:
        current_app.logger.warning(
            f"Usuario ID {user.id_user} (sector {sector_forzado}) intentó ver cupo ID {quota_id} del sector {cupo.idSector}"
        )
        abort(
            403,
            description="No tiene permisos para consultar un cupo de otro sector",
        )

    return (
        jsonify(
            {
                "idCupo": cupo.idCupo,
                "idSector": cupo.idSector,
                "idTipoComida": cupo.idTipoComida,
                "cantComensales": cupo.cantComensales,
                "activo": cupo.activo,
            }
        ),
        200,
    )


@bp_cupos.route("", methods=["POST"])
@token_required
@permission_required("quotas_new")
def crear_nuevo_cupo():
    """Endpoint para crear un cupo (Exclusivo rol Servicio de Alimentación)."""
    user = g.user

    es_valido, resultado = validar_entrada_cupo(request.get_json(silent=True))
    if not es_valido:
        current_app.logger.warning(
            f"Datos inválidos al intentar crear cupo: {resultado}"
        )
        abort(400, description=str(resultado))

    datos = resultado  # type: ignore[assignment]

    nuevo_cupo = cupos.create(
        id_sector=datos["id_sector"],
        id_tipo_comida=datos["id_tipo_comida"],
        cant_comensales=datos["cant_comensales"],
    )
    current_app.logger.info(
        f"Cupo creado exitosamente ID {nuevo_cupo.idCupo} para sector ID {nuevo_cupo.idSector} por usuario ID {user.id_user}"
    )
    return (
        jsonify(
            {
                "mensaje": "Cupo creado exitosamente",
                "idCupo": nuevo_cupo.idCupo,
                "idSector": nuevo_cupo.idSector,
                "idTipoComida": nuevo_cupo.idTipoComida,
                "cantComensales": nuevo_cupo.cantComensales,
                "activo": nuevo_cupo.activo,
            }
        ),
        201,
    )


@bp_cupos.route("/<int:quota_id>", methods=["PUT"])
@token_required
@permission_required("quotas_update")
def modificar_cupo(quota_id: int):
    """Endpoint para modificar un cupo existente (Exclusivo rol Servicio de Alimentación)."""
    user = g.user

    es_valido, resultado = validar_entrada_cupo(request.get_json(silent=True))
    if not es_valido:
        current_app.logger.warning(
            f"Datos inválidos al modificar cupo ID {quota_id}: {resultado}"
        )
        abort(400, description=str(resultado))

    datos = resultado  # type: ignore[assignment]

    cupo_actualizado = cupos.actualizar(
        id_cupo=quota_id,
        id_sector=datos["id_sector"],
        id_tipo_comida=datos["id_tipo_comida"],
        cant_comensales=datos["cant_comensales"],
    )
    current_app.logger.info(
        f"Cupo ID {quota_id} actualizado a {cupo_actualizado.cantComensales} comensales por usuario ID {user.id_user}"
    )
    return (
        jsonify(
            {
                "mensaje": "Cupo actualizado exitosamente",
                "idCupo": cupo_actualizado.idCupo,
                "idSector": cupo_actualizado.idSector,
                "idTipoComida": cupo_actualizado.idTipoComida,
                "cantComensales": cupo_actualizado.cantComensales,
                "activo": cupo_actualizado.activo,
            }
        ),
        200,
    )


@bp_cupos.route("/<int:quota_id>", methods=["DELETE"])
@token_required
@permission_required("quotas_destroy")
def eliminar_cupo(quota_id: int):
    """Endpoint para dar de baja lógica un cupo (Exclusivo rol Servicio de Alimentación)."""
    user = g.user

    cupo_inactivado = cupos.eliminar(quota_id)
    current_app.logger.info(
        f"Baja lógica de cupo ID {quota_id} realizada por usuario ID {user.id_user}"
    )
    return (
        jsonify(
            {
                "mensaje": "Cupo dado de baja correctamente",
                "idCupo": cupo_inactivado.idCupo,
                "activo": cupo_inactivado.activo,
            }
        ),
        200,
    )
