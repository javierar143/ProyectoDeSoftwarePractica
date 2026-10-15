from datetime import datetime
from src.core.database import db
from src.core.models.Solicitud import Solicitud
from src.core.models.Personal import Personal
from src.core.models.enums import EstadoAutorizacion, EstadoPedido
from src.core.repositories.autorizaciones import solicitudes as repo_solicitudes
from src.core.repositories.autorizaciones import entregas as repo_entregas

# <------ Errores ------>

class RecursoNoEncontradoError(Exception):
    """Error 404: El pedido, solicitud o persona no existe."""
    pass


class ConflictoEstadoError(Exception):
    """Error 409: El pedido ya fue autorizado/rechazado o la comida ya fue entregada."""
    pass


# <------ Autorizaciones (Servicio de Alimentacion) ------>

def listar_pedidos_para_autorizacion(filtros: dict):
    """Lista pedidos con cantidades pedidas y autorizadas diferenciadas"""

    estado_enum = None
    if filtros.get("estado"):
        try:
            estado_enum = EstadoPedido[filtros["estado"].upper()]
        except KeyError:
            raise ValueError(f"Estado de pedido inválido: {filtros['estado']}")

    pedidos = repo_solicitudes.listar_pedidos_autorizacion(
        fecha_desde=filtros.get("fecha_desde"),
        fecha_hasta=filtros.get("fecha_hasta"),
        id_sector=filtros.get("sector"),
        id_tipo_comida=filtros.get("tipo_comida"),
        id_tipo_menu=filtros.get("tipo_menu"),
        estado=estado_enum,
    )

    resultado = []
    for p in pedidos:
        # Calculo los toltales individuales para cada pedido de la lista
        totales = repo_solicitudes.calcular_totales_pedido(p.idPedido)
        resultado.append({
            "idPedido": p.idPedido,
            "idSector": p.idSector,
            "fecha_desde": p.fecha_desde.isoformat(),
            "periodicidad": p.periodicidad.value,
            "estado": p.estado_general.value,
            "cantidad_pedida": totales["cantidad_pedida"],
            "cantidad_autorizada": totales["cantidad_autorizada"],
            "desglose": totales["desglose"],
        })
    return resultado


def obtener_detalle_pedido_autorizacion(id_pedido: int):
    """Obtiene el detalle completo de un pedido con cantidades pedidas y autorizadas por separado"""

    # Valido que el pedido exista
    pedido = repo_solicitudes.get_pedido_by_id(id_pedido)
    if not pedido:
        raise RecursoNoEncontradoError("Pedido no encontrado.")

    totales = repo_solicitudes.calcular_totales_pedido(id_pedido)
    return {
        "idPedido": pedido.idPedido,
        "idSector": pedido.idSector,
        "fecha_desde": pedido.fecha_desde.isoformat(),
        "periodicidad": pedido.periodicidad.value,
        "estado": pedido.estado_general.value,
        "cantidad_pedida": totales["cantidad_pedida"],
        "cantidad_autorizada": totales["cantidad_autorizada"],
        "desglose_por_comida_y_menu": totales["desglose"],
        "solicitudes": [
            {
                "idSolicitud": s.idSolicitud,
                "idPersonal": s.idPersonal,
                "idTipoComida": s.idTipoComida,
                "idTipoMenu": s.idTipoMenu,
                "fecha_vianda": s.fecha_vianda.isoformat(),
                "condicionCupo": s.condicionCupo.value,
                "estadoAutorizacion": s.estadoAutorizacion.value,
            }
            for s in totales["solicitudes"]
        ],
    }


def autorizar_pedido(id_pedido: int, items_evaluados: list[dict], id_evaluador: int):
    """Autoriza o no autoriza solicitudes nominadas de un pedido (individual o masivamente)"""

    pedido = repo_solicitudes.get_pedido_by_id(id_pedido)
    if not pedido:
        raise RecursoNoEncontradoError("Pedido no encontrado.")

    # Controlo que el pedido no haya sido procesado antes
    if pedido.estado_general in (EstadoPedido.AUTORIZADO, EstadoPedido.RECHAZADO):
        raise ConflictoEstadoError("El pedido ya fue autorizado o rechazado previamente.")

    if not items_evaluados or not isinstance(items_evaluados, list):
        raise ValueError("Debe enviar el listado de solicitudes a evaluar.")

    solicitudes_pedido = repo_solicitudes.get_solicitudes_by_pedido(id_pedido)
    ids_validos = {s.idSolicitud for s in solicitudes_pedido}

    decisiones = {}
    for item in items_evaluados:
        id_sol = item.get("idSolicitud")
        estado_txt = (item.get("estado") or "").upper()

        # Checkeo que la solicitud sea de ese pedido
        if id_sol not in ids_validos:
            raise ValueError(f"La solicitud {id_sol} no pertenece al pedido {id_pedido}.")

        # Mapeo texto a Enum
        if estado_txt in ("AUTORIZADA", "AUTORIZADO"):
            decisiones[id_sol] = EstadoAutorizacion.AUTORIZADA
        elif estado_txt in ("NO_AUTORIZADA", "NO AUTORIZADA", "RECHAZADA", "RECHAZADO"):
            decisiones[id_sol] = EstadoAutorizacion.NO_AUTORIZADA
        else:
            raise ValueError(f"Estado '{estado_txt}' inválido. Use AUTORIZADA o NO_AUTORIZADA.")

    # Por defecto las solicitudes que no se mencionen se autorizan
    for id_valido in ids_validos:
        if id_valido not in decisiones:
            decisiones[id_valido] = EstadoAutorizacion.AUTORIZADA

    repo_solicitudes.autorizar_solicitudes_pedido(pedido, decisiones, id_evaluador)
    return obtener_detalle_pedido_autorizacion(id_pedido)


