"""Servicios para la creación, actualización, consulta y eliminación de pedidos."""

from datetime import date, datetime, time, timedelta
from flask import abort

from src.core.models.enums import (
    CondicionCupo,
    EstadoAutorizacion,
    EstadoPedido,
    Periodicidad,
)
from src.core.models.Pedido import Pedido
from src.core.models.Personal import Personal
from src.core.models.Solicitud import Solicitud
from src.core.repositories.pedidos import pedidos as repo_pedidos
from src.core.repositories.personal import personal as repo_personal
from src.core.services.configuracion import obtener_configuracion
from src.core.services.cupos import cupos


def _obtener_hora_corte() -> time:
    """Obtiene el horario de corte configurado en Ajustes del sistema (fallback 18:00)."""
    config = obtener_configuracion()
    valor = (
        getattr(config, "horario_corte", None)
        or getattr(config, "hora_corte", None)
        or getattr(config, "horaCorte", None)
    )

    if isinstance(valor, time):
        return valor

    if isinstance(valor, datetime):
        return valor.time()

    if isinstance(valor, str) and valor.strip():
        partes = valor.strip().split(":")
        try:
            hora = int(partes[0])
            minuto = int(partes[1]) if len(partes) > 1 else 0
            return time(hour=hora, minute=minuto)
        except ValueError:
            pass

    return time(hour=18, minute=0)


def _esta_fuera_de_corte(fecha_pedido: date, ahora: datetime, hora_corte: time) -> bool:
    """
    Indica si fecha_pedido ya pasó o ya superó el horario de corte del día anterior
    según la hora actual del servidor.
    """
    if fecha_pedido < ahora.date():
        return True

    dia_anterior = fecha_pedido - timedelta(days=1)
    limite_corte = datetime.combine(dia_anterior, hora_corte)
    return ahora > limite_corte


def _validar_fecha_y_corte(fecha_pedido: date) -> None:
    """Valida que una fecha de pedido no sea pasada ni haya superado su horario de corte."""
    ahora = datetime.now()
    hora_corte = _obtener_hora_corte()

    if fecha_pedido < ahora.date():
        abort(
            400,
            description=(
                f"No se pueden operar pedidos para una fecha pasada "
                f"({fecha_pedido.isoformat()})."
            ),
        )

    dia_anterior = fecha_pedido - timedelta(days=1)
    limite_corte = datetime.combine(dia_anterior, hora_corte)

    if ahora > limite_corte:
        abort(
            400,
            description=(
                f"El horario de corte ({hora_corte.strftime('%H:%M')} del día "
                f"anterior, {limite_corte.strftime('%d/%m/%Y %H:%M')}) ya venció "
                f"para la fecha {fecha_pedido.isoformat()}."
            ),
        )


def validar_sector_personal(persona: Personal, id_sector_jefe: int) -> None:
    """
    Verifica que si la persona es Personal Fijo, su sector coincida con el del Jefe.
    Los Residentes pueden incorporarse a pedidos de cualquier sector sin esta validación.
    """
    tipo_personal = getattr(persona, "tipo_personal", None)
    if tipo_personal is None:
        tipo_personal = repo_pedidos.get_tipo_personal_by_id(
            persona.idTipoPersonal
        )

    if (
        tipo_personal
        and "fijo" in tipo_personal.nombre.strip().lower()
        and not repo_personal.pertenece_a_sector(
            persona.idPersonal, id_sector_jefe
        )
    ):
        abort(
            400,
            description=f"La persona con ID {persona.idPersonal} es personal fijo y no pertenece al sector del Jefe de Servicio.",
        )


def _calcular_fecha_hasta(
    fecha_desde: date,
    periodicidad: Periodicidad,
    fecha_hasta: date | None = None,
) -> date:
    """Calcula la fecha_hasta obligatoria del Pedido según su periodicidad."""
    if fecha_hasta is not None:
        return fecha_hasta
    if periodicidad == Periodicidad.SEMANAL:
        return fecha_desde + timedelta(days=6)
    if periodicidad == Periodicidad.MENSUAL:
        return fecha_desde + timedelta(days=29)
    return fecha_desde


def _obtener_fechas_periodo(
    fecha_desde: date,
    periodicidad: Periodicidad,
    fecha_hasta: date | None = None,
) -> list[date]:
    """Devuelve la lista de fechas del período según periodicidad o fecha_hasta."""
    if fecha_hasta is not None:
        if fecha_hasta < fecha_desde:
            abort(
                400,
                description="La fecha_hasta no puede ser anterior a fecha_desde.",
            )
        fin = fecha_hasta
    elif periodicidad == Periodicidad.SEMANAL:
        fin = fecha_desde + timedelta(days=6)
    elif periodicidad == Periodicidad.MENSUAL:
        fin = fecha_desde + timedelta(days=29)
    else:
        fin = fecha_desde

    fechas: list[date] = []
    actual = fecha_desde
    while actual <= fin:
        fechas.append(actual)
        actual += timedelta(days=1)
    return fechas


