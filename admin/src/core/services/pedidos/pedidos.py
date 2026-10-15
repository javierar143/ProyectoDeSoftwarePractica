"""Servicios para la creación, actualización, consulta y eliminación de pedidos."""

from datetime import date

from sqlalchemy import select, exists

from src.core.models import SectorCompuestoPorPersonal
from src.core.database import db
from src.core.models.enums import (
    CondicionCupo,
    EstadoAutorizacion,
    EstadoPedido,
    Periodicidad,
)
from src.core.models.Pedido import Pedido
from src.core.models.Personal import Personal
from src.core.models.Solicitud import Solicitud
from src.core.models.TipoPersonal import TipoPersonal
from src.core.repositories.pedidos import pedidos as repo_pedidos
from src.core.services.configuracion import obtener_configuracion
from src.core.services.cupos import cupos


class PedidoForbiddenError(Exception):
    """Error cuando un usuario intenta operar sobre un pedido de otro sector (HTTP 403)."""

    pass


class PedidoNotFoundError(Exception):
    """Error cuando el pedido solicitado no existe (HTTP 404)."""

    pass


class PedidoValidationError(Exception):
    """Error para datos inválidos o reglas que devuelven HTTP 400."""

    pass


class PedidoConflictError(Exception):
    """Error para conflictos o duplicados que devuelven HTTP 409."""

    pass


def obtener_sector_de_personal(id_personal: int | None) -> int | None:
    """Obtiene el idSector asignado a una persona según la tabla intermedia, o None si no tiene."""

    if id_personal is None:
        return None

    relacion = db.session.scalar(
        db.select(SectorCompuestoPorPersonal).filter_by(idPersonal=id_personal)
    )
    if relacion is not None:
        return relacion.idSector

    return None


def pertenece_a_sector(id_personal: int, id_sector: int) -> bool:
    """Consulta en la tabla intermedia si el personal fijo pertenece al sector indicado."""
    stmt = select(
        exists().where(
            SectorCompuestoPorPersonal.idPersonal == id_personal,
            SectorCompuestoPorPersonal.idSector == id_sector,
        )
    )
    return bool(db.session.scalar(stmt))


def validar_sector_personal(persona: Personal, id_sector_jefe: int) -> None:
    """
    Verifica que si la persona es Personal Fijo, su sector coincida con el del Jefe.
    Los Residentes pueden incorporarse a pedidos de cualquier sector sin esta validación.
    """
    tipo_personal = db.session.get(TipoPersonal, persona.idTipoPersonal)

    if (
        tipo_personal
        and "fijo" in tipo_personal.nombre.strip().lower()
        and not pertenece_a_sector(persona.idPersonal, id_sector_jefe)
    ):
        raise PedidoValidationError(
            f"La persona con ID {persona.idPersonal} es personal fijo y no pertenece al sector del Jefe de Servicio."
        )


