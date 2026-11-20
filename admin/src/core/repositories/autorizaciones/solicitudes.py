from datetime import datetime, date
from sqlalchemy import select, or_, update
from src.core.database import db
from src.core.models.Pedido import Pedido
from src.core.models.Solicitud import Solicitud
from src.core.models.Entrega import Entrega
from src.core.models.Personal import Personal
from src.core.models.Sector import Sector
from src.core.models.TipoComida import TipoComida
from src.core.models.TipoMenu import TipoMenu
from src.core.models.enums import EstadoAutorizacion, EstadoPedido, CondicionCupo


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

    # Aplico filtros de forma dinamica
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

    # Agrupor por comida/menu
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


def autorizar_solicitudes_pedido(pedido, decisiones: dict, id_evaluador: int):
    """Actualiza de forma nominada las solicitudes de un pedido"""  

    ahora = datetime.now()
    for id_sol, nuevo_estado in decisiones.items():
        valores_sol = {
            "estadoAutorizacion": nuevo_estado,
            "idUserEvaluador": id_evaluador,
        }
        if hasattr(Solicitud, "fecha_evaluacion"):
            valores_sol["fecha_evaluacion"] = ahora

        db.session.execute(
            update(Solicitud)
            .where(Solicitud.idSolicitud == id_sol)
            .values(**valores_sol)
        )

    valores_ped = {"estado_general": EstadoPedido.AUTORIZADO}
    if hasattr(Pedido, "updated_at"):
        valores_ped["updated_at"] = ahora

    db.session.execute(
        update(Pedido)
        .where(Pedido.idPedido == pedido.idPedido)
        .values(**valores_ped)
    )
    db.session.commit()
    db.session.expire_all()
    return get_pedido_by_id(pedido.idPedido)


def rechazar_pedido_completo(pedido, id_evaluador: int | None = None, motivo: str = ""):
    """Marca un pedido como RECHAZADO y todas sus solicitudes como NO_AUTORIZADA"""

    ahora = datetime.now()
    vals_sol = {"estadoAutorizacion": EstadoAutorizacion.NO_AUTORIZADA}
    if id_evaluador:
        vals_sol["idUserEvaluador"] = id_evaluador

    db.session.execute(
        update(Solicitud)
        .where(Solicitud.idPedido == pedido.idPedido)
        .values(**vals_sol)
    )

    vals_ped = {"estado_general": EstadoPedido.RECHAZADO}
    if hasattr(Pedido, "motivo_rechazo"):
        vals_ped["motivo_rechazo"] = motivo
    if hasattr(Pedido, "updated_at"):
        vals_ped["updated_at"] = ahora

    db.session.execute(
        update(Pedido)
        .where(Pedido.idPedido == pedido.idPedido)
        .values(**vals_ped)
    )
    db.session.commit()
    db.session.expire_all()
    return get_pedido_by_id(pedido.idPedido)


def obtener_mapa_nombres_sectores() -> dict[int, str]:
    """Devuelve un diccionario {idSector: nombre} para resolver nombres sin depender de otra API."""
    filas = db.session.scalars(select(Sector)).all()
    return {s.idSector: s.nombre for s in filas}


