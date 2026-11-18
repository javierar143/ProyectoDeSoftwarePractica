
import { useAuthStore } from '@/stores/auth'
import { useMaintenanceStore } from '@/stores/maintenance'
import { getPublicConfiguration } from '@/modules/system/services/configuration'
import { getRoleHomeRoute } from '../navigation'

/**
 * Registra las reglas globales de autenticación y autorización.
 *
 * @param {import('vue-router').Router} router - Instancia del router.
 */
export function registerNavigationGuard(router) {
  router.beforeEach(async (to) => {
    const authStore = useAuthStore()
    const maintenanceStore = useMaintenanceStore()

    if (to.name === 'maintenance') return true
    if (maintenanceStore.isTransitioning) return false

    const leavingMaintenance = router.currentRoute.value.name === 'maintenance'

    try {
      const configuration = await getPublicConfiguration()
      if (configuration.modo_mantenimiento) {
        maintenanceStore.beginTransition(router, to.fullPath)
        return false
      }
      if (leavingMaintenance) maintenanceStore.finishMaintenance()
    } catch (error) {
      if (error.response?.status === 503) {
        maintenanceStore.beginTransition(router, to.fullPath)
        return false
      }
      if (leavingMaintenance) return false
      // Una falla al consultar configuración no invalida una sesión ni bloquea el acceso.
    }

    // Determina si la ruta requiere autenticación.
    const requiresAuth = to.meta.requiresAuth ?? !to.meta.guestOnly

    // Verifica la sesión en todas las rutas protegidas
    // y también al intentar ingresar nuevamente al login.
    const shouldVerifySession = requiresAuth || to.meta.guestOnly

    if (shouldVerifySession && authStore.token) {
      const sessionRestored = await authStore.restoreSession()

      if (!sessionRestored) {
        // Si el backend respondió 401, restoreSession
        // ya eliminó la sesión local.
        if (!authStore.token) {
          if (to.meta.guestOnly) {
            return true
          }

          return {
            name: 'login',
            query: { redirect: to.fullPath },
          }
        }

        // Ante errores de red o servidor no se considera
        // inválida la sesión, pero se cancela la navegación protegida.
        return to.meta.guestOnly ? true : false
      }
    }

    // Comprueba que exista una sesión válida.
    if (requiresAuth && !authStore.isAuthenticated) {
      return {
        name: 'login',
        query: { redirect: to.fullPath },
      }
    }

    // Verifica que el rol del usuario tenga acceso a la ruta.
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
