
"""Servicio para crear Personal y Usuario en una única transacción."""

from datetime import datetime

from sqlalchemy.exc import IntegrityError

from src.core.database import db
from src.core.models.Personal import Personal
from src.core.models.Usuario import Usuario
from src.core.models.SectorCompuestoPorPersonal import SectorCompuestoPorPersonal
from src.core.repositories.usuarios import rol
from src.core.repositories.usuarios import usuario as repo_usuario
from src.core.security.password import hash_password
from src.core.services.personal import personal



def create(
    dni: str,
    nombre: str,
    apellido: str,
    id_tipo_personal: int,
    id_tipo_menu: int,
    email: str,
    alias: str,
    password: str,
    is_system_admin: bool,
    rol_nombre: str,
    id_sector: int | None = None,
) -> tuple[Personal, Usuario]:
    """Crea Personal y Usuario en una única transacción.

    Raises:
        ValueError: Si hay campos inválidos, duplicados o referencias
            inexistentes.
    """
    dni = dni.strip()
    nombre = nombre.strip()
    apellido = apellido.strip()
    email = email.strip()
    alias = alias.strip()
    rol_nombre = rol_nombre.strip()

    if not all(
        (
            dni,
            nombre,
            apellido,
            email,
            "@" in email,
            alias,
            password.strip(),
            rol_nombre,
        )
    ):
        raise ValueError(
            "Completá correctamente todos los campos obligatorios."
        )

    if personal.get_by_dni(dni) is not None:
        raise ValueError("El DNI ya está registrado.")

    if repo_usuario.get_by_email(email) is not None:
        raise ValueError("El email ya está registrado.")

    rol_encontrado = rol.get_by_name(rol_nombre)
    if rol_encontrado is None:
        raise ValueError("El rol seleccionado no existe.")

    tipos_personal = personal.get_tipos_personal()
    tipos_menu = personal.get_tipos_menu()

    tipo_personal_valido = any(
        tipo.idTipoPersonal == id_tipo_personal
        for tipo in tipos_personal
    )
    tipo_menu_valido = any(
        menu.idTipoMenu == id_tipo_menu
        for menu in tipos_menu
    )

    if not tipo_personal_valido or not tipo_menu_valido:
        raise ValueError("El tipo de personal o menú no es válido.")

    tipo_personal = next(
        tipo
        for tipo in tipos_personal
        if tipo.idTipoPersonal == id_tipo_personal
    )

    nombre_tipo = tipo_personal.nombre.lower()

    if "residente" in nombre_tipo:
        id_sector = None

    elif "fijo" in nombre_tipo and id_sector is None:
        raise ValueError(
            "El personal fijo requiere un sector asignado obligatoriamente."
        )

    if id_sector is not None:
        sectores = personal.get_sectores()

        sector_valido = any(
            sector.idSector == id_sector
            for sector in sectores
        )

        if not sector_valido:
            raise ValueError(
                "El sector seleccionado no existe o está inactivo."
            )

    ahora = datetime.now()

    nuevo_personal = Personal(
        dni=dni,
        nombre=nombre,
        apellido=apellido,
        idTipoPersonal=id_tipo_personal,
        idTipoMenu=id_tipo_menu,
        isActive=True,
        inserted_at=ahora,
        updated_at=ahora,
    )

    try:
        db.session.add(nuevo_personal)
        db.session.flush()

        if id_sector is not None:
            db.session.add(
                SectorCompuestoPorPersonal(
                    idSector=id_sector,
                    idPersonal=nuevo_personal.idPersonal,
                )
            )

        nuevo_usuario = Usuario(
            email=email,
            alias=alias,
            password_hash=hash_password(password),
            isSystemAdmin=is_system_admin,
            isActive=True,
            inserted_at=ahora,
            updated_at=ahora,
            idRol=rol_encontrado.idRol,
            idPersonal=nuevo_personal.idPersonal,
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

    except IntegrityError as error:
        db.session.rollback()
        raise ValueError(
            "No se pudo crear el usuario: el DNI o el email ya están "
            "registrados, o existe una referencia inválida."
        ) from error
    except Exception:
        db.session.rollback()
        raise

    return nuevo_personal, nuevo_usuario
