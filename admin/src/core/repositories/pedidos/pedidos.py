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


def get_pedido_by_id(id_pedido: int) -> Pedido | None:
    """Recupera un pedido por su clave primaria."""
    return db.session.get(Pedido, id_pedido)


def limpiar_solicitudes_de_pedido(id_pedido: int):
    """
    Borra todos los renglones (solicitudes) actuales de un pedido.
    """
    stmt = db.delete(Solicitud).where(Solicitud.idPedido == id_pedido)
    db.session.execute(stmt)
    db.session.flush()


def guardar_nuevas_solicitudes(pedido: Pedido, nuevas_solicitudes: list[Solicitud]) -> Pedido:
    """Asocia y agrega los nuevos renglones al pedido."""
    for sol in nuevas_solicitudes:
        sol.idPedido = pedido.idPedido
        db.session.add(sol)

    return pedido


def eliminar_pedido(pedido: Pedido):
    """
    Elimina físicamente el pedido y sus solicitudes asociadas.
    La eliminación del detalle (solicitudes) se hace primero para mantener
    la integridad referencial.
    """
    stmt = db.delete(Solicitud).where(Solicitud.idPedido == pedido.idPedido)
    db.session.execute(stmt)

    db.session.delete(pedido)