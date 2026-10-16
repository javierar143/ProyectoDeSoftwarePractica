"""Repositorio para las consultas y persistencia en BD de Pedidos y Solicitudes."""

from datetime import date, datetime

from sqlalchemy import func, select, update

from src.core.database import db
from src.core.models.Pedido import Pedido
from src.core.models.Solicitud import Solicitud
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.enums import EstadoPedido


def create_pedido_con_solicitudes(
    nuevo_pedido: Pedido, lista_solicitudes: list[Solicitud]
) -> Pedido:
    """
    Guarda la cabecera (Pedido) y sus detalles (Solicitudes) en una misma transacción.
    """
    db.session.add(nuevo_pedido)
    db.session.flush()

    for solicitud in lista_solicitudes:
        solicitud.idPedido = nuevo_pedido.idPedido
        db.session.add(solicitud)

    db.session.commit()
    return nuevo_pedido


def get_pedido_by_id(id_pedido: int) -> Pedido | None:
    """Recupera un pedido activo por su clave primaria."""
    pedido = db.session.get(Pedido, id_pedido)
    if pedido is not None and pedido.activo:
        return pedido
    return None


def limpiar_solicitudes_de_pedido(id_pedido: int) -> None:
    """
    Realiza la baja lógica de los renglones (solicitudes) vigentes de un pedido
    antes de cargar los nuevos renglones en una modificación.
    """
    ahora = datetime.now()
    stmt = (
        update(Solicitud)
        .where(
            Solicitud.idPedido == id_pedido,
            Solicitud.activo.is_(True),
        )
        .values(activo=False, deleted_at=ahora, updated_at=ahora)
    )
    db.session.execute(stmt)
    db.session.flush()


def guardar_nuevas_solicitudes(
    pedido: Pedido, nuevas_solicitudes: list[Solicitud]
) -> Pedido:
    """Asocia y agrega los nuevos renglones activos al pedido."""
    pedido.updated_at = datetime.now()
    db.session.add(pedido)

    for sol in nuevas_solicitudes:
        sol.idPedido = pedido.idPedido
        sol.activo = True
        db.session.add(sol)

    db.session.commit()
    return pedido


def eliminar_pedido(pedido: Pedido) -> Pedido:
    """
    Realiza la baja lógica del pedido confirmado y de todas sus solicitudes asociadas,
    conservando el registro histórico en la base de datos.
    """
    ahora = datetime.now()

    stmt_solicitudes = (
        update(Solicitud)
        .where(
            Solicitud.idPedido == pedido.idPedido,
            Solicitud.activo.is_(True),
        )
        .values(activo=False, deleted_at=ahora, updated_at=ahora)
    )
    db.session.execute(stmt_solicitudes)

    pedido.activo = False
    pedido.deleted_at = ahora
    pedido.updated_at = ahora
    db.session.add(pedido)
    db.session.commit()
    return pedido


def get_solicitudes_by_pedido(id_pedido: int) -> list[Solicitud]:
    """Recupera todas las solicitudes nominadas vigentes pertenecientes a un pedido."""
    stmt = select(Solicitud).where(
        Solicitud.idPedido == id_pedido,
        Solicitud.activo.is_(True),
    )
    return list(db.session.scalars(stmt).all())


def existe_pedido_en_sector_y_fecha(
    id_sector: int, fecha_desde: date
) -> bool:
    """Verifica si ya existe un pedido activo y no rechazado para ese sector y fecha."""
    stmt = select(Pedido).where(
        Pedido.idSector == id_sector,
        Pedido.fecha_desde == fecha_desde,
        Pedido.activo.is_(True),
        Pedido.estado_general != EstadoPedido.RECHAZADO,
    )
    return db.session.scalar(stmt) is not None


def existe_solicitud_duplicada(
    id_personal: int,
    id_sector: int,
    fecha: date,
    id_tipo_comida: int,
    excluir_id_pedido: int | None = None,
) -> bool:
    """
    Verifica si la persona ya tiene esa comida solicitada activa en ese sector y fecha
    dentro de un pedido activo no rechazado.
    """
    stmt = (
        select(Solicitud)
        .join(Pedido, Solicitud.idPedido == Pedido.idPedido)
        .where(
            Solicitud.idPersonal == id_personal,
            Solicitud.fecha_vianda == fecha,
            Solicitud.idTipoComida == id_tipo_comida,
            Solicitud.activo.is_(True),
            Pedido.idSector == id_sector,
            Pedido.activo.is_(True),
            Pedido.estado_general != EstadoPedido.RECHAZADO,
        )
    )
    if excluir_id_pedido is not None:
        stmt = stmt.where(Pedido.idPedido != excluir_id_pedido)

    return db.session.scalar(stmt) is not None


def get_tipo_personal_by_id(id_tipo_personal: int) -> TipoPersonal | None:
    """Recupera un tipo de personal por su ID desde la base de datos."""
    return db.session.get(TipoPersonal, id_tipo_personal)

def list_pedidos_by_sector(
    page: int,
    per_page: int,
    id_sector: int | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    estado: EstadoPedido | None = None,
    id_tipo_comida: int | None = None,
    id_tipo_menu: int | None = None,
) -> tuple[list[Pedido], int]:
    """
    Lista los pedidos vigentes filtrando por sector y criterios opcionales,
    paginando con el per_page global enviado por el servicio.
    """
    stmt = select(Pedido).where(Pedido.activo.is_(True))

    if id_sector is not None:
        stmt = stmt.where(Pedido.idSector == id_sector)

    if fecha_desde is not None:
        stmt = stmt.where(Pedido.fecha_desde >= fecha_desde)
    if fecha_hasta is not None:
        stmt = stmt.where(Pedido.fecha_desde <= fecha_hasta)
    if estado is not None:
        stmt = stmt.where(Pedido.estado_general == estado)

    if id_tipo_comida is not None or id_tipo_menu is not None:
        stmt = stmt.join(
            Solicitud,
            (Solicitud.idPedido == Pedido.idPedido)
            & (Solicitud.activo.is_(True)),
        )
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


def obtener_solicitudes_para_resumen(
    id_sector: int | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    id_tipo_comida: int | None = None,
    id_tipo_menu: int | None = None,
) -> list[tuple[Solicitud, int]]:
    """
    Recupera las solicitudes vigentes junto con el idSector de su pedido
    para construir el resumen estadístico de comidas pedidas.
    """
    stmt = (
        select(Solicitud, Pedido.idSector)
        .join(Pedido, Solicitud.idPedido == Pedido.idPedido)
        .where(
            Pedido.activo.is_(True),
            Solicitud.activo.is_(True),
        )
    )

    if id_sector is not None:
        stmt = stmt.where(Pedido.idSector == id_sector)
    if fecha_desde is not None:
        stmt = stmt.where(Solicitud.fecha_vianda >= fecha_desde)
    if fecha_hasta is not None:
        stmt = stmt.where(Solicitud.fecha_vianda <= fecha_hasta)
    if id_tipo_comida is not None:
        stmt = stmt.where(Solicitud.idTipoComida == id_tipo_comida)
    if id_tipo_menu is not None:
        stmt = stmt.where(Solicitud.idTipoMenu == id_tipo_menu)

    return list(db.session.execute(stmt).all())