def buscar_comidas_autorizadas(
    fecha=None,
    fecha_desde=None,
    fecha_hasta=None,
    dni=None,
    nya=None,
    id_sector=None,
    id_tipo_comida=None,
    id_tipo_menu=None,
    condicion=None,
    id_personal=None,
):
    """Consulta comidas en estado AUTORIZADA filtrando por fecha/rango, DNI, nombre/apellido, sector, comida o menú."""

    stmt = (
        select(Solicitud, Pedido, Personal, Sector, TipoComida, TipoMenu)
        .join(Pedido, Solicitud.idPedido == Pedido.idPedido)
        .join(Personal, Solicitud.idPersonal == Personal.idPersonal)
        .join(Sector, Pedido.idSector == Sector.idSector)
        .join(TipoComida, Solicitud.idTipoComida == TipoComida.idTipoComida)
        .join(TipoMenu, Solicitud.idTipoMenu == TipoMenu.idTipoMenu)
        .where(
            Pedido.activo.is_(True),
            Solicitud.activo.is_(True),
            Pedido.estado_general == EstadoPedido.AUTORIZADO,
            Solicitud.estadoAutorizacion == EstadoAutorizacion.AUTORIZADA,
        )
    )

    if fecha:
        stmt = stmt.where(Solicitud.fecha_vianda == fecha)
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
    if condicion and condicion != "todas":
        try:
            cond_enum = CondicionCupo[condicion.upper()]
            stmt = stmt.where(Solicitud.condicionCupo == cond_enum)
        except KeyError:
            stmt = stmt.where(Solicitud.condicionCupo == condicion.lower())
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

    stmt = stmt.order_by(
        Personal.apellido.asc(),
        Personal.nombre.asc(),
        Solicitud.fecha_vianda.asc(),
    )

    filas = db.session.execute(stmt).all()
    resultados = []
    for solicitud, pedido, personal, sector, comida, menu in filas:
        entrega_obj = db.session.scalars(
            select(Entrega).where(Entrega.idSolicitud == solicitud.idSolicitud)
        ).first()
        entregada = entrega_obj is not None
        hora_entrega = (
            entrega_obj.fecha_hora.strftime("%H:%M")
            if entrega_obj and getattr(entrega_obj, "fecha_hora", None)
            else None
        )
        cond_val = (
            solicitud.condicionCupo.value
            if hasattr(solicitud.condicionCupo, "value")
            else str(solicitud.condicionCupo)
        )
        resultados.append({
            "idSolicitud": solicitud.idSolicitud,
            "idPedido": pedido.idPedido,
            "idSector": pedido.idSector,
            "sector": sector.nombre,
            "idPersonal": personal.idPersonal,
            "dni": getattr(personal, "dni", None),
            "nombre": getattr(personal, "nombre", None),
            "apellido": getattr(personal, "apellido", None),
            "fecha_vianda": solicitud.fecha_vianda.isoformat(),
            "idTipoComida": solicitud.idTipoComida,
            "comida": comida.nombre,
            "idTipoMenu": solicitud.idTipoMenu,
            "menu": menu.nombre,
            "condicionCupo": cond_val,
            "entregada": entregada,
            "hora_entrega": hora_entrega,
        })
    return resultados

def _clave_agrupacion(
    fecha_vianda,
    id_sector,
    nombre_sector,
    id_comida,
    nombre_comida,
    id_menu,
    nombre_menu,
    condicion_str,
    agrupamiento: str | None,
):
    """Devuelve el par (clave, etiqueta) según el criterio de agrupamiento solicitado."""
    if not agrupamiento:
        return None
    if agrupamiento in ("dia", "día"):
        clave = fecha_vianda.isoformat()
        return (clave, clave)
    if agrupamiento == "semana":
        iso_year, iso_week, _ = fecha_vianda.isocalendar()
        clave = f"{iso_year}-W{iso_week:02d}"
        return (clave, clave)
    if agrupamiento == "mes":
        clave = fecha_vianda.strftime("%Y-%m")
        return (clave, clave)
    if agrupamiento == "sector":
        return (f"sector_{id_sector}", nombre_sector or f"Sector #{id_sector}")
    if agrupamiento == "comida":
        return (f"comida_{id_comida}", nombre_comida or f"Comida #{id_comida}")
    if agrupamiento == "tipo_menu":
        return (f"menu_{id_menu}", nombre_menu or f"Menú #{id_menu}")
    if agrupamiento == "condicion":
        return (condicion_str.lower(), condicion_str.capitalize())
    return None


