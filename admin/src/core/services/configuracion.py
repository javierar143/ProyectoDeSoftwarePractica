from src.core.repositories import configuracion as repo_config

def obtener_configuracion():
    """Obtiene la configuracion actual del sistema a partir del repo"""

    return repo_config.obtener_configuracion()

def actualizar_configuracion(elementos: int, mantenimiento: bool):
    """Valida y actualiza la configuracion del sistema y el estado, enviando la actualizacion"""

    # Validos numero invalido
    if elementos < 1:
        raise ValueError("La cantidad de elementos debe ser mayor a 0.")
    return repo_config.actualizar_configuracion(elementos, mantenimiento)