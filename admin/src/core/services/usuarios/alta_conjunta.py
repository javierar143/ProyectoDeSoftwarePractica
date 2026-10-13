"""Servicio para crear Personal y Usuario en una única transacción."""

from datetime import datetime

from src.core.database import db
from src.core.models.Personal import Personal
from src.core.models.Usuario import Usuario
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
) -> tuple[Personal, Usuario]:
    """Crea Personal y Usuario y confirma ambas altas conjuntamente."""
    try:
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

        if not all(
            (
                dni.strip(),
                nombre.strip(),
                apellido.strip(),
                email.strip(),
                "@" in email,
                alias.strip(),
                password.strip(),
                rol_nombre.strip(),
            )
        ):
            raise ValueError("Completá correctamente todos los campos obligatorios.")

        ahora = datetime.now()

        nuevo_personal = Personal(
            dni=dni.strip(),
            nombre=nombre.strip(),
            apellido=apellido.strip(),
            idTipoPersonal=id_tipo_personal,
            idTipoMenu=id_tipo_menu,
            isActive=True,
            inserted_at=ahora,
            updated_at=ahora,
        )

        db.session.add(nuevo_personal)
        db.session.flush()

        nuevo_usuario = Usuario(
            email=email.strip(),
            alias=alias.strip(),
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

    except Exception:
        db.session.rollback()
        raise

    return nuevo_personal, nuevo_usuario
