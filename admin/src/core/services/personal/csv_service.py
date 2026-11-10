"""Servicio para la importación masiva de personal mediante CSV."""

import csv
import io
from flask import current_app
from src.core.services.personal import personal as service_personal
from src.web.validators.personal.personal import validar_datos_personal

def procesar_csv(contenido_csv: str, user_id: int | None = None) -> dict:
    """Parsea el CSV, valida cada fila e intenta crear los registros en BD."""
    stream = io.StringIO(contenido_csv, newline=None)
    csv_reader = csv.DictReader(stream)

    # Traigo catalogos y armo diccionarios para traducir nombres a IDs
    tipos_personal = service_personal.get_tipos_personal()
    tipos_menu = service_personal.get_tipos_menu()
    sectores = service_personal.get_sectores()

    map_tipos_personal = {t.nombre.strip().lower(): t.idTipoPersonal for t in tipos_personal}
    map_tipos_menu = {m.nombre.strip().lower(): m.idTipoMenu for m in tipos_menu}
    map_sectores = {s.nombre.strip().lower(): s.idSector for s in sectores}

    resultados = {
        "total": 0,
        "exitosos": 0,
        "fallidos": 0,
        "detalles_errores": [],
        "detalles_exitosos": []
    }

    for fila_num, fila in enumerate(csv_reader, start=2):
        resultados["total"] += 1
        
        # Limpio espacios y paso a minusculas
        fila_limpia = {str(k).strip().lower(): str(v).strip() for k, v in fila.items() if k is not None}

        nombre_tipo = fila_limpia.get("tipo_personal", "").lower()
        nombre_menu = fila_limpia.get("tipo_menu", "").lower()
        nombre_sector = fila_limpia.get("sector", "").lower()

        # Traduzco nombres a IDs
        id_tipo_pers = str(map_tipos_personal.get(nombre_tipo, ""))
        id_tipo_menu = str(map_tipos_menu.get(nombre_menu, ""))
        id_sec = str(map_sectores.get(nombre_sector, "")) if nombre_sector else ""

        datos_validacion = {
            "dni": fila_limpia.get("dni", ""),
            "nombre": fila_limpia.get("nombre", ""),
            "apellido": fila_limpia.get("apellido", ""),
            "idTipoPersonal": id_tipo_pers,
            "idTipoMenu": id_tipo_menu,
            "idSector": id_sec
        }

        # Valido los datos de la fila usando la misma logica del formulario web
        errores_fila = validar_datos_personal(datos_validacion, tipos_personal)

        if errores_fila:
            resultados["fallidos"] += 1
            resultados["detalles_errores"].append({
                "fila": fila_num,
                "persona": f"{datos_validacion['nombre']} {datos_validacion['apellido']} (DNI: {datos_validacion['dni']})",
                "errores": errores_fila
            })
            continue

        try:
            # si pasa, intento crear la persona pasandole el user_id (para forzar sector si es Jefe)
            persona_creada = service_personal.create(
                dni=datos_validacion["dni"],
                nombre=datos_validacion["nombre"],
                apellido=datos_validacion["apellido"],
                id_tipo_personal=int(id_tipo_pers),
                id_tipo_menu=int(id_tipo_menu),
                id_sector=int(id_sec) if id_sec else None,
                user_id=user_id
            )
            
            if persona_creada is None:
                resultados["fallidos"] += 1
                resultados["detalles_errores"].append({
                    "fila": fila_num,
                    "persona": f"{datos_validacion['nombre']} {datos_validacion['apellido']} (DNI: {datos_validacion['dni']})",
                    "errores": ["Ya existe una persona registrada con este DNI."]
                })
            else:
                resultados["exitosos"] += 1
                resultados["detalles_exitosos"].append(
                    f"{datos_validacion['nombre']} {datos_validacion['apellido']} (DNI: {datos_validacion['dni']})"
                )
                
        except Exception as e:
            current_app.logger.error(f"Error inesperado al importar CSV DNI {datos_validacion['dni']}: {str(e)}")
            resultados["fallidos"] += 1
            resultados["detalles_errores"].append({
                "fila": fila_num,
                "persona": f"DNI: {datos_validacion['dni']}",
                "errores": ["Error interno al guardar en la base de datos."]
            })

    current_app.logger.info(f"Importación CSV finalizada: {resultados['exitosos']} exitosos, {resultados['fallidos']} rechazados.")
    return resultados