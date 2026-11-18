"""Carga los permisos iniciales de la aplicación y los asigna a los roles."""

from sqlalchemy import select

from src.core.database import db
from src.core.models.Permiso import Permiso
from src.core.models.Rol import Rol
from src.core.models.RolPoseePermiso import RolPoseePermiso


PERMISOS_USUARIOS = (
    "user_index",
    "user_new",
    "user_update",
    "user_destroy",
)

PERMISOS_SECTORES = (
    "sector_index",  # listar y ver detalle de sectores
)

PERMISOS_PERSONAL = (
    "personal_index",
    "personal_new",
    "personal_update",
    "personal_destroy",
    "personal_import",
    "personal_create_residente",
    "personal_manage_all_sectors",
)

PERMISOS_POR_ROL = {
    "Administrador": PERMISOS_USUARIOS + PERMISOS_PERSONAL,
    "Servicio de Alimentación": PERMISOS_PERSONAL + PERMISOS_SECTORES,
    "Jefe de Servicio": (
        "personal_index",
        "personal_new",
        "personal_update",
        "personal_destroy",
        "personal_import",
    ),
    "Sector Comedor": (
        "personal_index",
        "personal_manage_all_sectors",
    )+ PERMISOS_SECTORES,
}


def load_permisos() -> None:
    """Crea los permisos y los asigna a cada rol de forma idempotente."""
    for nombre_rol, nombres_permisos in PERMISOS_POR_ROL.items():
        rol = db.session.execute(
            select(Rol).where(Rol.nombre == nombre_rol)
        ).scalar_one_or_none()

        if rol is None:
            raise ValueError(f"No existe el rol {nombre_rol}.")

        for nombre in nombres_permisos:
            permiso = db.session.execute(
                select(Permiso).where(Permiso.nombre == nombre)
            ).scalar_one_or_none()

            if permiso is None:
                permiso = Permiso(nombre=nombre)
                db.session.add(permiso)
                db.session.flush()

            asociacion = db.session.get(
                RolPoseePermiso,
                (rol.idRol, permiso.idPermiso),
            )

            if asociacion is None:
                db.session.add(
                    RolPoseePermiso(
                        idRol=rol.idRol,
                        idPermiso=permiso.idPermiso,
                    )
                )

    db.session.commit()