/**
 * Mapea cada rol operativo con su ruta inicial.
 */
const ROLE_HOME_ROUTES = {
  jefeServicio: 'inicio-jefe-servicio',
  servicioAlimentacion: 'inicio-servicio-alimentacion',
  sectorComedor: 'inicio-sector-comedor',
}

/**
 * Obtiene el nombre de la ruta inicial correspondiente al rol.
 *
 * @param {string|null} roleKey - Clave del rol operativo.
 * @returns {string|null} Nombre de la ruta inicial o null si no corresponde.
 */
export function getRoleHomeRoute(roleKey) {
  return ROLE_HOME_ROUTES[roleKey] ?? null
}