def rechazar_pedido(id_pedido: int, id_evaluador: int | None = None):
    """Rechaza un pedido completo si no estaba autorizado"""

    pedido = repo_solicitudes.get_pedido_by_id(id_pedido)
    if not pedido:
        raise RecursoNoEncontradoError("Pedido no encontrado.")

    # Checkeo que el pedido no haya sido rechazado previamente
    if pedido.estado_general in (EstadoPedido.AUTORIZADO, EstadoPedido.RECHAZADO):
        raise ConflictoEstadoError("No se puede rechazar un pedido que ya fue autorizado o rechazado.")

    repo_solicitudes.rechazar_pedido_completo(pedido, id_evaluador)
    return obtener_detalle_pedido_autorizacion(id_pedido)


# <------ Comidas Autorizadas y Entregas (Sector Comedor) ------>

def consultar_comidas_autorizadas(filtros: dict):
    """Consulta comidas autorizadas pidiendo al menos un filtro"""

    # Fuerzo al menos 1 filtro
    if not any(filtros.values()):
        raise ValueError("Debe enviar al menos un filtro de búsqueda (fecha, dni, sector o tipo_comida).")

    return repo_solicitudes.buscar_comidas_autorizadas(
        fecha=filtros.get("fecha"),
        dni=filtros.get("dni"),
        nya=filtros.get("nya"),
        id_sector=filtros.get("sector"),
        id_tipo_comida=filtros.get("tipo_comida"),
    )


def consultar_comidas_autorizadas_persona(id_personal: int, fecha_consulta):
    """Consulta las comidas autorizadas para una persona específica en una fecha"""

    persona = db.session.get(Personal, id_personal)
    if not persona:
        raise RecursoNoEncontradoError("La persona indicada no existe.")

    return repo_solicitudes.buscar_comidas_autorizadas(
        fecha=fecha_consulta, id_personal=id_personal
    )


def registrar_entrega_comedor(id_user: int, ids_solicitudes: list[int], id_personal_retira: int):
    """Registra la entrega de una o varias comidas validando autorizacion vigente, evitando entregas duplicadas"""

    if not ids_solicitudes:
        raise ValueError("Debe indicar al menos una solicitud para entregar.")
    if not id_personal_retira:
        raise ValueError("Debe indicar el id_personal responsable del retiro.")

    # Checkeo que el responsable de retirar la vianda exista
    responsable = db.session.get(Personal, id_personal_retira)
    if not responsable:
        raise ValueError("El responsable del retiro indicado no existe en el padrón de personal.")

    for id_sol in ids_solicitudes:
        solicitud = db.session.get(Solicitud, id_sol)
        if not solicitud:
            raise ValueError(f"La solicitud {id_sol} no existe.")

        # Valido que la solicitud este autorizada
        if solicitud.estadoAutorizacion != EstadoAutorizacion.AUTORIZADA:
            raise ValueError(f"La solicitud {id_sol} no cuenta con autorización vigente.")

        # Evito entregas duplicadas levantando conflicto si ya existe
        if repo_entregas.verificar_entrega_existente(id_sol):
            raise ConflictoEstadoError(f"La comida de la solicitud {id_sol} ya fue entregada anteriormente.")

    return repo_entregas.registrar_entregas_multiples(id_user, ids_solicitudes, id_personal_retira)


# <------ Resumenes ------>

def obtener_resumen_entregas_service(filtros: dict):
    """Obtiene el resumen de entregas autorizadas/entregadas"""

    fecha = filtros.get("fecha")
    id_tipo_comida = filtros.get("tipo_comida")
    id_sector = filtros.get("sector")

    desglose = repo_entregas.obtener_resumen_autorizados_vs_entregados(
        fecha=fecha, id_tipo_comida=id_tipo_comida, id_sector=id_sector
    )

    total_autorizado_gral = sum(item["total_autorizado"] for item in desglose)
    total_entregado_gral = sum(item["total_entregado"] for item in desglose)

    return {
        "fecha": fecha.isoformat() if fecha else None,
        "total_autorizado": total_autorizado_gral,
        "total_entregado": total_entregado_gral,
        "diferencia": total_autorizado_gral - total_entregado_gral,
        "desglose": desglose,
    }


def _forzar_sector_jefe_servicio(filtros: dict):
    """Fuerza el sector si el usuario autenticado es Jefe de Servicio"""

    from flask import session, g
    usuario_sector = None
    if hasattr(g, "current_user") and g.current_user:
        usuario_sector = getattr(g.current_user, "idSector", None)
    elif "id_sector" in session:
        usuario_sector = session["id_sector"]

    # Si es JS, superpongo el sector con el suyo
    if usuario_sector:
        filtros["sector"] = usuario_sector
    return filtros


def resumen_autorizaciones_service(filtros: dict):
    """Obtiene el resumen de autorizaciones (pedidos vs autorizados)"""

    return repo_solicitudes.obtener_resumen_autorizaciones(
        fecha_desde=filtros.get("fecha_desde"),
        fecha_hasta=filtros.get("fecha_hasta"),
        id_sector=filtros.get("sector"),
        id_tipo_comida=filtros.get("tipo_comida"),
        id_tipo_menu=filtros.get("tipo_menu"),
    )


def resumen_entregas_generales_service(filtros: dict):
    """Obtiene el resumen general de entregas (autorizados vs entregados)"""

    return repo_solicitudes.obtener_resumen_entregas_generales(
        fecha_desde=filtros.get("fecha_desde"),
        fecha_hasta=filtros.get("fecha_hasta"),
        id_sector=filtros.get("sector"),
        id_tipo_comida=filtros.get("tipo_comida"),
        id_tipo_menu=filtros.get("tipo_menu"),
    )