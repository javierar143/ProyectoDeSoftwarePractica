from datetime import date
from sqlalchemy import select, func
from src.core.models.Pedido import Pedido
from src.core.models.Solicitud import Solicitud
from src.core.models.enums import EstadoPedido
from src.core.database import db


def create_pedido_con_solicitudes(nuevo_pedido: Pedido, lista_solicitudes: list[Solicitud]) -> Pedido:
    """
    Guarda la cabecera (Pedido) y sus detalles (Solicitudes) en una misma transacción.
    No hace commit, solo prepara la unidad de trabajo.
    """
    db.session.add(nuevo_pedido)
    db.session.flush()

    for solicitud in lista_solicitudes:
        solicitud.idPedido = nuevo_pedido.idPedido
        db.session.add(solicitud)

    return nuevo_pedido


def get_pedido_by_id(id_pedido: int) -> Pedido | None:
    """Recupera un pedido por su clave primaria."""
    return db.session.get(Pedido, id_pedido)


def limpiar_solicitudes_de_pedido(id_pedido: int):
    """
    Borra todos los renglones (solicitudes) actuales de un pedido.
    """
    stmt = db.delete(Solicitud).where(Solicitud.idPedido == id_pedido)
    db.session.execute(stmt)
    db.session.flush()


def guardar_nuevas_solicitudes(pedido: Pedido, nuevas_solicitudes: list[Solicitud]) -> Pedido:
    """Asocia y agrega los nuevos renglones al pedido."""
    for sol in nuevas_solicitudes:
        sol.idPedido = pedido.idPedido
        db.session.add(sol)

    return pedido


def eliminar_pedido(pedido: Pedido):
    """
    Elimina físicamente el pedido y sus solicitudes asociadas.
    La eliminación del detalle (solicitudes) se hace primero para mantener
    la integridad referencial.
    """
    stmt = db.delete(Solicitud).where(Solicitud.idPedido == pedido.idPedido)
    db.session.execute(stmt)

    db.session.delete(pedido)
    db.session.flush()


def get_solicitudes_by_pedido(id_pedido: int) -> list[Solicitud]:
    """Recupera todas las solicitudes nominadas pertenecientes a un pedido."""
    stmt = select(Solicitud).where(Solicitud.idPedido == id_pedido)
    return list(db.session.scalars(stmt).all())


def existe_pedido_en_sector_y_fecha(id_sector: int, fecha_desde: date) -> bool:
    """Verifica si ya existe un pedido no rechazado para ese sector y fecha."""
    stmt = select(Pedido).where(
        Pedido.idSector == id_sector,
        Pedido.fecha_desde == fecha_desde,
        Pedido.estado_general != EstadoPedido.RECHAZADO,
    )
    return db.session.scalar(stmt) is not None


def list_pedidos_by_sector(
    id_sector: int,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    estado: EstadoPedido | None = None,
    id_tipo_comida: int | None = None,
    id_tipo_menu: int | None = None,
    page: int = 1,
    per_page: int = 25,
) -> tuple[list[Pedido], int]:
    """Lista los pedidos de un sector aplicando filtros opcionales y paginación."""
    stmt = select(Pedido).where(Pedido.idSector == id_sector)

    if fecha_desde is not None:
        stmt = stmt.where(Pedido.fecha_desde >= fecha_desde)
    if fecha_hasta is not None:
        stmt = stmt.where(Pedido.fecha_desde <= fecha_hasta)
    if estado is not None:
        stmt = stmt.where(Pedido.estado_general == estado)

    if id_tipo_comida is not None or id_tipo_menu is not None:
        stmt = stmt.join(Solicitud, Solicitud.idPedido == Pedido.idPedido)
        if id_tipo_comida is not None:
            stmt = stmt.where(Solicitud.idTipoComida == id_tipo_comida)
        if id_tipo_menu is not None:
            stmt = stmt.where(Solicitud.idTipoMenu == id_tipo_menu)
        stmt = stmt.distinct()

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.session.scalar(count_stmt) or 0

    stmt = stmt.order_by(Pedido.fecha_desde.desc(), Pedido.idPedido.desc())
    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    items = list(db.session.scalars(stmt).all())
    return items, total