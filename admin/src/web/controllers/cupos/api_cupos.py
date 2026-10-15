"""Controlador API para la gestión y consulta de cupos por sector."""

from flask import Blueprint, jsonify, request

from src.core.database import db
from src.core.models.Rol import Rol
from src.core.services.auth import api_auth
from src.core.services.cupos import cupos
from src.core.services.cupos.cupos import CupoNotFoundError, CupoServiceError
from src.core.services.pedidos.pedidos import obtener_sector_de_personal

bp_cupos = Blueprint("cupos", __name__, url_prefix="/api/quotas")


def _autenticar_y_obtener_rol():
    """
    Valida el Bearer token con el servicio de Javi y obtiene el nombre del Rol.
    Devuelve (user, nombre_rol, None) o (None, None, respuesta_error_401).
    """
    authorization = request.headers.get("Authorization")
    if authorization is None or not authorization.startswith("Bearer "):
        return None, None, (jsonify({"error": "Token de autenticación requerido"}), 401)

    token = authorization[7:]
    user = api_auth.get_authenticated_user(token)

    if user is None or not user.isActive:
        return None, None, (jsonify({"error": "Token inválido o expirado"}), 401)

    rol = db.session.get(Rol, user.idRol)
    nombre_rol = rol.nombre.strip().lower() if rol and rol.nombre else ""

    return user, nombre_rol, None


@bp_cupos.route("", methods=["GET"])
def listar_cupos():
    """Endpoint para listar cupos filtrados por sector y tipo de comida."""
    user, nombre_rol, error_auth = _autenticar_y_obtener_rol()
    if error_auth:
        return error_auth

    es_jefe = "jefe" in nombre_rol
    es_alimentacion = "alimenta" in nombre_rol
    es_comedor = "comedor" in nombre_rol

    if not (es_jefe or es_alimentacion or es_comedor):
        return jsonify({"error": "No tiene permisos para consultar cupos"}), 403

    id_sector_param = request.args.get("sector", type=int)
    id_tipo_comida = request.args.get("tipo_comida", type=int)
    orden = request.args.get("orden", default="asc", type=str)
    page = request.args.get("page", default=1, type=int)

    if es_jefe:
        sector_jefe = obtener_sector_de_personal(user.idPersonal)
        if id_sector_param is not None and id_sector_param != sector_jefe:
            return jsonify(
                {"error": "Un Jefe de Servicio solo puede consultar cupos de su propio sector"}
            ), 403
        id_sector_filtro = sector_jefe
    else:
        id_sector_filtro = id_sector_param

    items, total, per_page = cupos.listar(
        id_sector=id_sector_filtro,
        id_tipo_comida=id_tipo_comida,
        orden=orden,
        page=page,
    )

    return jsonify({
        "items": [
            {
                "idCupo": c.idCupo,
                "idSector": c.idSector,
                "idTipoComida": c.idTipoComida,
                "cantComensales": c.cantComensales,
            }
            for c in items
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }), 200


@bp_cupos.route("/<int:quota_id>", methods=["GET"])
def obtener_cupo(quota_id: int):
    """Endpoint para consultar el detalle de un cupo por su ID."""
    user, nombre_rol, error_auth = _autenticar_y_obtener_rol()
    if error_auth:
        return error_auth

    es_jefe = "jefe" in nombre_rol
    es_alimentacion = "alimenta" in nombre_rol
    es_comedor = "comedor" in nombre_rol

    if not (es_jefe or es_alimentacion or es_comedor):
        return jsonify({"error": "No tiene permisos para consultar cupos"}), 403

    try:
        cupo = cupos.obtener_por_id(quota_id)

        if es_jefe:
            sector_jefe = obtener_sector_de_personal(user.idPersonal)
            if cupo.idSector != sector_jefe:
                return jsonify(
                    {"error": "No tiene permisos para consultar un cupo de otro sector"}
                ), 403

        return jsonify({
            "idCupo": cupo.idCupo,
            "idSector": cupo.idSector,
            "idTipoComida": cupo.idTipoComida,
            "cantComensales": cupo.cantComensales,
        }), 200
    except CupoNotFoundError as e:
        return jsonify({"error": str(e)}), 404


@bp_cupos.route("", methods=["POST"])
def crear_nuevo_cupo():
    """Endpoint para crear un cupo (Exclusivo rol Servicio de Alimentación)."""
    _, nombre_rol, error_auth = _autenticar_y_obtener_rol()
    if error_auth:
        return error_auth

    if "alimenta" not in nombre_rol:
        return jsonify(
            {"error": "Solo el Servicio de Alimentación puede crear cupos"}
        ), 403

    data = request.get_json(silent=True)

    if not data or not all(
        k in data for k in ("idSector", "idTipoComida", "cantComensales")
    ):
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    try:
        nuevo_cupo = cupos.create(
            id_sector=data["idSector"],
            id_tipo_comida=data["idTipoComida"],
            cant_comensales=data["cantComensales"],
        )
        db.session.commit()
        return jsonify({
            "mensaje": "Cupo creado exitosamente",
            "idCupo": nuevo_cupo.idCupo,
            "idSector": nuevo_cupo.idSector,
            "idTipoComida": nuevo_cupo.idTipoComida,
            "cantComensales": nuevo_cupo.cantComensales,
        }), 201

    except CupoServiceError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error interno al crear el cupo."}), 500


@bp_cupos.route("/<int:quota_id>", methods=["PUT"])
def modificar_cupo(quota_id: int):
    """Endpoint para modificar un cupo existente (Exclusivo rol Servicio de Alimentación)."""
    _, nombre_rol, error_auth = _autenticar_y_obtener_rol()
    if error_auth:
        return error_auth

    if "alimenta" not in nombre_rol:
        return jsonify(
            {"error": "Solo el Servicio de Alimentación puede modificar cupos"}
        ), 403

    data = request.get_json(silent=True)

    if not data or not all(
        k in data for k in ("idSector", "idTipoComida", "cantComensales")
    ):
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    try:
        cupo_actualizado = cupos.actualizar(
            id_cupo=quota_id,
            id_sector=data["idSector"],
            id_tipo_comida=data["idTipoComida"],
            cant_comensales=data["cantComensales"],
        )
        db.session.commit()
        return jsonify({
            "mensaje": "Cupo actualizado exitosamente",
            "idCupo": cupo_actualizado.idCupo,
            "idSector": cupo_actualizado.idSector,
            "idTipoComida": cupo_actualizado.idTipoComida,
            "cantComensales": cupo_actualizado.cantComensales,
        }), 200

    except CupoNotFoundError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 404

    except CupoServiceError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error interno al modificar el cupo."}), 500