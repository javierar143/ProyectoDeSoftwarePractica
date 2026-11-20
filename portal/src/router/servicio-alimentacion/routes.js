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
    path: '/servicio-alimentacion/cupos',
    name: 'servicio-alimentacion-cupos',
    component: () => import('@/modules/cupos/views/CuposView.vue'),
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
]

export default servicioAlimentacionRoutes
