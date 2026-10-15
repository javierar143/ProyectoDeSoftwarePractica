
"""Consultas de búsqueda, filtrado y paginación de usuarios."""

from sqlalchemy import asc, desc, func, or_, select

from src.core.database import db
from src.core.models.Personal import Personal
from src.core.models.Rol import Rol
from src.core.models.Usuario import Usuario
from src.core.models.UsuarioEsJefeSector import UsuarioEsJefeSector


def _construir_condiciones(filtros: dict) -> list:
    """Construye las condiciones SQL a partir de filtros validados."""
    condiciones = []
    busqueda = filtros.get("buscar", "").strip()

    if busqueda:
        patron = f"%{busqueda}%"
        condiciones.append(
            or_(
                Usuario.email.ilike(patron),
                Usuario.alias.ilike(patron),
                Personal.nombre.ilike(patron),
                Personal.apellido.ilike(patron),
                Personal.dni.ilike(patron),
                func.concat(
                    Personal.nombre, " ", Personal.apellido
                ).ilike(patron),
            )
        )

    if filtros.get("activo") == "1":
        condiciones.append(Usuario.isActive.is_(True))
    elif filtros.get("activo") == "0":
        condiciones.append(Usuario.isActive.is_(False))

    if filtros.get("rol_id") is not None:
        condiciones.append(Usuario.idRol == filtros["rol_id"])

    if filtros.get("sector_id") is not None:
        condiciones.append(
            UsuarioEsJefeSector.idSector == filtros["sector_id"]
        )

    return condiciones


def _aplicar_filtros(consulta, filtros: dict):
    """Aplica las relaciones y condiciones comunes a una consulta."""
    consulta = (
        consulta
        .join(Rol, Usuario.idRol == Rol.idRol)
        .join(Personal, Usuario.idPersonal == Personal.idPersonal)
    )

    if filtros.get("sector_id") is not None:
        consulta = consulta.join(
            UsuarioEsJefeSector,
            UsuarioEsJefeSector.idUser == Usuario.id_user,
        )

    return consulta.where(*_construir_condiciones(filtros))


def _obtener_orden(filtros: dict) -> list:
    """Devuelve las columnas de ordenamiento validadas."""
    columnas = {
        "fecha": (Usuario.inserted_at,),
        "apellido_nombre": (Personal.apellido, Personal.nombre),
        "email": (Usuario.email,),
    }

    sentido = asc if filtros.get("sentido") == "asc" else desc
    orden = columnas[filtros["orden"]]

    criterios = [sentido(columna) for columna in orden]
    criterios.append(asc(Usuario.id_user))

    return criterios


def buscar_paginado(
    filtros: dict,
    elementos_por_pagina: int,
) -> tuple[list[tuple[Usuario, str]], int]:
    """Busca usuarios y devuelve la página y el total de coincidencias.

    Args:
        filtros: Parámetros previamente validados y normalizados.
        elementos_por_pagina: Cantidad configurada de resultados por página.

    Returns:
        Una tupla con los usuarios de la página y el total de coincidencias.
    """
    consulta_total = _aplicar_filtros(
        select(func.count(Usuario.id_user)),
        filtros,
    )
    total = db.session.execute(consulta_total).scalar_one()

    pagina = filtros["pagina"]
    desplazamiento = (pagina - 1) * elementos_por_pagina

    consulta = _aplicar_filtros(
        select(Usuario, Rol.nombre),
        filtros,
    )
    consulta = consulta.order_by(*_obtener_orden(filtros))
    consulta = consulta.offset(desplazamiento).limit(elementos_por_pagina)

    resultados = list(db.session.execute(consulta).tuples().all())

    return resultados, total
