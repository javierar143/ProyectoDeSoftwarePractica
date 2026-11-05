
"""Controles para la asignación de privilegios de administrador."""

from flask import abort, session

from src.core.repositories.usuarios import usuario as repo_usuario



def _es_rol_administrador(nombre_rol: str | None) -> bool:
    """Indica si el nombre corresponde al rol Administrador."""
    return (
        nombre_rol is not None
        and nombre_rol.strip().casefold() == "administrador"
    )


def require_admin_privilege_change(
    rol_anterior: str | None,
    is_system_admin_anterior: bool,
    rol_nuevo: str | None,
    is_system_admin_nuevo: bool,
) -> None:
    """Exige ser administrador del sistema para cambiar privilegios."""

    cambio_rol_administrador = (
        _es_rol_administrador(rol_anterior)
        != _es_rol_administrador(rol_nuevo)
    )

    cambio_admin_sistema = (
        is_system_admin_anterior != is_system_admin_nuevo
    )

    if not cambio_rol_administrador and not cambio_admin_sistema:
        return

    user_id = session.get("user_id")

    if user_id is None:
        abort(403)

    usuario_actual = repo_usuario.get_by_id(user_id)

    if (
        usuario_actual is None
        or not usuario_actual.isActive
        or not usuario_actual.isSystemAdmin
    ):
        abort(
            403,
            description=(
                "No tenés autorización para modificar privilegios "
                "de administrador."
            ),
        )
