from src.core.database import db
from src.core.models.Configuracion import Configuracion


def obtener_configuracion():
    """Obtiene la configuración actual del sistema, caso contrario inicializa una default"""
    config = db.session.query(Configuracion).first()
    # Si no existe, la creo con valores default
    if not config:
        config = Configuracion(
            elementos_por_pagina=10, 
            modo_mantenimiento=False,
            mensaje_mantenimiento="El sistema se encuentra en mantenimiento temporalmente."
        )
        db.session.add(config)
        db.session.commit()
    return config


def actualizar_configuracion(elementos, mantenimiento, mensaje):
    """Actualiza la configuración del sistema, el estado de mantenimiento y el mensaje"""
    config = obtener_configuracion()
    config.elementos_por_pagina = elementos
    config.modo_mantenimiento = mantenimiento
    config.mensaje_mantenimiento = mensaje
    db.session.commit()
    return config