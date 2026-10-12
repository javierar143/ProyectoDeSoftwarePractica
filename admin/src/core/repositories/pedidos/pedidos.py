from src.core.models.Pedido import Pedido
from src.core.models.Solicitud import Solicitud
from src.core.database import db


def create_pedido_con_solicitudes(nuevo_pedido: Pedido, lista_solicitudes: list[Solicitud]) -> Pedido:
    """
    Guarda la cabecera (Pedido) y sus detalles (Solicitudes) en una misma transacción.
    No hace commit, solo prepara la unidad de trabajo.
    """
    db.session.add(nuevo_pedido)
    db.session.flush()

    for solicitud in lista_solicitudes:
        solicitud.idPedido = nuevo_pedido.idPedido
        db.session.add(solicitud)

    return nuevo_pedido