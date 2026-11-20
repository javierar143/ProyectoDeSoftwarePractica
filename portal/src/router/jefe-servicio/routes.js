/**
 * Rutas del módulo Jefe de Servicio.
 *
 * Incluye el acceso a la funcionalidad de carga, consulta y edición
 * de pedidos y gestión de personal correspondientes a su sector.
 */
export const jefeServicioRoutes = [
  {
    path: '/inicio/jefe-servicio',
    name: 'inicio-jefe-servicio',
    // Reemplazar por la vista definitiva del panel o listado de pedidos al terminar
    component: () => import('./temporalJefeServicio.vue'),
    meta: {
      requiresAuth: true,
      roles: ['jefeServicio'],
    },
  },
  {
    path: '/jefe-servicio/pedidos/nuevo',
    name: 'jefe-servicio-pedidos-nuevo',
    component: () => import('@/modules/pedidos/views/CrearPedidoView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['jefeServicio'],
    },
  },
  {
    path: '/jefe-servicio/personal',
    name: 'jefe-servicio-personal',
    component: () => import('@/modules/personal/views/PersonalView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['jefeServicio'],
    },
  },
]
