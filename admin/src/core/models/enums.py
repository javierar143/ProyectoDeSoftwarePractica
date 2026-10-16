"""Enumeraciones del dominio para pedidos, solicitudes y cupos."""

import enum


class Periodicidad(str, enum.Enum):
    """Periodicidad con la que se carga un pedido."""

    DIARIA = "diaria"
    SEMANAL = "semanal"
    MENSUAL = "mensual"


class EstadoPedido(str, enum.Enum):
    """Estado general de un pedido."""

    CONFIRMADO = "confirmado"
    AUTORIZADO = "autorizado"
    RECHAZADO = "rechazado"


class CondicionCupo(str, enum.Enum):
    """Condición de una solicitud respecto del cupo del sector."""

    REGULAR = "regular"
    EXCEPCION = "excepcion"


class EstadoAutorizacion(str, enum.Enum):
    """Estado de autorización de una solicitud."""

    PENDIENTE = "pendiente"
    AUTORIZADA = "autorizada"
    NO_AUTORIZADA = "no_autorizada"