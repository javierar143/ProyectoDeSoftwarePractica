"""Servicios relacionados con la gestión de usuarios."""

from datetime import datetime

from src.core.models.Usuario import Usuario
from src.core.repositories import usuario


def get_all() -> list[Usuario]:
    """Obtiene todos los usuarios."""
    usuarios = usuario.get_all()

    return usuarios


def get_by_id(user_id: int) -> Usuario | None:
    """Obtiene un usuario por su identificador."""
    usuario_encontrado = usuario.get_by_id(user_id)

    return usuario_encontrado


def create(
    email: str,
    alias: str,
    password_hash: str,
    is_system_admin: bool,
    rol_id: int,
    personal_id: int,
) -> Usuario | None:
    """Crea un usuario validando que su email sea único."""
    usuario_existente = usuario.get_by_email(email)
    nuevo_usuario = None

    if usuario_existente is None:
        ahora = datetime.now()
        nuevo_usuario = Usuario(
            email=email,
            alias=alias,
            password_hash=password_hash,
            isSystemAdmin=is_system_admin,
            isActive=True,
            updated_at=ahora,
            inserted_at=ahora,
            idRol=rol_id,
            idPersonal=personal_id,
        )
        usuario.create(nuevo_usuario)

    return nuevo_usuario


def update(
    user_id: int,
    email: str,
    alias: str,
    rol_id: int,
) -> Usuario | None:
    """Modifica los datos administrables de un usuario."""
    usuario_actual = usuario.get_by_id(user_id)
    usuario_actualizado = None

    if usuario_actual is not None:
        email_existente = usuario.get_by_email(email)

        if (
            email_existente is None
            or email_existente.id_user == user_id
        ):
            usuario_actual.email = email
            usuario_actual.alias = alias
            usuario_actual.idRol = rol_id
            usuario_actual.updated_at = datetime.now()

            usuario_actualizado = usuario.update(usuario_actual)

    return usuario_actualizado


def set_active(user_id: int, is_active: bool) -> Usuario | None:
    """Activa o desactiva lógicamente una cuenta de usuario."""
    usuario_actual = usuario.get_by_id(user_id)
    usuario_actualizado = None

    if usuario_actual is not None:
        usuario_actual.isActive = is_active
        usuario_actual.updated_at = datetime.now()
        usuario_actualizado = usuario.update(usuario_actual)

    return usuario_actualizado

def get_all_with_role() -> list[tuple[Usuario, str]]:
    """Obtiene todos los usuarios junto con el nombre de su rol."""
    usuarios = usuario.get_all_with_role()

    return usuarios