"""Datos temporales para probar el alta de usuarios."""

from datetime import datetime

from src.core.database import db
from src.core.models.PersonalTemporal import PersonalTemporal
from src.core.models.Rol import Rol
from src.core.models.Usuario import Usuario
from src.core.security.password import hash_password


PERSONAL_TEMPORAL = [
    {
        "idPersonal": 1,
        "dni": "11111111",
        "nombre": "Usuario Personal 01",
        "apellido": "Temporal",
    },
    {
        "idPersonal": 2,
        "dni": "22222222",
        "nombre": "Usuario Personal 02",
        "apellido": "Temporal",
    },
    {
        "idPersonal": 3,
        "dni": "33333333",
        "nombre": "Usuario Personal 03",
        "apellido": "Temporal",
    },
    {
        "idPersonal": 4,
        "dni": "44444444",
        "nombre": "Usuario Personal 04",
        "apellido": "Temporal",
    },
    {
        "idPersonal": 5,
        "dni": "55555555",
        "nombre": "Usuario Personal 05",
        "apellido": "Temporal",
    },
]


ROLES_TEMPORALES = [
    {"idRol": 1, "nombre": "Administrador"},
    {"idRol": 2, "nombre": "Jefe de Servicio"},
    {"idRol": 3, "nombre": "Servicio de Alimentación"},
    {"idRol": 4, "nombre": "Sector Comedor"},
]


def load_personal_temporal() -> None:
    """Carga los datos temporales necesarios para probar usuarios."""
    for datos in PERSONAL_TEMPORAL:
        persona = db.session.get(
            PersonalTemporal,
            datos["idPersonal"],
        )

        if persona is None:
            persona = PersonalTemporal(**datos)
            db.session.add(persona)
        else:
            persona.dni = datos["dni"]
            persona.nombre = datos["nombre"]
            persona.apellido = datos["apellido"]

    for datos in ROLES_TEMPORALES:
        rol = db.session.get(Rol, datos["idRol"])

        if rol is None:
            rol = Rol(**datos)
            db.session.add(rol)
        else:
            rol.nombre = datos["nombre"]

    db.session.commit()

    administrador = db.session.get(Usuario, 1)

    if administrador is None:
        ahora = datetime.now()

        administrador = Usuario(
            email="admin@temporal.com",
            alias="Administrador",
            password_hash=hash_password("admin123"),
            isSystemAdmin=True,
            isActive=True,
            updated_at=ahora,
            inserted_at=ahora,
            idRol=1,
            idPersonal=1,
        )

        db.session.add(administrador)
        db.session.commit()

    return None