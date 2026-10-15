from datetime import date
from sqlalchemy import select, or_, update
from src.core.database import db
from src.core.models.Pedido import Pedido
from src.core.models.Solicitud import Solicitud
from src.core.models.Entrega import Entrega
from src.core.models.Personal import Personal
from src.core.models.enums import EstadoAutorizacion, EstadoPedido


def get_pedido_by_id(id_pedido: int):
    """Obtiene un pedido por su ID"""

    return db.session.get(Pedido, id_pedido)


def get_solicitudes_by_pedido(id_pedido: int):
    """Obtiene todas las solicitudes nominadas pertenecientes a un pedido"""

    stmt = select(Solicitud).where(Solicitud.idPedido == id_pedido)
    return db.session.scalars(stmt).all()


def listar_pedidos_autorizacion(
    fecha_desde=None,
    fecha_hasta=None,
    id_sector=None,
    id_tipo_comida=None,
    id_tipo_menu=None,
    estado=None,
):
    """Lista los pedidos aplicando filtros para el Servicio de Alimentacion"""

    stmt = select(Pedido).join(Solicitud, Pedido.idPedido == Solicitud.idPedido)

    if fecha_desde:
        stmt = stmt.where(Solicitud.fecha_vianda >= fecha_desde)
    if fecha_hasta:
        stmt = stmt.where(Solicitud.fecha_vianda <= fecha_hasta)
    if id_sector:
        stmt = stmt.where(Pedido.idSector == id_sector)
    if id_tipo_comida:
        stmt = stmt.where(Solicitud.idTipoComida == id_tipo_comida)
    if id_tipo_menu:
        stmt = stmt.where(Solicitud.idTipoMenu == id_tipo_menu)
    if estado:
        stmt = stmt.where(Pedido.estado_general == estado)

    stmt = stmt.distinct().order_by(Pedido.fecha_desde.desc(), Pedido.idPedido.desc())
    return db.session.scalars(stmt).all()


def calcular_totales_pedido(id_pedido: int):
    """Calcula cantidades pedidas y autorizadas por separado sin pisar el pedido original"""

    solicitudes = get_solicitudes_by_pedido(id_pedido)
    cantidad_pedida = len(solicitudes)
    cantidad_autorizada = sum(1 for s in solicitudes if s.estadoAutorizacion == EstadoAutorizacion.AUTORIZADA)

    por_comida_y_menu = {}
    for s in solicitudes:
        clave = f"comida_{s.idTipoComida}_menu_{s.idTipoMenu}"
        if clave not in por_comida_y_menu:
            por_comida_y_menu[clave] = {
                "idTipoComida": s.idTipoComida,
                "idTipoMenu": s.idTipoMenu,
                "cantidad_pedida": 0,
                "cantidad_autorizada": 0,
            }
        por_comida_y_menu[clave]["cantidad_pedida"] += 1
        if s.estadoAutorizacion == EstadoAutorizacion.AUTORIZADA:
            por_comida_y_menu[clave]["cantidad_autorizada"] += 1

    return {
        "cantidad_pedida": cantidad_pedida,
        "cantidad_autorizada": cantidad_autorizada,
        "desglose": list(por_comida_y_menu.values()),
        "solicitudes": solicitudes,
    }


def autorizar_solicitudes_pedido(pedido: Pedido, decisiones: dict, id_evaluador: int):
    """Actualiza de forma nominada las solicitudes de un pedido"""

    for id_sol, nuevo_estado in decisiones.items():
        db.session.execute(
            update(Solicitud)
            .where(
                Solicitud.idSolicitud == id_sol,
                Solicitud.idPedido == pedido.idPedido,
            )
            .values(
                estadoAutorizacion=nuevo_estado,
                idUserEvaluador=id_evaluador,
            )
        )

    db.session.execute(
        update(Pedido)
        .where(Pedido.idPedido == pedido.idPedido)
        .values(estado_general=EstadoPedido.AUTORIZADO)
    )
    db.session.commit()
    db.session.expire_all()
    return get_pedido_by_id(pedido.idPedido)


def rechazar_pedido_completo(pedido: Pedido, id_evaluador: int | None = None):
    """Marca un pedido como RECHAZADO y todas sus solicitudes como NO_AUTORIZADA"""

    valores_solicitud = {"estadoAutorizacion": EstadoAutorizacion.NO_AUTORIZADA}
    if id_evaluador:
        valores_solicitud["idUserEvaluador"] = id_evaluador

    db.session.execute(
        update(Solicitud)
        .where(Solicitud.idPedido == pedido.idPedido)
        .values(**valores_solicitud)
    )

    db.session.execute(
        update(Pedido)
        .where(Pedido.idPedido == pedido.idPedido)
        .values(estado_general=EstadoPedido.RECHAZADO)
    )
    db.session.commit()
    db.session.expire_all()
    return get_pedido_by_id(pedido.idPedido)