def crear_pedido(
    id_jefe: int,
    id_sector: int,
    fecha_desde: date,
    periodicidad: str,
    comidas: dict[int, list[int]],
    fecha_hasta: date | None = None,
    dias_excluidos: list[date] | None = None,
) -> Pedido | tuple[dict, int]:
    """
    Crea un Pedido por cada día del período según la periodicidad (diaria, semanal, mensual)
    y genera las Solicitudes de cada día calculando cupo Regular o Excepción.
    """
    periodicidad_enum = Periodicidad(periodicidad.lower())
    fechas_periodo = _obtener_fechas_periodo(
        fecha_desde, periodicidad_enum, fecha_hasta
    )

    excluidos_set = set(dias_excluidos or [])
    if excluidos_set:
        fechas_periodo = [f for f in fechas_periodo if f not in excluidos_set]

    if not fechas_periodo:
        abort(
            400,
            description="Debe quedar al menos un día activo en el período.",
        )

    ahora = datetime.now()
    hora_corte = _obtener_hora_corte()
    fechas_rechazadas = [
        fecha_dia.isoformat()
        for fecha_dia in fechas_periodo
        if _esta_fuera_de_corte(fecha_dia, ahora, hora_corte)
    ]
    if fechas_rechazadas:
        abort(
            400,
            description=(
                "No se pueden crear pedidos para fechas pasadas o que ya "
                f"superaron su horario de corte: {', '.join(fechas_rechazadas)}."
            ),
        )

    # Si alguna fecha activa del período ya tiene pedido para este sector,
    # informamos todas las fechas en conflicto con su requestId para editar.
    fechas_conflicto: list[dict[str, int | str]] = []
    for fecha_dia in fechas_periodo:
        pedido_existente = repo_pedidos.get_pedido_en_sector_y_fecha(
            id_sector, fecha_dia
        )
        if pedido_existente is not None:
            fechas_conflicto.append(
                {
                    "fecha": fecha_dia.isoformat(),
                    "requestId": pedido_existente.idPedido,
                }
            )

    if fechas_conflicto:
        fechas_str = ", ".join(
            f"{item['fecha'].split('-')[2]}/{item['fecha'].split('-')[1]}/{item['fecha'].split('-')[0]}"
            for item in fechas_conflicto
        )
        return (
            {
                "error": f"Ya existe un pedido registrado para este sector en: {fechas_str}.",
                "fechas_conflicto": fechas_conflicto,
            },
            409,
        )

    pedidos_y_solicitudes: list[tuple[Pedido, list[Solicitud]]] = []

    for fecha_dia in fechas_periodo:
        pedido_dia = Pedido(
            idUser=id_jefe,
            idSector=id_sector,
            fecha_desde=fecha_dia,
            fecha_hasta=fecha_dia,
            periodicidad=periodicidad_enum,
            estado_general=EstadoPedido.CONFIRMADO,
            activo=True,
        )

        solicitudes_dia: list[Solicitud] = []

        for id_tipo_comida_str, lista_personal in comidas.items():
            id_tipo_comida = int(id_tipo_comida_str)

            cupo = cupos.get_by_sector_y_comida(id_sector, id_tipo_comida)
            limite_cupo = cupo.cantComensales if cupo else 0

            contador_comida = 0
            vistos_en_comida: set[int] = set()

            for id_personal in lista_personal:
                if id_personal in vistos_en_comida:
                    abort(
                        409,
                        description=f"La persona {id_personal} está repetida en la misma comida.",
                    )
                vistos_en_comida.add(id_personal)

                persona = repo_personal.get_by_id(id_personal)
                if not persona or not persona.isActive:
                    abort(
                        400,
                        description=f"La persona con ID {id_personal} no existe o está inactiva.",
                    )

                validar_sector_personal(persona, id_sector)

                if repo_pedidos.existe_solicitud_duplicada(
                    id_personal=id_personal,
                    fecha=fecha_dia,
                    id_tipo_comida=id_tipo_comida,
                ):
                    abort(
                        409,
                        description=(
                            f"La persona con ID {id_personal} ya tiene una solicitud "
                            f"activa para esa comida en la fecha {fecha_dia.isoformat()}."
                        ),
                    )

                contador_comida += 1
                condicion = (
                    CondicionCupo.REGULAR
                    if contador_comida <= limite_cupo
                    else CondicionCupo.EXCEPCION
                )

                solicitudes_dia.append(
                    Solicitud(
                        idPersonal=id_personal,
                        idTipoComida=id_tipo_comida,
                        idTipoMenu=persona.idTipoMenu,
                        condicionCupo=condicion,
                        estadoAutorizacion=EstadoAutorizacion.PENDIENTE,
                        fecha_vianda=fecha_dia,
                        activo=True,
                    )
                )

        pedidos_y_solicitudes.append((pedido_dia, solicitudes_dia))

    if len(pedidos_y_solicitudes) == 1:
        unico_pedido, unicas_solicitudes = pedidos_y_solicitudes[0]
        pedido_creado = repo_pedidos.create_pedido_con_solicitudes(
            unico_pedido, unicas_solicitudes
        )
        return [pedido_creado]

    return repo_pedidos.create_multiples_pedidos_con_solicitudes(
        pedidos_y_solicitudes
    )

