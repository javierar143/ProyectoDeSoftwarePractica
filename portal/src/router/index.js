import { createRouter, createWebHistory } from 'vue-router'

import { authRoutes } from './auth/routes'
import { registerNavigationGuard } from './guards/navigation-guard'
import { jefeServicioRoutes } from './jefe-servicio/routes'
import { servicioAlimentacionRoutes } from './servicio-alimentacion/routes'
import { sectorComedorRoutes } from './sector-comedor/routes'
import { systemRoutes } from './system/routes'

/**
 * Reúne las rutas declaradas por los distintos módulos del portal.
 *
 * Auth y system quedan fuera del layout.
 * Las rutas operativas se anidan bajo AppLayout para mostrar
 * top bar + navbar + contenido.
 */
const routes = [
  {
    path: '/',
    redirect: { name: 'login' },
  },
  ...authRoutes,
  ...systemRoutes,
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    children: [
      ...jefeServicioRoutes,
      ...servicioAlimentacionRoutes,
      ...sectorComedorRoutes,
    ],
  },
]

/**
 * Crea y configura el router principal de la aplicación.
 */
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Registra las reglas globales de navegación.
registerNavigationGuard(router)

export default router