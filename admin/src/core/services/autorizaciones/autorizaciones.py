from datetime import datetime, date
from src.core.database import db
from src.core.models.Solicitud import Solicitud
from src.core.models.Personal import Personal
from src.core.models.enums import EstadoAutorizacion, EstadoPedido
from src.core.repositories.autorizaciones import solicitudes as repo_solicitudes
from src.core.repositories.autorizaciones import entregas as repo_entregas
from src.web.validators.autorizaciones import autorizaciones_validator as validador
import csv
import io

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

    filtros = validador.validar_filtros_autorizaciones(filtros)
    mapa_sectores = repo_solicitudes.obtener_mapa_nombres_sectores()

    pedidos = repo_solicitudes.listar_pedidos_autorizacion(
        fecha_desde=filtros.get("fecha_desde"),
        fecha_hasta=filtros.get("fecha_hasta"),
        id_sector=filtros.get("sector"),
        id_tipo_comida=filtros.get("tipo_comida"),
        id_tipo_menu=filtros.get("tipo_menu"),
        estado=filtros.get("estado_enum"),
    )

    condicion_filtro = (filtros.get("condicion") or "").strip().lower()
    resultado = []
    for p in pedidos:
        totales = repo_solicitudes.calcular_totales_pedido(p.idPedido)
        if condicion_filtro in ("regular", "excepcion"):
            tiene_condicion = any(
                (
                    s.condicionCupo.value
                    if hasattr(s.condicionCupo, "value")
                    else str(s.condicionCupo)
                ).lower()
                == condicion_filtro
                for s in totales["solicitudes"]
            )
            if not tiene_condicion:
                continue

        resultado.append({
            "idPedido": p.idPedido,
            "idSector": p.idSector,
            "nombreSector": mapa_sectores.get(p.idSector, f"Sector #{p.idSector}"),
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
    ultima_mod = getattr(pedido, "updated_at", None) or getattr(pedido, "fecha_modificacion", None)

    return {
        "idPedido": pedido.idPedido,
        "idSector": pedido.idSector,
        "fecha_desde": pedido.fecha_desde.isoformat(),
        "periodicidad": pedido.periodicidad.value,
        "estado": pedido.estado_general.value,
        "motivo_rechazo": getattr(pedido, "motivo_rechazo", None),
        "ultima_modificacion": ultima_mod.isoformat() if ultima_mod else None,
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


def autorizar_pedido(
    id_pedido: int,
    items_evaluados: list[dict],
    id_evaluador: int,
    ultima_modificacion: str | None = None,
):
    """Autoriza o no autoriza solicitudes nominadas de un pedido (individual o masivamente)"""

    # Valido estructura del listado de solicitudes con el validator
    validador.validar_items_autorizacion(items_evaluados)

    pedido = repo_solicitudes.get_pedido_by_id(id_pedido)
    if not pedido:
        raise RecursoNoEncontradoError("Pedido no encontrado.")

    # Checkeo que un pedido rechazado no puede autorizarse
    if pedido.estado_general == EstadoPedido.RECHAZADO:
        raise ConflictoEstadoError("El pedido ya fue rechazado previamente y no puede autorizarse.")

    # Checkeo que los pedidos de dias anteriores no pueden autorizarse ni corregirse
    if pedido.fecha_desde < date.today():
        raise ConflictoEstadoError("No se pueden autorizar ni corregir pedidos de días anteriores.")

    # Si ya estaba AUTORIZADO, se puede corregir solo si ninguna comida fue entregada
    if pedido.estado_general == EstadoPedido.AUTORIZADO:
        if repo_entregas.pedido_tiene_entregas(id_pedido):
            raise ConflictoEstadoError(
                "No se puede corregir la autorización porque una o más comidas del pedido ya fueron entregadas."
            )

    # Control de cambios simultaneos sobre el pedido
    ultima_mod_actual = getattr(pedido, "updated_at", None) or getattr(pedido, "fecha_modificacion", None)
    if ultima_modificacion and ultima_mod_actual:
        if ultima_mod_actual.isoformat() != ultima_modificacion:
            raise ConflictoEstadoError(
                "El pedido fue modificado mientras se revisaba. Recargue los datos para ver la versión actual."
            )

    solicitudes_pedido = repo_solicitudes.get_solicitudes_by_pedido(id_pedido)
    ids_validos = {s.idSolicitud for s in solicitudes_pedido}

    # Checkeo que la solicitud sea de ese pedido y mapeo texto a Enum en el validator
    decisiones = validador.validar_items_autorizacion(items_evaluados, ids_validos, id_pedido)

    # Por defecto las solicitudes que no se mencionen se autorizan
    for id_valido in ids_validos:
        if id_valido not in decisiones:
            decisiones[id_valido] = EstadoAutorizacion.AUTORIZADA

    repo_solicitudes.autorizar_solicitudes_pedido(pedido, decisiones, id_evaluador)
    return obtener_detalle_pedido_autorizacion(id_pedido)


def rechazar_pedido(id_pedido: int, id_evaluador: int | None = None, motivo: str | None = None):
    """Rechaza un pedido completo si no estaba autorizado, exigiendo motivo obligatorio"""

    # Nuevo -> Valido que el motivo de rechazo sea obligatorio
    motivo_limpio = validador.validar_motivo_rechazo(motivo)

    pedido = repo_solicitudes.get_pedido_by_id(id_pedido)
    if not pedido:
        raise RecursoNoEncontradoError("Pedido no encontrado.")

    # Nuevo -> No pueden rechazarse pedidos de dias anteriores
    if pedido.fecha_desde < date.today():
        raise ConflictoEstadoError("No se pueden rechazar pedidos de días anteriores.")

    # Checkeo que el pedido no haya sido autorizado o rechazado previamente
    if pedido.estado_general in (EstadoPedido.AUTORIZADO, EstadoPedido.RECHAZADO):
        raise ConflictoEstadoError("No se puede rechazar un pedido que ya fue autorizado o rechazado.")

    repo_solicitudes.rechazar_pedido_completo(pedido, id_evaluador, motivo_limpio)
    return obtener_detalle_pedido_autorizacion(id_pedido)


# <------ Comidas Autorizadas y Entregas (Sector Comedor) ------>


def _validar_formato_y_rango_csv(filtros_raw: dict) -> tuple[date, date]:
    """Valida que formato sea 'csv' y que fecha_desde y fecha_hasta estén presentes y sean válidas"""

    formato = filtros_raw.get("formato")
    if formato is not None and formato != "csv":
        raise ValueError("El parámetro 'formato' solo admite el valor 'csv'.")

    f_desde_str = filtros_raw.get("fecha_desde") or filtros_raw.get("fecha")
    f_hasta_str = filtros_raw.get("fecha_hasta") or filtros_raw.get("fecha")
    if not f_desde_str or not f_hasta_str:
        raise ValueError("El rango de fechas (fecha_desde y fecha_hasta) es obligatorio para exportar a CSV.")

    f_desde = validador.validar_fecha_opcional(f_desde_str)
    f_hasta = validador.validar_fecha_opcional(f_hasta_str)
    if not f_desde or not f_hasta:
        raise ValueError("El rango de fechas ingresado no es válido.")
    if f_desde > f_hasta:
        raise ValueError("La fecha 'fecha_desde' no puede ser posterior a 'fecha_hasta'.")

    return f_desde, f_hasta


def consultar_comidas_autorizadas(filtros: dict):
    """Consulta comidas autorizadas (JSON) o genera el archivo CSV de personas autorizadas"""

    formato = filtros.get("formato")
    if formato is not None and formato != "csv":
        raise ValueError("El parámetro 'formato' solo admite el valor 'csv'.")

    if formato == "csv":
        f_desde, f_hasta = _validar_formato_y_rango_csv(filtros)
        filas = repo_solicitudes.buscar_comidas_autorizadas(
            fecha_desde=f_desde,
            fecha_hasta=f_hasta,
            dni=filtros.get("dni"),
            nya=filtros.get("nya"),
            id_sector=filtros.get("sector"),
            id_tipo_comida=filtros.get("tipo_comida"),
            id_tipo_menu=filtros.get("tipo_menu"),
            condicion=filtros.get("condicion"),
        )
        return generar_csv_personas_autorizadas(filas)

    filtros_validados = validador.validar_filtros_comidas_autorizadas(filtros)
    return repo_solicitudes.buscar_comidas_autorizadas(
        fecha=filtros_validados.get("fecha"),
        dni=filtros_validados.get("dni"),
        nya=filtros_validados.get("nya"),
        id_sector=filtros_validados.get("sector"),
        id_tipo_comida=filtros_validados.get("tipo_comida"),
    )


def generar_csv_personas_autorizadas(filas: list[dict]) -> str:
    """Genera el CSV con una fila por persona: apellido y nombre, DNI, sector, desayuno, almuerzo, merienda, cena y tipo de menú."""
    agrupado = {}
    for item in filas:
        clave = (
            item.get("idPersonal"),
            item.get("fecha_vianda"),
            item.get("idSector"),
        )
        if clave not in agrupado:
            apellido = (item.get("apellido") or "").strip()
            nombre = (item.get("nombre") or "").strip()
            nya_texto = f"{apellido}, {nombre}".strip(", ")
            agrupado[clave] = {
                "apellido y nombre": nya_texto,
                "DNI": item.get("dni") or "",
                "sector": item.get("sector") or f"Sector #{item.get('idSector')}",
                "desayuno": "No",
                "almuerzo": "No",
                "merienda": "No",
                "cena": "No",
                "tipo de menú": (item.get("menu") or "").lower(),
            }

        id_comida = item.get("idTipoComida")
        nombre_comida = (item.get("comida") or "").strip().lower()
        if id_comida == 1 or "desayuno" in nombre_comida:
            agrupado[clave]["desayuno"] = "Sí"
        elif id_comida == 2 or "almuerzo" in nombre_comida:
            agrupado[clave]["almuerzo"] = "Sí"
        elif id_comida == 3 or "merienda" in nombre_comida:
            agrupado[clave]["merienda"] = "Sí"
        elif id_comida == 4 or "cena" in nombre_comida:
            agrupado[clave]["cena"] = "Sí"

    output = io.StringIO()
    columnas = [
        "apellido y nombre",
        "DNI",
        "sector",
        "desayuno",
        "almuerzo",
        "merienda",
        "cena",
        "tipo de menú",
    ]
    writer = csv.DictWriter(output, fieldnames=columnas)
    writer.writeheader()
    for fila in agrupado.values():
        writer.writerow(fila)
    return output.getvalue()


def resumen_autorizaciones_service(filtros: dict):
    """Obtiene el resumen de autorizaciones (pedidos vs autorizados) en JSON o CSV"""
    
    formato = filtros.get("formato")
    if formato is not None and formato != "csv":
        raise ValueError("El parámetro 'formato' solo admite el valor 'csv'.")

    if formato == "csv":
        _validar_formato_y_rango_csv(filtros)

    filtros_validados = validador.validar_filtros_autorizaciones(filtros)
    filtros_validados = _forzar_sector_jefe_servicio(filtros_validados)

    resumen = repo_solicitudes.obtener_resumen_autorizaciones(
        fecha_desde=filtros_validados.get("fecha_desde"),
        fecha_hasta=filtros_validados.get("fecha_hasta"),
        id_sector=filtros_validados.get("sector"),
        id_tipo_comida=filtros_validados.get("tipo_comida"),
        id_tipo_menu=filtros_validados.get("tipo_menu"),
        condicion=filtros_validados.get("condicion"),
        estado=filtros_validados.get("estado_enum"),
    )

    if formato == "csv":
        output = io.StringIO()
        columnas = [
            "sector",
            "comida",
            "tipo de menú",
            "pedidas regulares",
            "pedidas excepción",
            "total pedidas",
            "total autorizadas",
            "diferencia",
        ]
        writer = csv.DictWriter(output, fieldnames=columnas)
        writer.writeheader()
        for fila in resumen.get("desglose", []):
            writer.writerow({
                "sector": fila["sector"],
                "comida": fila["comida"],
                "tipo de menú": fila["tipo_menu"],
                "pedidas regulares": fila["cantidad_pedida_regulares"],
                "pedidas excepción": fila["cantidad_pedida_excepciones"],
                "total pedidas": fila["cantidad_pedida"],
                "total autorizadas": fila["cantidad_autorizada"],
                "diferencia": fila["diferencia"],
            })
        return output.getvalue()

    return resumen


def consultar_comidas_autorizadas_persona(id_personal: int, fecha_consulta):
    """Consulta las comidas autorizadas para una persona específica en una fecha"""

    # Si fecha_consulta viene como string desde el controlador, el validator la convierte a date
    fecha_valida = validador.validar_fecha_opcional(fecha_consulta) or date.today()

    persona = db.session.get(Personal, id_personal)
    if not persona:
        raise RecursoNoEncontradoError("La persona indicada no existe.")

    return repo_solicitudes.buscar_comidas_autorizadas(
        fecha=fecha_valida, id_personal=id_personal
    )


def registrar_entrega_comedor(
    id_user: int,
    ids_solicitudes: list[int],
    id_personal_retira: int | None = None,
    tercero: dict | None = None,
):
    """Registra la entrega de una o varias comidas validando autorizacion vigente, evitando entregas duplicadas"""

    # Valido lista de solicitudes y formato de tercero (si se envio) en el validator
    dni_tercero, nombre_tercero = validador.validar_datos_entrega(
        ids_solicitudes, id_personal_retira, tercero
    )

    personas_incluidas = set()
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

        personas_incluidas.add(solicitud.idPersonal)

    # Etapa 2: Si el retiro incluye una sola persona, esa persona es el responsable por defecto
    if len(personas_incluidas) == 1 and not id_personal_retira and not dni_tercero:
        id_personal_retira = next(iter(personas_incluidas))

    # Etapa 2: El responsable es obligatorio cuando el retiro incluye mas de una persona
    if len(personas_incluidas) > 1 and not id_personal_retira and not dni_tercero:
        raise ValueError("Debe indicar el responsable del retiro cuando se retira para varias personas.")

    # Checkeo que el responsable de retirar la vianda exista (si es personal del hospital)
    if id_personal_retira:
        responsable = db.session.get(Personal, id_personal_retira)
        if not responsable:
            raise ValueError("El responsable del retiro indicado no existe en el padrón de personal.")

    return repo_entregas.registrar_entregas_multiples(
        id_user,
        ids_solicitudes,
        id_personal_retira,
        dni_tercero=dni_tercero,
        nombre_tercero=nombre_tercero,
    )


def listar_entregas_service(filtros: dict):
    """Lista las entregas registradas (evita que el controlador llame directo a repo_entregas)"""

    filtros = validador.validar_filtros_entregas(filtros)
    return repo_entregas.listar_entregas(
        fecha=filtros.get("fecha"),
        id_sector=filtros.get("sector"),
        id_tipo_comida=filtros.get("tipo_comida"),
    )


def obtener_detalle_entrega_service(id_entrega: int):
    """Obtiene el detalle de una entrega por ID (evita que el controlador llame directo a repo_entregas)"""

    entrega = repo_entregas.get_entrega_by_id(id_entrega)
    if not entrega:
        raise RecursoNoEncontradoError("Entrega no encontrada.")
    return entrega


# <------ Resumenes ------>

def obtener_resumen_entregas_service(filtros: dict):
    """Obtiene el resumen de entregas autorizadas/entregadas"""

    filtros = validador.validar_filtros_entregas(filtros)
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




def resumen_entregas_generales_service(filtros: dict):
    """Obtiene el resumen general de entregas (autorizados vs entregados)"""

    filtros = validador.validar_filtros_autorizaciones(filtros)
    filtros = _forzar_sector_jefe_servicio(filtros)

    return repo_solicitudes.obtener_resumen_entregas_generales(
        fecha_desde=filtros.get("fecha_desde"),
        fecha_hasta=filtros.get("fecha_hasta"),
        id_sector=filtros.get("sector"),
        id_tipo_comida=filtros.get("tipo_comida"),
        id_tipo_menu=filtros.get("tipo_menu"),
        condicion=filtros.get("condicion"),
    )

def listar_fechas_para_autorizacion(filtros: dict):
    """Lista las fechas que poseen pedidos para marcar en el calendario """

    filtros = validador.validar_filtros_autorizaciones(filtros)
    filtros = _forzar_sector_jefe_servicio(filtros)

    return repo_solicitudes.listar_fechas_autorizacion(
        fecha_desde=filtros.get("fecha_desde"),
        fecha_hasta=filtros.get("fecha_hasta"),
        id_sector=filtros.get("sector"),
        id_tipo_comida=filtros.get("tipo_comida"),
        id_tipo_menu=filtros.get("tipo_menu"),
        estado=filtros.get("estado_enum"),
    )