def crear_pedido(
    id_jefe: int,
    id_sector: int,
    fecha_desde: date,
    periodicidad: str,
    comidas: dict[int, list[int]],
) -> Pedido:
    """
    Organiza la creación de un pedido (cabecera) y sus solicitudes (detalle),
    calculando qué viandas entran en cupo Regular y cuáles por Excepción.
    """
    if not comidas or not any(comidas.values()):
        raise PedidoValidationError(
            "El pedido debe incluir al menos una solicitud de comida."
        )

    try:
        periodicidad_enum = Periodicidad(periodicidad.lower())
    except (ValueError, AttributeError):
        raise PedidoValidationError("La periodicidad indicada no es válida.")

    if repo_pedidos.existe_pedido_en_sector_y_fecha(id_sector, fecha_desde):
        raise PedidoConflictError(
            "Ya existe un pedido registrado para este sector en la fecha indicada."
        )

    nuevo_pedido = Pedido(
        idUser=id_jefe,
        idSector=id_sector,
        fecha_desde=fecha_desde,
        periodicidad=periodicidad_enum,
        estado_general=EstadoPedido.CONFIRMADO,
    )

    solicitudes_a_guardar = []

    for id_tipo_comida_str, lista_personal in comidas.items():
        id_tipo_comida = int(id_tipo_comida_str)

        cupo = cupos.get_by_sector_y_comida(id_sector, id_tipo_comida)
        limite_cupo = cupo.cantComensales if cupo else 0

        contador_comida = 0
        vistos_en_comida = set()

        for id_personal in lista_personal:
            if id_personal in vistos_en_comida:
                raise PedidoConflictError(
                    f"La persona {id_personal} está repetida en la misma comida."
                )
            vistos_en_comida.add(id_personal)

            persona = db.session.get(Personal, id_personal)
            if not persona or not persona.isActive:
                raise PedidoValidationError(
                    f"La persona con ID {id_personal} no existe o está inactiva."
                )

            validar_sector_personal(persona, id_sector)

            if Solicitud.existe_duplicado(
                session=db.session,
                id_personal=id_personal,
                id_sector=id_sector,
                fecha=fecha_desde,
                id_tipo_comida=id_tipo_comida,
            ):
                raise PedidoConflictError(
                    f"Ya existe una solicitud para la persona {id_personal} en esa fecha y comida."
                )

            contador_comida += 1
            if contador_comida <= limite_cupo:
                condicion = CondicionCupo.REGULAR
            else:
                condicion = CondicionCupo.EXCEPCION

            nueva_solicitud = Solicitud(
                idPersonal=id_personal,
                idTipoComida=id_tipo_comida,
                idTipoMenu=persona.idTipoMenu,
                condicionCupo=condicion,
                estadoAutorizacion=EstadoAutorizacion.PENDIENTE,
                fecha_vianda=fecha_desde,
            )
            solicitudes_a_guardar.append(nueva_solicitud)

    return repo_pedidos.create_pedido_con_solicitudes(
        nuevo_pedido, solicitudes_a_guardar
    )


def actualizar_pedido(
    id_pedido: int,
    comidas: dict[int, list[int]],
    id_sector_jefe: int | None = None,
) -> Pedido:
    """
    Modifica un pedido existente si sigue en estado CONFIRMADO.
    Elimina las solicitudes anteriores y recalcula cupos (Regular/Excepción).
    """
    pedido = repo_pedidos.get_pedido_by_id(id_pedido)
    if not pedido:
        raise PedidoNotFoundError(f"El pedido con ID {id_pedido} no existe.")

    if id_sector_jefe is not None and pedido.idSector != id_sector_jefe:
        raise PedidoForbiddenError(
            "No tiene permisos para operar sobre un pedido de otro sector."
        )

    if pedido.estado_general != EstadoPedido.CONFIRMADO:
        raise PedidoConflictError(
            f"No se puede modificar un pedido que ya está {pedido.estado_general.value}."
        )

    if not comidas or not any(comidas.values()):
        raise PedidoValidationError(
            "El pedido actualizado debe incluir al menos una solicitud."
        )

    repo_pedidos.limpiar_solicitudes_de_pedido(id_pedido)

    solicitudes_a_guardar = []

    for id_tipo_comida_str, lista_personal in comidas.items():
        id_tipo_comida = int(id_tipo_comida_str)

        cupo = cupos.get_by_sector_y_comida(pedido.idSector, id_tipo_comida)
        limite_cupo = cupo.cantComensales if cupo else 0

        contador_comida = 0
        vistos_en_comida = set()

        for id_personal in lista_personal:
            if id_personal in vistos_en_comida:
                raise PedidoConflictError(
                    f"La persona {id_personal} está repetida en la misma comida."
                )
            vistos_en_comida.add(id_personal)

            persona = db.session.get(Personal, id_personal)
            if not persona or not persona.isActive:
                raise PedidoValidationError(
                    f"La persona con ID {id_personal} no existe o está inactiva."
                )

            validar_sector_personal(persona, pedido.idSector)

            if Solicitud.existe_duplicado(
                session=db.session,
                id_personal=id_personal,
                id_sector=pedido.idSector,
                fecha=pedido.fecha_desde,
                id_tipo_comida=id_tipo_comida,
            ):
                raise PedidoConflictError(
                    f"Ya existe una solicitud para la persona {id_personal} en esa fecha."
                )

            contador_comida += 1
            if contador_comida <= limite_cupo:
                condicion = CondicionCupo.REGULAR
            else:
                condicion = CondicionCupo.EXCEPCION

            nueva_solicitud = Solicitud(
                idPersonal=id_personal,
                idTipoComida=id_tipo_comida,
                idTipoMenu=persona.idTipoMenu,
                condicionCupo=condicion,
                estadoAutorizacion=EstadoAutorizacion.PENDIENTE,
                fecha_vianda=pedido.fecha_desde,
            )
            solicitudes_a_guardar.append(nueva_solicitud)

    return repo_pedidos.guardar_nuevas_solicitudes(pedido, solicitudes_a_guardar)


