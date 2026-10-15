from src.core.database import db
from src.core.models.Configuracion import Configuracion


def obtener_configuracion():
    """Obtiene la configuracion actual del sistema, caso contrario inicializa una default"""

    config = db.session.query(Configuracion).first()
    # Si no existe , la creo con valores default
    if not config:
        config = Configuracion(elementos_por_pagina=10, modo_mantenimiento=False)
        db.session.add(config)
        db.session.commit()
    return config


def actualizar_configuracion(elementos, mantenimiento):
    """Actualiza la configuracion del sistema y el estado"""

    config = obtener_configuracion()
    config.elementos_por_pagina = elementos
    config.modo_mantenimiento = mantenimiento
    db.session.commit()
    return config