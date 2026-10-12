
"""Carga los tipos iniciales de personal y menú."""

from sqlalchemy import select

from src.core.database import db
from src.core.models.TipoMenu import TipoMenu
from src.core.models.TipoPersonal import TipoPersonal


TIPOS_PERSONAL_INICIALES = ("Fijo", "Residente")
TIPOS_MENU_INICIALES = ("General", "Vegetariano", "Celíaco")


def load_tipos_iniciales() -> None:
    """Crea los tipos de personal y menú que todavía no existen."""
    for nombre in TIPOS_PERSONAL_INICIALES:
        statement = select(TipoPersonal).where(TipoPersonal.nombre == nombre)
        tipo = db.session.execute(statement).scalar_one_or_none()

        if tipo is None:
            db.session.add(TipoPersonal(nombre=nombre))

    for nombre in TIPOS_MENU_INICIALES:
        statement = select(TipoMenu).where(TipoMenu.nombre == nombre)
        tipo = db.session.execute(statement).scalar_one_or_none()

        if tipo is None:
            db.session.add(TipoMenu(nombre=nombre))

    db.session.flush()
