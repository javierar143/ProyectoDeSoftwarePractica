from datetime import date

from src.core.models.enums import (
    EstadoPedido,
    Periodicidad,
    CondicionCupo,
    EstadoAutorizacion,
)
from src.core.database import db
from src.core.models.Pedido import Pedido
from src.core.models.Solicitud import Solicitud
from src.core.models.Personal import Personal
from src.core.services.cupos import cupos
from src.core.repositories.pedidos import pedidos as repo_pedidos


class PedidoValidationError(Exception):
    """Error para datos inválidos o reglas que devuelven HTTP 400."""
    pass


class PedidoConflictError(Exception):
    """Error para conflictos o duplicados que devuelven HTTP 409."""
    pass


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
        raise PedidoValidationError("El pedido debe incluir al menos una solicitud de comida.")

    try:
        periodicidad_enum = Periodicidad(periodicidad.lower())
    except (ValueError, AttributeError):
        raise PedidoValidationError("La periodicidad indicada no es válida.")

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

    return repo_pedidos.create_pedido_con_solicitudes(nuevo_pedido, solicitudes_a_guardar)