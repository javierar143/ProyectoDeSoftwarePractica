
/**
 * Rutas del módulo Sector Comedor.
 *
 * Incluye el acceso a la funcionalidad de búsqueda
 * del modo kiosco.
 */
export const sectorComedorRoutes = [
  {
    path: '/inicio/sector-comedor',
    name: 'inicio-sector-comedor',

    // TEMPORAL: eliminar esta vista y su importación
    // cuando se implemente la pantalla definitiva.
    component: () => import('./temporalSectorComedor.vue'),

    meta: {
      requiresAuth: true,
      roles: ['sectorComedor'],
    },
  },
]
