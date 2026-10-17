
"""Carga el personal y las cuentas iniciales para desarrollo y pruebas."""

from datetime import datetime

from sqlalchemy import select

from src.core.database import db
from src.core.models.Personal import Personal
from src.core.models.Rol import Rol
from src.core.models.TipoMenu import TipoMenu
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.Usuario import Usuario
from src.core.security.password import hash_password
from src.core.models.Sector import Sector
from src.core.repositories.personal import personal as repo_personal
from src.core.models.SectorCompuestoPorPersonal import SectorCompuestoPorPersonal


PERSONAL_INICIAL = (
    {
        "dni": "11111111",
        "nombre": "Juan",
        "apellido": "Soyadmin",
        "sector": "Dirección", 
        "usuario": {
            "email": "admin@temporal.com",
            "alias": "Administrador",
            "rol": "Administrador",
            "password": "1234",
            "es_admin": True,
        },
    },
    {
        "dni": "22222222",
        "nombre": "Fulano",
        "apellido": "Detal",
        "sector": "Alimentación",
        "usuario": {
            "email": "jefe@ejemplo.com",
            "alias": "Jefe de Servicio",
            "rol": "Jefe de Servicio",
            "password": "1234",
            "es_admin": False,
        },
    },
    {
        "dni": "33333333",
        "nombre": "Mengano",
        "apellido": "Perez",
        "sector": "Quirófano",
        "usuario": None,
    },
    {
        "dni": "44444444",
        "nombre": "Pascuala",
        "apellido": "Gomez",
        "sector": "Quirófano",
        "usuario": None,
    },
)


from src.core.models.SectorCompuestoPorPersonal import SectorCompuestoPorPersonal

def load_personal_inicial() -> None:
    """Carga el personal inicial y solo las cuentas expresamente definidas."""
    tipo_personal = db.session.execute(
        select(TipoPersonal).where(TipoPersonal.nombre == "Fijo")
    ).scalar_one_or_none()
    tipo_menu = db.session.execute(
        select(TipoMenu).where(TipoMenu.nombre == "General")
    ).scalar_one_or_none()

    if tipo_personal is None or tipo_menu is None:
        raise ValueError("Deben cargarse primero los tipos iniciales.")

    ahora = datetime.now()

    for datos in PERSONAL_INICIAL:
        persona = db.session.execute(
            select(Personal).where(Personal.dni == datos["dni"])
        ).scalar_one_or_none()

        if persona is None:
            persona = Personal(
                dni=datos["dni"],
                nombre=datos["nombre"],
                apellido=datos["apellido"],
                isActive=True,
                inserted_at=ahora,
                updated_at=ahora,
                idTipoPersonal=tipo_personal.idTipoPersonal,
                idTipoMenu=tipo_menu.idTipoMenu,
            )
            db.session.add(persona)
            db.session.flush()

        id_sector = None
        nombre_sector = datos.get("sector")
        if nombre_sector:
            sector = db.session.execute(
                select(Sector).where(Sector.nombre == nombre_sector)
            ).scalar_one_or_none()
            if sector is None:
                raise ValueError(f"No existe el sector '{nombre_sector}'.")
            id_sector = sector.idSector

            ya_asignado = db.session.execute(
                select(SectorCompuestoPorPersonal).where(
                    SectorCompuestoPorPersonal.idPersonal == persona.idPersonal,
                    SectorCompuestoPorPersonal.idSector == id_sector,
                )
            ).scalar_one_or_none()
            if ya_asignado is None:
                db.session.add(
                    SectorCompuestoPorPersonal(
                        idSector=id_sector,
                        idPersonal=persona.idPersonal,
                    )
                )

        datos_usuario = datos["usuario"]
        if datos_usuario is None:
            continue

        rol = db.session.execute(
            select(Rol).where(Rol.nombre == datos_usuario["rol"])
        ).scalar_one_or_none()
        if rol is None:
            raise ValueError(f"No existe el rol {datos_usuario['rol']}.")

        usuario_por_email = db.session.execute(
            select(Usuario).where(Usuario.email == datos_usuario["email"])
        ).scalar_one_or_none()
        usuario_por_persona = db.session.execute(
            select(Usuario).where(Usuario.idPersonal == persona.idPersonal)
        ).scalar_one_or_none()

        if usuario_por_email is not None or usuario_por_persona is not None:
            continue

        id_sector_usuario = (
            id_sector if datos_usuario["rol"] == "Jefe de Servicio" else None
        )

        db.session.add(
            Usuario(
                email=datos_usuario["email"],
                alias=datos_usuario["alias"],
                password_hash=hash_password(datos_usuario["password"]),
                isSystemAdmin=datos_usuario["es_admin"],
                isActive=True,
                inserted_at=ahora,
                updated_at=ahora,
                idRol=rol.idRol,
                idPersonal=persona.idPersonal,
                idSector=id_sector_usuario,
            )
        )

    db.session.flush()