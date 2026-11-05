
from flask import abort, session

from src.core.services.usuarios import usuario as usuario_service


def set_authenticated_user(user_id: int) -> None:
    session["user_id"] = user_id


def get_authenticated_user_id() -> int | None:
    user_id = session.get("user_id")
    return user_id


def clear_session() -> None:
    session.clear()


def is_authenticated() -> bool:
    user_id = get_authenticated_user_id()
    return user_id is not None


def require_authentication() -> None:
    user_id = get_authenticated_user_id()

    if user_id is None:
        abort(401)

    usuario_actual = usuario_service.get_by_id(user_id)

    if usuario_actual is None or not usuario_actual.isActive:
        clear_session()
        abort(401)
