
/**
 * Rutas del módulo Servicio de Alimentación.
 *
 * Incluye el acceso a los pedidos pendientes de autorización del día.
 */
export const servicioAlimentacionRoutes = [
  {
    path: '/inicio/servicio-alimentacion',
    name: 'inicio-servicio-alimentacion',

    // TEMPORAL: eliminar esta vista y su importación
    // cuando se implemente la pantalla definitiva.
    component: () => import('./temporalServicioAlimentacion.vue'),

    meta: {
      requiresAuth: true,
      roles: ['servicioAlimentacion'],
    },
  },
]
