"""Completa las asignaciones de sector de los Jefes de Servicio."""

from datetime import datetime

from sqlalchemy import select

from src.core.database import db
from src.core.models.Rol import Rol
from src.core.models.Sector import Sector
from src.core.models.SectorCompuestoPorPersonal import (
    SectorCompuestoPorPersonal,
)
from src.core.models.Usuario import Usuario


def load_asignaciones_jefes_sector() -> dict:
    """
    Asigna el sector de Personal a los Jefes de Servicio
    que todavía no tienen un sector en su cuenta.

    Solo realiza la asignación cuando existe exactamente
    un sector de Personal y dicho sector está activo.
    """

    usuarios = db.session.execute(
        select(Usuario)
        .join(Rol, Rol.idRol == Usuario.idRol)
        .where(
            Rol.nombre == "Jefe de Servicio",
            Usuario.idSector.is_(None),
        )
    ).scalars().all()

    asignados = 0
    sin_sector_origen = 0
    requieren_revision = 0

    try:
        for usuario in usuarios:
            sectores = db.session.execute(
                select(Sector.idSector, Sector.isActive)
                .join(
                    SectorCompuestoPorPersonal,
                    SectorCompuestoPorPersonal.idSector
                    == Sector.idSector,
                )
                .where(
                    SectorCompuestoPorPersonal.idPersonal
                    == usuario.idPersonal
                )
            ).all()

            sectores_unicos = {
                id_sector: activo
                for id_sector, activo in sectores
            }

            if not sectores_unicos:
                sin_sector_origen += 1
                continue

            if len(sectores_unicos) != 1:
                requieren_revision += 1
                continue

            id_sector, sector_activo = next(
                iter(sectores_unicos.items())
            )

            if not sector_activo:
                requieren_revision += 1
                continue

            usuario.idSector = id_sector
            usuario.updated_at = datetime.now()
            asignados += 1

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return {
        "asignados": asignados,
        "sin_sector_origen": sin_sector_origen,
        "requieren_revision": requieren_revision,
    }