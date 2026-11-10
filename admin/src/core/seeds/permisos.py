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

PERMISOS_PERSONAL = (
    "personal_index",
    "personal_new",
    "personal_update",
    "personal_destroy",
    "personal_import",
    "personal_create_residente", 
    "personal_manage_all_sectors",
)


def load_permisos() -> None:
    """Carga los permisos iniciales en la base de datos y los asigna al rol Administrador y al rol Jefe de Servicio."""
    rol_admin = db.session.execute(
        select(Rol).where(Rol.nombre == "Administrador")
    ).scalar_one_or_none()

    if rol_admin is None:
        raise ValueError("No existe el rol Administrador.")

    for nombre in PERMISOS_USUARIOS + PERMISOS_PERSONAL:
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
            
    # Se asignan permisos de personal al rol Servicio de Alimentación
    rol_alimentacion = db.session.execute(
         select(Rol).where(Rol.nombre == "Servicio de Alimentación")
    ).scalar_one_or_none()

    if rol_alimentacion is not None:
        for nombre in PERMISOS_PERSONAL:
            permiso = db.session.execute(
                select(Permiso).where(Permiso.nombre == nombre)
            ).scalar_one_or_none()

            if permiso is not None:
                asociacion = db.session.get(
                    RolPoseePermiso,
                    (rol_alimentacion.idRol, permiso.idPermiso),
                )

                if asociacion is None:
                    db.session.add(
                        RolPoseePermiso(
                            idRol=rol_alimentacion.idRol,
                            idPermiso=permiso.idPermiso,
                        )
                    )

    # Se asignan permisos de personal al rol Jefe de Servicio
    rol_jefe = db.session.execute(
        select(Rol).where(Rol.nombre == "Jefe de Servicio")
    ).scalar_one_or_none()

    if rol_jefe is not None:
        # Permisos específicos para el rol Jefe de Servicio
        permisos_jefe = (
            "personal_index",
            "personal_new",
            "personal_update",
            "personal_destroy",
            "personal_import",
        )
        
        for nombre in permisos_jefe:
            permiso = db.session.execute(
                select(Permiso).where(Permiso.nombre == nombre)
            ).scalar_one_or_none()
            
            if permiso is not None:
                asociacion_jefe = db.session.get(
                    RolPoseePermiso,
                    (rol_jefe.idRol, permiso.idPermiso),
                )
                if asociacion_jefe is None:
                    db.session.add(
                        RolPoseePermiso(
                            idRol=rol_jefe.idRol,
                            idPermiso=permiso.idPermiso,
                        )
                    )

    db.session.commit()

