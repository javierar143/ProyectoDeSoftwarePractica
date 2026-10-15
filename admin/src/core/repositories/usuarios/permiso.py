"""Repositorio para la consulta de permisos asociados a roles."""

from sqlalchemy import select

from src.core.database import db
from src.core.models.Permiso import Permiso
from src.core.models.RolPoseePermiso import RolPoseePermiso


def has_permission(rol_id: int, permiso_nombre: str) -> bool:
    """Indica si un rol tiene asignado un permiso por su nombre."""
    statement = (
        select(Permiso.idPermiso)
        .join(
            RolPoseePermiso,
            Permiso.idPermiso == RolPoseePermiso.idPermiso,
        )
        .where(
            RolPoseePermiso.idRol == rol_id,
            Permiso.nombre == permiso_nombre,
        )
    )
    permiso_id = db.session.execute(statement).scalar_one_or_none()
    tiene_permiso = permiso_id is not None

    return tiene_permiso
