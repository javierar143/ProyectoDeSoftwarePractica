import { useAuthStore } from '@/stores/auth'
import { getRoleHomeRoute } from '../navigation'

/**
 * Registra las reglas globales de autenticación y autorización.
 *
 * @param {import('vue-router').Router} router - Instancia del router.
 */
export function registerNavigationGuard(router) {
  router.beforeEach(async (to) => {
    const authStore = useAuthStore()

    // Recupera la sesión si existe un token pero aún no se cargó el usuario.
    if (authStore.token && !authStore.user) {
      await authStore.restoreSession()
    }

    // Todas las rutas requieren autenticación, excepto las destinadas a invitados.
    const requiresAuth = to.meta.requiresAuth ?? !to.meta.guestOnly

    if (requiresAuth && !authStore.isAuthenticated) {
      return {
        name: 'login',
        query: { redirect: to.fullPath },
      }
    }

    // Verifica el rol cuando la ruta declara roles autorizados.
    if (to.meta.roles) {
      const role = authStore.operationalRoleKey

      if (!role || !to.meta.roles.includes(role)) {
        return { name: 'access-denied' }
      }
    }

    // Evita que un usuario autenticado vuelva al inicio de sesión.
    if (to.meta.guestOnly && authStore.isAuthenticated) {
      const destination = getRoleHomeRoute(authStore.operationalRoleKey)

      return destination
        ? { name: destination }
        : { name: 'access-denied' }
    }
  })
}