def buscar_comidas_autorizadas(fecha=None, dni=None, nya=None, id_sector=None, id_tipo_comida=None, id_personal=None):
    """Consulta comidas en estado AUTORIZADA filtrando por fecha, DNI, nombre/apellido, sector o comida"""

    stmt = (
        select(Solicitud, Pedido, Personal)
        .join(Pedido, Solicitud.idPedido == Pedido.idPedido)
        .join(Personal, Solicitud.idPersonal == Personal.idPersonal)
        .where(
            Pedido.estado_general == EstadoPedido.AUTORIZADO,
            Solicitud.estadoAutorizacion == EstadoAutorizacion.AUTORIZADA,
        )
    )

    if fecha:
        stmt = stmt.where(Solicitud.fecha_vianda == fecha)
    if id_sector:
        stmt = stmt.where(Pedido.idSector == id_sector)
    if id_tipo_comida:
        stmt = stmt.where(Solicitud.idTipoComida == id_tipo_comida)
    if id_personal:
        stmt = stmt.where(Solicitud.idPersonal == id_personal)
    if dni:
        stmt = stmt.where(Personal.dni.ilike(f"%{dni}%"))
    if nya:
        stmt = stmt.where(
            or_(
                Personal.nombre.ilike(f"%{nya}%"),
                Personal.apellido.ilike(f"%{nya}%"),
            )
        )

    filas = db.session.execute(stmt).all()
    resultados = []
    for solicitud, pedido, personal in filas:
        entregada = (
            db.session.scalars(
                select(Entrega).where(Entrega.idSolicitud == solicitud.idSolicitud)
            ).first()
            is not None
        )
        resultados.append({
            "idSolicitud": solicitud.idSolicitud,
            "idPedido": pedido.idPedido,
            "idSector": pedido.idSector,
            "idPersonal": personal.idPersonal,
            "dni": getattr(personal, "dni", None),
            "nombre": getattr(personal, "nombre", None),
            "apellido": getattr(personal, "apellido", None),
            "fecha_vianda": solicitud.fecha_vianda.isoformat(),
            "idTipoComida": solicitud.idTipoComida,
            "idTipoMenu": solicitud.idTipoMenu,
            "condicionCupo": solicitud.condicionCupo.value,
            "entregada": entregada,
        })
    return resultados


def obtener_resumen_autorizaciones(fecha_desde=None, fecha_hasta=None, id_sector=None, id_tipo_comida=None, id_tipo_menu=None):
    """Calcula totales de pedidos vs autorizados con su diferencia."""
    stmt = select(Solicitud).join(Pedido, Solicitud.idPedido == Pedido.idPedido)
    if fecha_desde:
        stmt = stmt.where(Solicitud.fecha_vianda >= fecha_desde)
    if fecha_hasta:
        stmt = stmt.where(Solicitud.fecha_vianda <= fecha_hasta)
    if id_sector:
        stmt = stmt.where(Pedido.idSector == id_sector)
    if id_tipo_comida:
        stmt = stmt.where(Solicitud.idTipoComida == id_tipo_comida)
    if id_tipo_menu:
        stmt = stmt.where(Solicitud.idTipoMenu == id_tipo_menu)

    solicitudes = db.session.scalars(stmt).all()
    total_pedido = len(solicitudes)
    total_autorizado = sum(1 for s in solicitudes if s.estadoAutorizacion == EstadoAutorizacion.AUTORIZADA)

    return {
        "total_pedido": total_pedido,
        "total_autorizado": total_autorizado,
        "diferencia": total_pedido - total_autorizado,
    }


def obtener_resumen_entregas_generales(fecha_desde=None, fecha_hasta=None, id_sector=None, id_tipo_comida=None, id_tipo_menu=None):
    """Calcula totales autorizados vs entregados con su diferencia para resúmenes generales."""
    stmt = select(Solicitud, Pedido).join(Pedido, Solicitud.idPedido == Pedido.idPedido).where(Solicitud.estadoAutorizacion == EstadoAutorizacion.AUTORIZADA)
    if fecha_desde:
        stmt = stmt.where(Solicitud.fecha_vianda >= fecha_desde)
    if fecha_hasta:
        stmt = stmt.where(Solicitud.fecha_vianda <= fecha_hasta)
    if id_sector:
        stmt = stmt.where(Pedido.idSector == id_sector)
    if id_tipo_comida:
        stmt = stmt.where(Solicitud.idTipoComida == id_tipo_comida)
    if id_tipo_menu:
        stmt = stmt.where(Solicitud.idTipoMenu == id_tipo_menu)

    filas = db.session.execute(stmt).all()
    total_autorizado = len(filas)
    total_entregado = 0
    for solicitud, pedido in filas:
        entregada = db.session.scalars(select(Entrega).where(Entrega.idSolicitud == solicitud.idSolicitud)).first() is not None
        if entregada:
            total_entregado += 1

    return {
        "total_autorizado": total_autorizado,
        "total_entregado": total_entregado,
        "diferencia": total_autorizado - total_entregado,
    }