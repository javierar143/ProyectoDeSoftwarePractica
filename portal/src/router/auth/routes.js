/**
 * Rutas del módulo de autenticación.
 *
 * Incluye el inicio de sesión y la pantalla de acceso denegado.
 */
export const authRoutes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../../modules/auth/views/LoginView.vue'),
    meta: {
      guestOnly: true,
    },
  },
  {
    path: '/access-denied',
    name: 'access-denied',
    component: () =>
      import('../../modules/auth/views/AccessDeniedView.vue'),
  },
]