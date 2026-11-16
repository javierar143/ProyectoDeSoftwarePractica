/**
 * Rutas generales del sistema.
 *
 * Incluye las pantallas que no pertenecen a un módulo operativo,
 * como la pantalla de mantenimiento.
 */
export const systemRoutes = [
  {
    path: '/maintenance',
    name: 'maintenance',
    component: () =>
      import('../../modules/system/views/MaintenanceView.vue'),
    meta: {
      requiresAuth: false,
    },
  },
]