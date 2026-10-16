from datetime import datetime, date
from sqlalchemy import select, func
from src.core.database import db
from src.core.models.Entrega import Entrega
from src.core.models.Solicitud import Solicitud
from src.core.models.Pedido import Pedido
from src.core.models.enums import EstadoAutorizacion, EstadoPedido


def verificar_entrega_existente(id_solicitud: int) -> bool:
    """Verifica si una solicitud ya fue entregada para evitar entregas duplicadas"""

    statement = select(Entrega).where(Entrega.idSolicitud == id_solicitud)
    return db.session.scalars(statement).first() is not None


def registrar_entregas_multiples(id_user: int, ids_solicitudes: list[int], id_personal_retira: int):
    """Registra la entrega física de una o varias viandas en una misma operacion"""

    ahora = datetime.now()
    nuevas_entregas = []

    # Recorro cada ID de solicitud y le preparo un registro de entrega
    for id_sol in ids_solicitudes:
        nueva_entrega = Entrega(
            idUser=id_user,
            idSolicitud=id_sol,
            idPersonal=id_personal_retira,
            fecha_hora=ahora,
        )
        db.session.add(nueva_entrega)
        nuevas_entregas.append(nueva_entrega)

    db.session.commit()
    return nuevas_entregas


def get_entrega_by_id(id_entrega: int):
    """Obtiene el detalle de una entrega por su ID"""

    return db.session.get(Entrega, id_entrega)


def listar_entregas(fecha: date | None = None, id_sector: int | None = None, id_tipo_comida: int | None = None):
    """Lista las entregas filtrando por fecha, sector y tipo de comida"""

    stmt = (
        select(Entrega, Solicitud, Pedido)
        .join(Solicitud, Entrega.idSolicitud == Solicitud.idSolicitud)
        .join(Pedido, Solicitud.idPedido == Pedido.idPedido)
    )

    # Junto Entrega Solicitud y Pedido y aplico filtros de busqueda
    if fecha:
        stmt = stmt.where(func.date(Entrega.fecha_hora) == fecha)
    if id_sector:
        stmt = stmt.where(Pedido.idSector == id_sector)
    if id_tipo_comida:
        stmt = stmt.where(Solicitud.idTipoComida == id_tipo_comida)

    stmt = stmt.order_by(Entrega.fecha_hora.desc())
    return db.session.execute(stmt).all()


def obtener_resumen_autorizados_vs_entregados(fecha: date | None = None, id_tipo_comida: int | None = None, id_sector: int | None = None):
    """Calcula totales de autorizados/entregados por tipo de comida y menu"""

    # Agarro todas las autorizadas
    stmt_aut = (
        select(Solicitud, Pedido)
        .join(Pedido, Solicitud.idPedido == Pedido.idPedido)
        .where(
            Pedido.estado_general == EstadoPedido.AUTORIZADO,
            Solicitud.estadoAutorizacion == EstadoAutorizacion.AUTORIZADA,
        )
    )

    if fecha:
        stmt_aut = stmt_aut.where(Solicitud.fecha_vianda == fecha)
    if id_sector:
        stmt_aut = stmt_aut.where(Pedido.idSector == id_sector)
    if id_tipo_comida:
        stmt_aut = stmt_aut.where(Solicitud.idTipoComida == id_tipo_comida)

    filas_aut = db.session.execute(stmt_aut).all()

    resumen = {}
    for solicitud, pedido in filas_aut:
        # Checkeo si esta solicitud especifica ya cuenta con entrega registrada
        entregada = db.session.scalars(
            select(Entrega).where(Entrega.idSolicitud == solicitud.idSolicitud)
        ).first() is not None

        # Agrupo por tipo de comida y menu
        clave = (solicitud.idTipoComida, solicitud.idTipoMenu)
        if clave not in resumen:
            resumen[clave] = {
                "idTipoComida": solicitud.idTipoComida,
                "idTipoMenu": solicitud.idTipoMenu,
                "total_autorizado": 0,
                "total_entregado": 0,
            }

        resumen[clave]["total_autorizado"] += 1
        if entregada:
            resumen[clave]["total_entregado"] += 1

    return list(resumen.values())