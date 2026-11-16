/**
 * Rutas del módulo Servicio de Alimentación.
 *
 * Incluye el acceso a los pedidos pendientes de autorización del día.
 */
export const servicioAlimentacionRoutes = [
  {
    path: '/inicio/servicio-alimentacion',
    name: 'inicio-servicio-alimentacion',
    meta: {
      requiresAuth: true,
      roles: ['servicioAlimentacion'],
    },
  },
]