from datetime import date
from src.core.models.enums import EstadoAutorizacion, EstadoPedido


def validar_fecha_opcional(valor, nombre_campo: str = "fecha") -> date | None:
    """Acepta un date o un string YYYY-MM-DD y devuelve un objeto date."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor).strip())
    except ValueError:
        raise ValueError(f"Formato de {nombre_campo} inválido. Use YYYY-MM-DD.")


def validar_filtros_autorizaciones(filtros: dict) -> dict:
    """Valida fechas, estado (Enum) y filtro de condición para listados y resúmenes."""
    copia = dict(filtros)
    fecha_desde = validar_fecha_opcional(copia.get("fecha_desde"), "fecha_desde")
    fecha_hasta = validar_fecha_opcional(copia.get("fecha_hasta"), "fecha_hasta")

    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise ValueError("La fecha 'desde' no puede ser posterior a la fecha 'hasta'.")

    estado_enum = None
    if copia.get("estado"):
        if isinstance(copia["estado"], EstadoPedido):
            estado_enum = copia["estado"]
        else:
            try:
                estado_enum = EstadoPedido[str(copia["estado"]).strip().upper()]
            except KeyError:
                raise ValueError(f"Estado de pedido inválido: {copia['estado']}")

    condicion = copia.get("condicion")
    if condicion:
        condicion_limpia = str(condicion).strip().lower()
        if condicion_limpia not in ("regular", "excepcion", "todas"):
            raise ValueError("Condición inválida. Use 'regular', 'excepcion' o 'todas'.")
        copia["condicion"] = condicion_limpia

    copia["fecha_desde"] = fecha_desde
    copia["fecha_hasta"] = fecha_hasta
    copia["estado_enum"] = estado_enum
    return copia


def validar_items_autorizacion(
    items_evaluados: list[dict], ids_validos: set[int] | None = None, id_pedido: int | None = None
) -> dict[int, EstadoAutorizacion]:
    """Valida el listado de solicitudes a evaluar y devuelve el diccionario {idSolicitud: EstadoAutorizacion}."""
    if not items_evaluados or not isinstance(items_evaluados, list):
        raise ValueError("Debe enviar el listado de solicitudes a evaluar.")

    decisiones = {}
    for item in items_evaluados:
        if not isinstance(item, dict):
            raise ValueError("Cada ítem de solicitud debe ser un objeto válido.")

        id_sol = item.get("idSolicitud")
        estado_txt = (item.get("estado") or "").upper()

        if ids_validos is not None and id_sol not in ids_validos:
            raise ValueError(f"La solicitud {id_sol} no pertenece al pedido {id_pedido}.")

        if estado_txt in ("AUTORIZADA", "AUTORIZADO"):
            decisiones[id_sol] = EstadoAutorizacion.AUTORIZADA
        elif estado_txt in ("NO_AUTORIZADA", "NO AUTORIZADA", "RECHAZADA", "RECHAZADO"):
            decisiones[id_sol] = EstadoAutorizacion.NO_AUTORIZADA
        else:
            raise ValueError(f"Estado '{estado_txt}' inválido. Use AUTORIZADA o NO_AUTORIZADA.")

    return decisiones


def validar_motivo_rechazo(motivo: str | None) -> str:
    """Valida que el motivo de rechazo sea obligatorio (Etapa 2)."""
    motivo_limpio = (motivo or "").strip()
    if not motivo_limpio:
        raise ValueError("El motivo de rechazo es obligatorio.")
    return motivo_limpio


def validar_filtros_comidas_autorizadas(filtros: dict) -> dict:
    """Valida que haya al menos un filtro y que la fecha sea válida."""
    copia = dict(filtros)
    copia["fecha"] = validar_fecha_opcional(copia.get("fecha"), "fecha")

    if not any(copia.values()):
        raise ValueError(
            "Debe enviar al menos un filtro de búsqueda (fecha, dni, sector o tipo_comida)."
        )
    return copia


def validar_filtros_entregas(filtros: dict) -> dict:
    """Valida la fecha en los filtros de entregas y resumen de entregas."""
    copia = dict(filtros)
    copia["fecha"] = validar_fecha_opcional(copia.get("fecha"), "fecha")
    return copia


def validar_datos_entrega(
    ids_solicitudes: list[int],
    id_personal_retira: int | None = None,
    tercero: dict | None = None,
) -> tuple[str | None, str | None]:
    """Valida la lista de solicitudes y el formato del tercero responsable si aplica."""
    if not ids_solicitudes or not isinstance(ids_solicitudes, list):
        raise ValueError("Debe indicar al menos una solicitud para entregar.")

    dni_tercero = None
    nombre_tercero = None
    if tercero:
        if not isinstance(tercero, dict):
            raise ValueError("Los datos del tercero responsable son inválidos.")
        dni_tercero = str(tercero.get("dni") or "").strip()
        nombre_tercero = str(tercero.get("nombre_apellido") or tercero.get("nombre") or "").strip()
        if not dni_tercero.isdigit() or not (7 <= len(dni_tercero) <= 8):
            raise ValueError("El DNI del tercero responsable no tiene un formato válido.")
        if not nombre_tercero:
            raise ValueError("Debe indicar el nombre y apellido del tercero responsable.")

    return dni_tercero, nombre_tercero