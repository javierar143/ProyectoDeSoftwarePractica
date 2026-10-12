
"""Carga personas y usuarios ficticios para desarrollo y pruebas."""

from datetime import datetime

from sqlalchemy import select

from src.core.database import db
from src.core.models.Personal import Personal
from src.core.models.Rol import Rol
from src.core.models.TipoMenu import TipoMenu
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.Usuario import Usuario
from src.core.security.password import hash_password


PERSONAL_INICIAL = (
    {
        "dni": "11111111",
        "nombre": "Administrador",
        "apellido": "Prueba",
        "email": "admin@temporal.com",
        "alias": "Administrador",
        "rol": "Administrador",
        "password": "1234",
        "es_admin": True,
    },
    {
        "dni": "22222222",
        "nombre": "Jefe",
        "apellido": "Prueba",
        "email": "jefe@ejemplo.com",
        "alias": "Jefe de Servicio",
        "rol": "Jefe de Servicio",
        "password": "1234",
        "es_admin": False,
    },
    {
        "dni": "33333333",
        "nombre": "Alimentacion",
        "apellido": "Prueba",
        "email": "alimentacion@ejemplo.com",
        "alias": "Servicio de Alimentación",
        "rol": "Servicio de Alimentación",
        "password": "1234",
        "es_admin": False,
    },
    {
        "dni": "44444444",
        "nombre": "Comedor",
        "apellido": "Prueba",
        "email": "comedor@ejemplo.com",
        "alias": "Sector Comedor",
        "rol": "Sector Comedor",
        "password": "1234",
        "es_admin": False,
    },
)


def load_personal_inicial() -> None:
    """Crea las personas y los usuarios iniciales que no existen."""
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

        rol = db.session.execute(
            select(Rol).where(Rol.nombre == datos["rol"])
        ).scalar_one_or_none()

        if rol is None:
            raise ValueError(f"No existe el rol {datos['rol']}.")

        usuario_por_email = db.session.execute(
            select(Usuario).where(Usuario.email == datos["email"])
        ).scalar_one_or_none()

        usuario_por_persona = db.session.execute(
            select(Usuario).where(
                Usuario.idPersonal == persona.idPersonal
            )
        ).scalar_one_or_none()

        if usuario_por_email is None and usuario_por_persona is None:
            usuario = Usuario(
                email=datos["email"],
                alias=datos["alias"],
                password_hash=hash_password(datos["password"]),
                isSystemAdmin=datos["es_admin"],
                isActive=True,
                inserted_at=ahora,
                updated_at=ahora,
                idRol=rol.idRol,
                idPersonal=persona.idPersonal,
            )
            db.session.add(usuario)
        elif usuario_por_email is not None:
            if usuario_por_email.idPersonal != persona.idPersonal:
                raise ValueError(
                    f"El correo {datos['email']} ya pertenece a otra persona."
                )

    db.session.flush()
