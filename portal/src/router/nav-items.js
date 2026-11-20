/**
 * Links del navbar del portal, agrupados por rol operativo.
 *
 * Solo incluye rutas que ya existen en el router post-pull.
 * Sector Comedor no tiene ítems: el kiosco usa top bar mínima.
 */
export const NAV_ITEMS_BY_ROLE = {
  jefeServicio: [
    { name: 'inicio-jefe-servicio', label: 'Pedidos' },
    { name: 'jefe-servicio-pedidos-nuevo', label: 'Nuevo pedido' },
    { name: 'jefe-servicio-personal', label: 'Personal' },
  ],
  servicioAlimentacion: [
    { name: 'inicio-servicio-alimentacion', label: 'Autorizaciones' },
    { name: 'servicio-alimentacion-cupos', label: 'Cupos' },
    { name: 'servicio-alimentacion-reportes', label: 'Reportes' },
  ],
  sectorComedor: [],
}

/**
 * Devuelve los links visibles para el rol actual.
 *
 * @param {string|null} roleKey
 * @returns {{ name: string, label: string }[]}
 */
export function getNavItemsForRole(roleKey) {
  if (!roleKey) {
    return []
  }

  return NAV_ITEMS_BY_ROLE[roleKey] ?? []
}