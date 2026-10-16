"""Validador de datos de personal."""

def validar_datos_personal(datos: dict, tipos_personal: list) -> list[str]:
    """Valida los datos de entrada del formulario de personal."""
    errores = []
    
    dni = datos.get("dni", "").strip()
    nombre = datos.get("nombre", "").strip()
    apellido = datos.get("apellido", "").strip()
    id_tipo_personal = datos.get("idTipoPersonal")
    id_tipo_menu = datos.get("idTipoMenu")
    id_sector = datos.get("idSector")

    if not dni or not dni.isdigit():
        errores.append("El DNI es obligatorio y debe contener solo números.")
    if not nombre:
        errores.append("El nombre es obligatorio.")
    if not apellido:
        errores.append("El apellido es obligatorio.")
    if not id_tipo_personal:
        errores.append("Debe seleccionar un tipo de personal.")
    if not id_tipo_menu:
        errores.append("Debe seleccionar un tipo de menú.")

    #  el personal fijo requiere sector
    tipo_sel = next((t for t in tipos_personal if str(t.idTipoPersonal) == str(id_tipo_personal)), None)
    if tipo_sel and "fijo" in tipo_sel.nombre.lower() and not id_sector:
        errores.append("Debe seleccionar un sector para el personal fijo.")

    return errores