def obtener_resumen_autorizaciones(
    fecha_desde=None,
    fecha_hasta=None,
    id_sector=None,
    id_tipo_comida=None,
    id_tipo_menu=None,
    condicion=None,
    estado=None,
    agrupamiento=None,
):
    """Calcula totales pedidos vs autorizados (general, desglose y agrupación opcional)."""

    stmt = (
        select(Solicitud, Pedido, Sector, TipoComida, TipoMenu)
        .join(Pedido, Solicitud.idPedido == Pedido.idPedido)
        .join(Sector, Pedido.idSector == Sector.idSector)
        .join(TipoComida, Solicitud.idTipoComida == TipoComida.idTipoComida)
        .join(TipoMenu, Solicitud.idTipoMenu == TipoMenu.idTipoMenu)
        .where(Solicitud.activo.is_(True), Pedido.activo.is_(True))
    )
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
    if condicion and condicion != "todas":
        try:
            cond_enum = CondicionCupo[condicion.upper()]
            stmt = stmt.where(Solicitud.condicionCupo == cond_enum)
        except KeyError:
            stmt = stmt.where(Solicitud.condicionCupo == condicion.lower())

    filas = db.session.execute(stmt).all()
    total_pedido = len(filas)
    total_autorizado = 0
    regulares_ped = 0
    excepciones_ped = 0
    residentes_ped = 0

    desglose_map = {}
    agrup_map = {}

    for s, p, sec, com, menu in filas:
        es_aut = s.estadoAutorizacion == EstadoAutorizacion.AUTORIZADA
        if es_aut:
            total_autorizado += 1

        val_cond = (
            s.condicionCupo.value
            if hasattr(s.condicionCupo, "value")
            else str(s.condicionCupo)
        )
        es_sector_residentes = (sec.nombre or "").strip().lower() == "residentes"

        if es_sector_residentes:
            residentes_ped += 1
        elif val_cond.lower() == "excepcion":
            excepciones_ped += 1
        else:
            regulares_ped += 1

        clave = (
            sec.idSector,
            sec.nombre,
            com.idTipoComida,
            com.nombre,
            menu.idTipoMenu,
            menu.nombre,
        )
        if clave not in desglose_map:
            desglose_map[clave] = {
                "idSector": sec.idSector,
                "sector": sec.nombre,
                "idTipoComida": com.idTipoComida,
                "comida": com.nombre,
                "idTipoMenu": menu.idTipoMenu,
                "tipo_menu": menu.nombre,
                "cantidad_pedida": 0,
                "cantidad_pedida_regulares": 0,
                "cantidad_pedida_excepciones": 0,
                "cantidad_autorizada": 0,
                "diferencia": 0,
            }

        item = desglose_map[clave]
        item["cantidad_pedida"] += 1
        if val_cond.lower() == "excepcion":
            item["cantidad_pedida_excepciones"] += 1
        else:
            item["cantidad_pedida_regulares"] += 1
        if es_aut:
            item["cantidad_autorizada"] += 1
        item["diferencia"] = item["cantidad_pedida"] - item["cantidad_autorizada"]

        par_agrup = _clave_agrupacion(
            s.fecha_vianda,
            sec.idSector,
            sec.nombre,
            com.idTipoComida,
            com.nombre,
            menu.idTipoMenu,
            menu.nombre,
            val_cond,
            agrupamiento,
        )
        if par_agrup is not None:
            clave_grp, etiqueta_grp = par_agrup
            if clave_grp not in agrup_map:
                agrup_map[clave_grp] = {
                    "clave": clave_grp,
                    "etiqueta": etiqueta_grp,
                    "total_pedido": 0,
                    "total_autorizado": 0,
                    "diferencia": 0,
                }
            grp = agrup_map[clave_grp]
            grp["total_pedido"] += 1
            if es_aut:
                grp["total_autorizado"] += 1
            grp["diferencia"] = grp["total_pedido"] - grp["total_autorizado"]

    desglose_ordenado = [
        desglose_map[k]
        for k in sorted(
            desglose_map.keys(),
            key=lambda x: (x[1], x[3], x[5]),
        )
    ]

    agrupaciones_ordenadas = [
        agrup_map[k] for k in sorted(agrup_map.keys())
    ]

    return {
        "total_pedido": total_pedido,
        "total_pedido_regulares": regulares_ped,
        "total_pedido_excepciones": excepciones_ped,
        "total_pedido_residentes": residentes_ped,
        "total_autorizado": total_autorizado,
        "diferencia": total_pedido - total_autorizado,
        "desglose": desglose_ordenado,
        "agrupaciones": agrupaciones_ordenadas,
    }


