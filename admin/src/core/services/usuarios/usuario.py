"""Servicios relacionados con la gestión de usuarios."""

from datetime import datetime

from src.core.models.Usuario import Usuario
from src.core.repositories.usuarios import rol
from src.core.repositories.usuarios import usuario as repo_usuario
from src.core.security.password import hash_password


def get_all() -> list[Usuario]:
    """Obtiene todos los usuarios registrados."""
    return repo_usuario.get_all()


def get_by_id(user_id: int) -> Usuario | None:
    """Obtiene un usuario por su identificador."""
    return repo_usuario.get_by_id(user_id)


def create(
    email: str,
    alias: str,
    password: str,
    is_system_admin: bool,
    rol_nombre: str,
    personal_id: int,
) -> Usuario:
    """Crea un usuario si los datos y sus asociaciones son válidos.

    Raises:
        ValueError: Si los datos son inválidos, el email ya existe,
            el Personal ya tiene un usuario o el rol no es válido.
    """
    email = email.strip()
    alias = alias.strip()
    rol_nombre = rol_nombre.strip()

    if not email or "@" not in email or not alias or not password.strip():
        raise ValueError("Completá correctamente los campos obligatorios.")

    usuario_existente = repo_usuario.get_by_email(email)
    if usuario_existente is not None:
        raise ValueError("El email ya está registrado.")

    usuario_por_personal = repo_usuario.get_by_personal_id(personal_id)
    if usuario_por_personal is not None:
        raise ValueError(
            "El Personal seleccionado ya tiene un usuario asociado."
        )

    rol_encontrado = rol.get_by_name(rol_nombre)
    if rol_encontrado is None:
        raise ValueError("El rol seleccionado no existe.")

    ahora = datetime.now()

    nuevo_usuario = Usuario(
        email=email,
        alias=alias,
        password_hash=hash_password(password),
        isSystemAdmin=is_system_admin,
        isActive=True,
        updated_at=ahora,
        inserted_at=ahora,
        idRol=rol_encontrado.idRol,
        idPersonal=personal_id,
    )

    repo_usuario.create(nuevo_usuario)

    return nuevo_usuario


def update(
    user_id: int,
    email: str,
    alias: str,
    rol_id: int,
    is_system_admin: bool | None = None,
    password: str = "",
) -> Usuario | None:
    """Actualiza los datos de un usuario existente.

    Raises:
        ValueError: Si el email ya pertenece a otro usuario.
    """
    email = email.strip()
    alias = alias.strip()

    usuario_actual = repo_usuario.get_by_id(user_id)
    email_existente = repo_usuario.get_by_email(email)
    rol_encontrado = rol.get_by_id(rol_id)

    email_disponible = (
        email_existente is None
        or email_existente.id_user == user_id
    )

    usuario_actualizado = None

    if usuario_actual is not None and not email:
        raise ValueError("El email es obligatorio.")

    if usuario_actual is not None and not email_disponible:
        raise ValueError("El email ya está registrado.")

    if usuario_actual is not None and rol_encontrado is not None:
        usuario_actual.email = email
        usuario_actual.alias = alias
        usuario_actual.idRol = rol_encontrado.idRol

        if is_system_admin is not None:
            usuario_actual.isSystemAdmin = is_system_admin

        if password:
            usuario_actual.password_hash = hash_password(password)

        usuario_actual.updated_at = datetime.now()
        usuario_actualizado = repo_usuario.update(usuario_actual)

    return usuario_actualizado


def set_active(user_id: int, is_active: bool) -> Usuario | None:
    """Activa o bloquea una cuenta, respetando las restricciones de seguridad."""
    usuario_actual = repo_usuario.get_by_id(user_id)

    if usuario_actual is None:
        return None

    rol_actual = rol.get_by_id(usuario_actual.idRol)

    es_administrador = (
        usuario_actual.isSystemAdmin
        or (
            rol_actual is not None
            and rol_actual.nombre == "Administrador"
        )
    )

    if es_administrador and not is_active:
        raise ValueError(
            "No se puede bloquear una cuenta de administrador."
        )

    usuario_actual.isActive = is_active
    usuario_actual.updated_at = datetime.now()

    return repo_usuario.update(usuario_actual)


def get_all_with_role() -> list[tuple[Usuario, str]]:
    """Obtiene todos los usuarios junto con el nombre de su rol."""
    return repo_usuario.get_all_with_role()