def borrar_pedido(id_pedido: int, id_sector_jefe: int | None = None) -> None:
    """Valida y elimina un pedido si sigue en estado CONFIRMADO."""
    pedido = repo_pedidos.get_pedido_by_id(id_pedido)
    if not pedido:
        raise PedidoNotFoundError(f"El pedido con ID {id_pedido} no existe.")

    if id_sector_jefe is not None and pedido.idSector != id_sector_jefe:
        raise PedidoForbiddenError(
            "No tiene permisos para operar sobre un pedido de otro sector."
        )

    if pedido.estado_general != EstadoPedido.CONFIRMADO:
        raise PedidoConflictError(
            f"No se puede eliminar un pedido que ya fue {pedido.estado_general.value}."
        )

    repo_pedidos.eliminar_pedido(pedido)


def obtener_detalle_pedido(id_pedido: int, id_sector_jefe: int | None = None) -> dict:
    """Devuelve el detalle completo de un pedido con totales pedidos y autorizados separados."""
    pedido = repo_pedidos.get_pedido_by_id(id_pedido)
    if not pedido:
        raise PedidoNotFoundError(f"El pedido con ID {id_pedido} no existe.")

    if id_sector_jefe is not None and pedido.idSector != id_sector_jefe:
        raise PedidoForbiddenError(
            "No tiene permisos para consultar un pedido de otro sector."
        )

    solicitudes = repo_pedidos.get_solicitudes_by_pedido(id_pedido)

    totales_pedidos: dict[str, int] = {}
    totales_autorizados: dict[str, int] = {}
    detalle_solicitudes = []

    for s in solicitudes:
        clave = f"comida_{s.idTipoComida}_menu_{s.idTipoMenu}"
        totales_pedidos[clave] = totales_pedidos.get(clave, 0) + 1
        if s.estadoAutorizacion == EstadoAutorizacion.AUTORIZADA:
            totales_autorizados[clave] = totales_autorizados.get(clave, 0) + 1

        detalle_solicitudes.append({
            "idSolicitud": s.idSolicitud,
            "idPersonal": s.idPersonal,
            "idTipoComida": s.idTipoComida,
            "idTipoMenu": s.idTipoMenu,
            "fecha_vianda": s.fecha_vianda.isoformat(),
            "condicionCupo": s.condicionCupo.value,
            "estadoAutorizacion": s.estadoAutorizacion.value,
        })

    resultado = {
        "idPedido": pedido.idPedido,
        "idSector": pedido.idSector,
        "fecha_desde": pedido.fecha_desde.isoformat(),
        "periodicidad": pedido.periodicidad.value,
        "estado": pedido.estado_general.value,
        "cantidades_pedidas": totales_pedidos,
        "solicitudes": detalle_solicitudes,
    }

    if pedido.estado_general in (EstadoPedido.AUTORIZADO, EstadoPedido.RECHAZADO):
        resultado["cantidades_autorizadas"] = totales_autorizados

    return resultado


def listar_pedidos_sector(
    id_sector: int,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    estado_str: str | None = None,
    id_tipo_comida: int | None = None,
    id_tipo_menu: int | None = None,
    page: int = 1,
) -> tuple[list[dict], int, int]:
    """Lista los pedidos del sector del Jefe usando la configuración general de paginado."""
    estado_enum = None
    if estado_str:
        try:
            estado_enum = EstadoPedido(estado_str.lower())
        except ValueError:
            raise PedidoValidationError("El filtro de estado no es válido.")

    if page < 1:
        page = 1

    config = obtener_configuracion()
    per_page = config.elementos_por_pagina

    pedidos_lista, total = repo_pedidos.list_pedidos_by_sector(
        id_sector=id_sector,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        estado=estado_enum,
        id_tipo_comida=id_tipo_comida,
        id_tipo_menu=id_tipo_menu,
        page=page,
        per_page=per_page,
    )

    items = [obtener_detalle_pedido(p.idPedido, id_sector) for p in pedidos_lista]
    return items, total, per_page