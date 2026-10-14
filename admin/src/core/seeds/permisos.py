"""Carga los permisos iniciales de la aplicación."""

from src.core.database import db
from src.core.models.Permiso import Permiso
from src.core.models.Rol import Rol
from src.core.models.RolPoseePermiso import RolPoseePermiso
from sqlalchemy import select


PERMISOS_USUARIOS = (
    "user_index",
    "user_new",
    "user_update",
    "user_destroy",
)


def load_permisos() -> None:
    """Crea los permisos y los asigna al rol Administrador."""
    rol_admin = db.session.execute(
        select(Rol).where(Rol.nombre == "Administrador")
    ).scalar_one_or_none()

    if rol_admin is None:
        raise ValueError("No existe el rol Administrador.")

    for nombre in PERMISOS_USUARIOS:
        permiso = db.session.execute(
            select(Permiso).where(Permiso.nombre == nombre)
        ).scalar_one_or_none()

        if permiso is None:
            permiso = Permiso(nombre=nombre)
            db.session.add(permiso)
            db.session.flush()

        asociacion = db.session.get(
            RolPoseePermiso,
            (rol_admin.idRol, permiso.idPermiso),
        )

        if asociacion is None:
            db.session.add(
                RolPoseePermiso(
                    idRol=rol_admin.idRol,
                    idPermiso=permiso.idPermiso,
                )
            )

    db.session.commit()

