/**
 * Rutas del módulo Servicio de Alimentación.
 *
 * Incluye el acceso a los pedidos pendientes de autorización del día
 * y una vista temporal para probar autorizar o rechazar pedidos.
 */

export const servicioAlimentacionRoutes = [
  {
    path: '/inicio/servicio-alimentacion',
    name: 'inicio-servicio-alimentacion',
    component: () => import('@/modules/autorizaciones/views/AutorizacionesView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['servicioAlimentacion'],
    },
  },
  {
    // TEMPORAL (BORRAR CUANDO ESTRE CRUD DE PEDIDOS): para crear pedidos de prueba y luego autorizarlos/rechazarlos
    path: '/temporal/crear-pedido',
    name: 'temporal-crear-pedido',
    component: () => import('@/modules/pedidos/views/CrearPedidoView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['jefeServicio'],
    },
  },
  {
    path: '/servicio-alimentacion/reportes',
    name: 'servicio-alimentacion-reportes',
    component: () => import('@/modules/reportes/views/ReportesView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['servicioAlimentacion'], 
    },
  },
]

export default servicioAlimentacionRoutes