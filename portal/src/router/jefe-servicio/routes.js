
/**
 * Rutas del módulo Jefe de Servicio.
 *
 * Incluye el acceso a la funcionalidad de carga de pedidos
 * correspondientes a su sector.
 */
export const jefeServicioRoutes = [
  {
    path: '/inicio/jefe-servicio',
    name: 'inicio-jefe-servicio',

    // TEMPORAL: eliminar esta vista y su importación
    // cuando se implemente la pantalla definitiva.
    component: () => import('./temporalJefeServicio.vue'),

    meta: {
      requiresAuth: true,
      roles: ['jefeServicio'],
    },
  },
]
