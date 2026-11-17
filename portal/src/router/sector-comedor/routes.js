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
    component: () => import('@/modules/entregas/views/EntregasView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['sectorComedor'],
    },
  },
]