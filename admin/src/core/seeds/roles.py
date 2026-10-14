
"""Carga los roles iniciales de la aplicación."""

from sqlalchemy import select

from src.core.database import db
from src.core.models.Rol import Rol


ROLES_INICIALES = (
    "Administrador",
    "Jefe de Servicio",
    "Servicio de Alimentación",
    "Sector Comedor",
)


def load_roles() -> None:
    """Crea los roles iniciales que todavía no existen."""
    for nombre in ROLES_INICIALES:
        statement = select(Rol).where(Rol.nombre == nombre)
        rol = db.session.execute(statement).scalar_one_or_none()

        if rol is None:
            db.session.add(Rol(nombre=nombre))

    db.session.flush()
