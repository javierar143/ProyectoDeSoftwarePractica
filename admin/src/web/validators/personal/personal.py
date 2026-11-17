"""Validador de datos de personal."""

import re


PATRON_NOMBRE = re.compile(
    r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s'-]+$"
)


def validar_datos_personal(
    datos: dict,
    tipos_personal: list,
    tipos_menu: list | None = None,
    sectores: list | None = None,
    sector_forzado: int | None = None,
) -> list[str]:
    """Valida los datos de entrada del formulario de personal."""
    errores = []

    dni = str(datos.get("dni") or "").strip()
    nombre = str(datos.get("nombre") or "").strip()
    apellido = str(datos.get("apellido") or "").strip()
    id_tipo_personal = str(datos.get("idTipoPersonal") or "").strip()
    id_tipo_menu = str(datos.get("idTipoMenu") or "").strip()
    id_sector = str(datos.get("idSector") or "").strip()

    if sector_forzado is not None and not id_sector:
        id_sector = str(sector_forzado)

    if not dni or not dni.isdigit():
        errores.append("El DNI es obligatorio y debe contener solo números.")
    elif not 7 <= len(dni) <= 10:
        errores.append("El DNI debe tener entre 7 y 10 dígitos.")

    if not nombre:
        errores.append("El nombre es obligatorio.")
    elif not 2 <= len(nombre) <= 50:
        errores.append("El nombre debe tener entre 2 y 50 caracteres.")
    elif not PATRON_NOMBRE.fullmatch(nombre):
        errores.append(
            "El nombre solo puede contener letras, espacios, guiones y apóstrofes."
        )

    if not apellido:
        errores.append("El apellido es obligatorio.")
    elif not 2 <= len(apellido) <= 50:
        errores.append("El apellido debe tener entre 2 y 50 caracteres.")
    elif not PATRON_NOMBRE.fullmatch(apellido):
        errores.append(
            "El apellido solo puede contener letras, espacios, guiones y apóstrofes."
        )

    # Validación de Tipo de Personal
    tipo_sel = None
    if not id_tipo_personal:
        errores.append("Debe seleccionar un tipo de personal.")
    else:
        tipo_sel = next(
            (
                t
                for t in tipos_personal
                if str(t.idTipoPersonal) == id_tipo_personal
            ),
            None,
        )
        if tipo_sel is None:
            errores.append("El tipo de personal seleccionado no es válido.")

    # Validación de Tipo de Menú
    if not id_tipo_menu:
        errores.append("Debe seleccionar un tipo de menú.")
    elif tipos_menu is not None:
        menu_sel = next(
            (
                m
                for m in tipos_menu
                if str(m.idTipoMenu) == id_tipo_menu
            ),
            None,
        )
        if menu_sel is None:
            errores.append("El tipo de menú seleccionado no es válido.")

    # Validación de Sector según el Tipo de Personal
    if tipo_sel is not None:
        nombre_tipo = tipo_sel.nombre.lower()
        if "fijo" in nombre_tipo:
            if not id_sector:
                errores.append(
                    "Debe seleccionar un sector para el personal fijo."
                )
            elif sectores is not None:
                sector_sel = next(
                    (
                        s
                        for s in sectores
                        if str(s.idSector) == id_sector
                    ),
                    None,
                )
                if sector_sel is None:
                    errores.append(
                        "El sector seleccionado no existe o está inactivo."
                    )

    return errores