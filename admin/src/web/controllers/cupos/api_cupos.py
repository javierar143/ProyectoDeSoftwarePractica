"""Controlador API para la gestión y consulta de cupos por sector."""

from flask import Blueprint, abort, current_app, jsonify, request

from src.core.services.auth import api_auth
from src.core.services.cupos import cupos
from src.core.services.personal.personal import get_sector_asignado
from src.core.services.usuarios.rol import get_by_id
from src.web.validators.cupos.cupos_validator import (
    validar_entrada_cupo,
    validar_filtros_listado_cupos,
)

bp_cupos = Blueprint("cupos", __name__, url_prefix="/api/quotas")


def _autenticar_y_obtener_rol():
    """Valida el Bearer token con el servicio de Javi y obtiene el rol del usuario."""
    authorization = request.headers.get("Authorization")
    if authorization is None or not authorization.startswith("Bearer "):
        current_app.logger.warning(
            "Intento de acceso a /api/quotas sin token de autenticación"
        )
        abort(401, description="Token de autenticación requerido")

    token = authorization[7:].strip()
    user = api_auth.get_authenticated_user(token)

    if user is None or not user.isActive:
        current_app.logger.warning(
            "Intento de acceso a /api/quotas con token inválido o usuario inactivo"
        )
        abort(401, description="Token inválido o expirado")

    rol = get_by_id(user.idRol)
    nombre_rol = rol.nombre.strip().lower() if rol and rol.nombre else ""

    return user, nombre_rol


def _obtener_sector_jefe(user) -> int | None:
    """Obtiene el idSector del Jefe de Servicio desde personal o desde su usuario."""
    id_personal = getattr(user, "idPersonal", None)
    if id_personal is not None:
        sector = get_sector_asignado(id_personal)
        if sector is not None:
            return getattr(sector, "idSector", sector)
    return getattr(user, "idSector", None)


@bp_cupos.route("", methods=["GET"])
def listar_cupos():
    """Endpoint para listar cupos filtrados por sector y tipo de comida."""
    user, nombre_rol = _autenticar_y_obtener_rol()

    es_jefe = "jefe" in nombre_rol
    es_alimentacion = "alimenta" in nombre_rol
    es_comedor = "comedor" in nombre_rol

    if not (es_jefe or es_alimentacion or es_comedor):
        current_app.logger.warning(
            f"Usuario ID {user.id_user} con rol '{nombre_rol}' intentó listar cupos sin permisos"
        )
        abort(403, description="No tiene permisos para consultar cupos")

    es_valido, resultado = validar_filtros_listado_cupos(request.args)
    if not es_valido:
        current_app.logger.warning(
            f"Filtros inválidos al listar cupos: {resultado}"
        )
        abort(400, description=str(resultado))

    filtros = resultado  # type: ignore[assignment]
    id_sector_param = filtros["id_sector"]

    if es_jefe:
        sector_jefe = _obtener_sector_jefe(user)
        if sector_jefe is None:
            current_app.logger.warning(
                f"Jefe de Servicio ID {user.id_user} sin sector asignado intentó consultar cupos"
            )
            abort(403, description="El usuario no tiene un sector asignado")
        if id_sector_param is not None and id_sector_param != sector_jefe:
            current_app.logger.warning(
                f"Jefe de Servicio ID {user.id_user} (sector {sector_jefe}) intentó consultar cupos del sector {id_sector_param}"
            )
            abort(
                403,
                description="Un Jefe de Servicio solo puede consultar cupos de su propio sector",
            )
        id_sector_filtro = sector_jefe
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
def obtener_cupo(quota_id: int):
    """Endpoint para consultar el detalle de un cupo por su ID."""
    user, nombre_rol = _autenticar_y_obtener_rol()

    es_jefe = "jefe" in nombre_rol
    es_alimentacion = "alimenta" in nombre_rol
    es_comedor = "comedor" in nombre_rol

    if not (es_jefe or es_alimentacion or es_comedor):
        current_app.logger.warning(
            f"Usuario ID {user.id_user} sin permisos intentó consultar cupo ID {quota_id}"
        )
        abort(403, description="No tiene permisos para consultar cupos")

    cupo = cupos.obtener_por_id(quota_id)

    if es_jefe:
        sector_jefe = _obtener_sector_jefe(user)
        if cupo.idSector != sector_jefe:
            current_app.logger.warning(
                f"Jefe ID {user.id_user} (sector {sector_jefe}) intentó ver cupo ID {quota_id} del sector {cupo.idSector}"
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
def crear_nuevo_cupo():
    """Endpoint para crear un cupo (Exclusivo rol Servicio de Alimentación)."""
    user, nombre_rol = _autenticar_y_obtener_rol()

    if "alimenta" not in nombre_rol:
        current_app.logger.warning(
            f"Usuario ID {user.id_user} con rol '{nombre_rol}' intentó crear un cupo sin permisos"
        )
        abort(
            403,
            description="Solo el Servicio de Alimentación puede crear cupos",
        )

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
def modificar_cupo(quota_id: int):
    """Endpoint para modificar un cupo existente (Exclusivo rol Servicio de Alimentación)."""
    user, nombre_rol = _autenticar_y_obtener_rol()

    if "alimenta" not in nombre_rol:
        current_app.logger.warning(
            f"Usuario ID {user.id_user} con rol '{nombre_rol}' intentó modificar cupo ID {quota_id}"
        )
        abort(
            403,
            description="Solo el Servicio de Alimentación puede modificar cupos",
        )

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
def eliminar_cupo(quota_id: int):
    """Endpoint para dar de baja lógica un cupo (Exclusivo rol Servicio de Alimentación)."""
    user, nombre_rol = _autenticar_y_obtener_rol()

    if "alimenta" not in nombre_rol:
        current_app.logger.warning(
            f"Usuario ID {user.id_user} con rol '{nombre_rol}' intentó eliminar cupo ID {quota_id}"
        )
        abort(
            403,
            description="Solo el Servicio de Alimentación puede eliminar cupos",
        )

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