def obtener_resumen_entregas_generales(
    fecha_desde=None,
    fecha_hasta=None,
    id_sector=None,
    id_tipo_comida=None,
    id_tipo_menu=None,
    condicion=None,
    agrupamiento=None,
):
    """Calcula totales autorizados vs entregados con desglose y agrupación opcional."""

    stmt = (
        select(Solicitud, Pedido, Sector, TipoComida, TipoMenu)
        .join(Pedido, Solicitud.idPedido == Pedido.idPedido)
        .join(Sector, Pedido.idSector == Sector.idSector)
        .join(TipoComida, Solicitud.idTipoComida == TipoComida.idTipoComida)
        .join(TipoMenu, Solicitud.idTipoMenu == TipoMenu.idTipoMenu)
        .where(
            Solicitud.estadoAutorizacion == EstadoAutorizacion.AUTORIZADA,
            Solicitud.activo.is_(True),
            Pedido.activo.is_(True),
        )
    )
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
    if condicion and condicion != "todas":
        try:
            cond_enum = CondicionCupo[condicion.upper()]
            stmt = stmt.where(Solicitud.condicionCupo == cond_enum)
        except KeyError:
            stmt = stmt.where(Solicitud.condicionCupo == condicion.lower())

    filas = db.session.execute(stmt).all()
    ids_solicitudes = [s.idSolicitud for s, _, _, _, _ in filas]

    ids_entregados = set()
    if ids_solicitudes:
        stmt_entregas = select(Entrega.idSolicitud).where(
            Entrega.idSolicitud.in_(ids_solicitudes)
        )
        ids_entregados = set(db.session.execute(stmt_entregas).scalars().all())

    total_autorizado = len(filas)
    total_entregado = 0
    desglose_map = {}
    agrup_map = {}

    for s, p, sec, com, menu in filas:
        es_entregada = s.idSolicitud in ids_entregados
        if es_entregada:
            total_entregado += 1

        val_cond = (
            s.condicionCupo.value
            if hasattr(s.condicionCupo, "value")
            else str(s.condicionCupo)
        )

        clave = (
            sec.idSector,
            sec.nombre,
            com.idTipoComida,
            com.nombre,
            menu.idTipoMenu,
            menu.nombre,
        )
        if clave not in desglose_map:
            desglose_map[clave] = {
                "idSector": sec.idSector,
                "sector": sec.nombre,
                "idTipoComida": com.idTipoComida,
                "comida": com.nombre,
                "idTipoMenu": menu.idTipoMenu,
                "tipo_menu": menu.nombre,
                "total_autorizado": 0,
                "total_entregado": 0,
                "diferencia": 0,
            }

        item = desglose_map[clave]
        item["total_autorizado"] += 1
        if es_entregada:
            item["total_entregado"] += 1
        item["diferencia"] = item["total_autorizado"] - item["total_entregado"]

        par_agrup = _clave_agrupacion(
            s.fecha_vianda,
            sec.idSector,
            sec.nombre,
            com.idTipoComida,
            com.nombre,
            menu.idTipoMenu,
            menu.nombre,
            val_cond,
            agrupamiento,
        )
        if par_agrup is not None:
            clave_grp, etiqueta_grp = par_agrup
            if clave_grp not in agrup_map:
                agrup_map[clave_grp] = {
                    "clave": clave_grp,
                    "etiqueta": etiqueta_grp,
                    "total_autorizado": 0,
                    "total_entregado": 0,
                    "diferencia": 0,
                }
            grp = agrup_map[clave_grp]
            grp["total_autorizado"] += 1
            if es_entregada:
                grp["total_entregado"] += 1
            grp["diferencia"] = grp["total_autorizado"] - grp["total_entregado"]

    desglose_ordenado = [
        desglose_map[k]
        for k in sorted(
            desglose_map.keys(),
            key=lambda x: (x[1], x[3], x[5]),
        )
    ]

    agrupaciones_ordenadas = [
        agrup_map[k] for k in sorted(agrup_map.keys())
    ]

    return {
        "total_autorizado": total_autorizado,
        "total_entregado": total_entregado,
        "diferencia": total_autorizado - total_entregado,
        "desglose": desglose_ordenado,
        "agrupaciones": agrupaciones_ordenadas,
    }
    
def listar_fechas_autorizacion(
    fecha_desde=None,
    fecha_hasta=None,
    id_sector=None,
    id_tipo_comida=None,
    id_tipo_menu=None,
    estado=None,
):
    """Devuelve las fechas distintas que tienen pedidos/solicitudes segun los filtros"""

    stmt = (
        select(Solicitud.fecha_vianda)
        .join(Pedido, Solicitud.idPedido == Pedido.idPedido)
        .where(Solicitud.activo.is_(True), Pedido.activo.is_(True))
    )

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

    stmt = stmt.distinct().order_by(Solicitud.fecha_vianda.asc())
    fechas = db.session.scalars(stmt).all()
    return [f.isoformat() for f in fechas if f is not None]