def actualizar_pedido(
    id_pedido: int,
    comidas: dict[int, list[int]],
    id_sector_jefe: int | None = None,
    fecha_desde: date | None = None,
    periodicidad: str | None = None,
    fecha_hasta: date | None = None,
) -> Pedido:
    """
    Modifica un pedido existente si sigue en estado CONFIRMADO y no superó el corte.
    Desactiva lógicamente las solicitudes anteriores y recalcula cupos (Regular/Excepción).
    """
    pedido = repo_pedidos.get_pedido_by_id(id_pedido)
    if not pedido:
        abort(404, description=f"El pedido con ID {id_pedido} no existe.")

    if id_sector_jefe is not None and pedido.idSector != id_sector_jefe:
        abort(
            403,
            description="No tiene permisos para operar sobre un pedido de otro sector.",
        )

    _validar_fecha_y_corte(pedido.fecha_desde)

    if pedido.estado_general != EstadoPedido.CONFIRMADO:
        abort(
            409,
            description=f"No se puede modificar un pedido que ya está {pedido.estado_general.value}.",
        )

    if fecha_desde is not None:
        _validar_fecha_y_corte(fecha_desde)
        pedido.fecha_desde = fecha_desde
    if periodicidad is not None:
        pedido.periodicidad = Periodicidad(periodicidad.lower())
    if (
        fecha_desde is not None
        or periodicidad is not None
        or fecha_hasta is not None
    ):
        pedido.fecha_hasta = _calcular_fecha_hasta(
            pedido.fecha_desde, pedido.periodicidad, fecha_hasta
        )

    repo_pedidos.limpiar_solicitudes_de_pedido(id_pedido)

    solicitudes_a_guardar: list[Solicitud] = []

    for id_tipo_comida_str, lista_personal in comidas.items():
        id_tipo_comida = int(id_tipo_comida_str)

        cupo = cupos.get_by_sector_y_comida(pedido.idSector, id_tipo_comida)
        limite_cupo = cupo.cantComensales if cupo else 0

        contador_comida = 0
        vistos_en_comida: set[int] = set()

        for id_personal in lista_personal:
            if id_personal in vistos_en_comida:
                abort(
                    409,
                    description=f"La persona {id_personal} está repetida en la misma comida.",
                )
            vistos_en_comida.add(id_personal)

            persona = repo_personal.get_by_id(id_personal)
            if not persona or not persona.isActive:
                abort(
                    400,
                    description=f"La persona con ID {id_personal} no existe o está inactiva.",
                )

            validar_sector_personal(persona, pedido.idSector)

            if repo_pedidos.existe_solicitud_duplicada(
                id_personal=id_personal,
                id_sector=pedido.idSector,
                fecha=pedido.fecha_desde,
                id_tipo_comida=id_tipo_comida,
                excluir_id_pedido=pedido.idPedido,
            ):
                abort(
                    409,
                    description=f"Ya existe una solicitud para la persona {id_personal} en esa fecha.",
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
                activo=True,
            )
            solicitudes_a_guardar.append(nueva_solicitud)

    return repo_pedidos.guardar_nuevas_solicitudes(
        pedido, solicitudes_a_guardar
    )


def borrar_pedido(id_pedido: int, id_sector_jefe: int | None = None) -> Pedido:
    """
    Valida y realiza la baja lógica de un pedido si sigue en estado CONFIRMADO
    y no superó el horario de corte.
    """
    pedido = repo_pedidos.get_pedido_by_id(id_pedido)
    if not pedido:
        abort(404, description=f"El pedido con ID {id_pedido} no existe.")

    if id_sector_jefe is not None and pedido.idSector != id_sector_jefe:
        abort(
            403,
            description="No tiene permisos para operar sobre un pedido de otro sector.",
        )

    _validar_fecha_y_corte(pedido.fecha_desde)

    if pedido.estado_general != EstadoPedido.CONFIRMADO:
        abort(
            409,
            description=f"No se puede eliminar un pedido que ya fue {pedido.estado_general.value}.",
        )

    return repo_pedidos.eliminar_pedido(pedido)


def obtener_detalle_pedido(
    id_pedido: int, id_sector_jefe: int | None = None
) -> dict:
    """Devuelve el detalle completo de un pedido con totales pedidos y autorizados separados."""
    pedido = repo_pedidos.get_pedido_by_id(id_pedido)
    if not pedido:
        abort(404, description=f"El pedido con ID {id_pedido} no existe.")

    if id_sector_jefe is not None and pedido.idSector != id_sector_jefe:
        abort(
            403,
            description="No tiene permisos para consultar un pedido de otro sector.",
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

        detalle_solicitudes.append(
            {
                "idSolicitud": s.idSolicitud,
                "idPersonal": s.idPersonal,
                "idTipoComida": s.idTipoComida,
                "idTipoMenu": s.idTipoMenu,
                "fecha_vianda": s.fecha_vianda.isoformat(),
                "condicionCupo": s.condicionCupo.value,
                "estadoAutorizacion": s.estadoAutorizacion.value,
            }
        )

    fecha_hasta_val = getattr(pedido, "fecha_hasta", None) or pedido.fecha_desde

    resultado = {
        "idPedido": pedido.idPedido,
        "idSector": pedido.idSector,
        "fecha_desde": pedido.fecha_desde.isoformat(),
        "fecha_hasta": fecha_hasta_val.isoformat(),
        "periodicidad": pedido.periodicidad.value,
        "estado": pedido.estado_general.value,
        "activo": pedido.activo,
        "cantidades_pedidas": totales_pedidos,
        "solicitudes": detalle_solicitudes,
    }

    if pedido.estado_general in (
        EstadoPedido.AUTORIZADO,
        EstadoPedido.RECHAZADO,
    ):
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
    estado_enum = EstadoPedido(estado_str.lower()) if estado_str else None

    if page < 1:
        page = 1

    config = obtener_configuracion()
    per_page = config.elementos_por_pagina

    pedidos_lista, total = repo_pedidos.list_pedidos_by_sector(
        page=page,
        per_page=per_page,
        id_sector=id_sector,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        estado=estado_enum,
        id_tipo_comida=id_tipo_comida,
        id_tipo_menu=id_tipo_menu,
    )

    items = [
        obtener_detalle_pedido(p.idPedido, id_sector) for p in pedidos_lista
    ]
    return items, total, per_page


def obtener_resumen_pedidos(
    id_sector: int | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    id_tipo_comida: int | None = None,
    id_tipo_menu: int | None = None,
    agrupamiento: str = "sector",
) -> dict:
    """
    Calcula los totales de comidas pedidas (totales, regulares y por excepción)
    agrupados por día, semana, mes, sector, comida o tipo de menú.
    """
    filas = repo_pedidos.obtener_solicitudes_para_resumen(
        id_sector=id_sector,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        id_tipo_comida=id_tipo_comida,
        id_tipo_menu=id_tipo_menu,
    )

    grupos: dict[str, dict[str, int]] = {}
    total_general = 0

    for solicitud, sector_pedido in filas:
        if agrupamiento == "dia":
            clave = solicitud.fecha_vianda.isoformat()
        elif agrupamiento == "semana":
            iso_year, iso_week, _ = solicitud.fecha_vianda.isocalendar()
            clave = f"{iso_year}-W{iso_week:02d}"
        elif agrupamiento == "mes":
            clave = solicitud.fecha_vianda.strftime("%Y-%m")
        elif agrupamiento == "comida":
            clave = f"comida_{solicitud.idTipoComida}"
        elif agrupamiento == "tipo_menu":
            clave = f"menu_{solicitud.idTipoMenu}"
        else:
            clave = f"sector_{sector_pedido}"

        if clave not in grupos:
            grupos[clave] = {
                "total_pedidas": 0,
                "regulares": 0,
                "excepciones": 0,
            }

        grupos[clave]["total_pedidas"] += 1
        if solicitud.condicionCupo == CondicionCupo.REGULAR:
            grupos[clave]["regulares"] += 1
        else:
            grupos[clave]["excepciones"] += 1

        total_general += 1

    return {
        "agrupamiento": agrupamiento,
        "total_general": total_general,
        "resumen": grupos,
    }