/**
 * Endpoints que gestionan directamente la autenticación.
 * Sus errores son tratados por el store correspondiente.
 */
const AUTH_ENDPOINTS = [
  '/auth/login',
  '/auth/google',
  '/auth/me',
  '/roles/operational',
  '/auth/refresh',
  '/auth/logout',
]

/**
 * Determina si una petición corresponde a un endpoint de autenticación.
 *
 * @param {string} url - URL de la petición.
 * @returns {boolean} Indica si es un endpoint de autenticación.
 */
function isAuthEndpoint(url = '') {
  return AUTH_ENDPOINTS.some((endpoint) => url.includes(endpoint))
}

/**
 * Registra el tratamiento global de respuestas 401.
 *
 * Ante un 401 de una operación protegida, elimina la sesión local
 * y redirige al login conservando la ruta actual.
 *
 * @param {import('axios').AxiosInstance} apiClient - Cliente HTTP.
 * @param {object} authStore - Store de autenticación.
 * @param {import('vue-router').Router} router - Router de la aplicación.
 */
export function registerAuthResponseInterceptor(
  apiClient,
  authStore,
  router,
) {
  apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config

      if (
        error.response?.status !== 401 ||
        !originalRequest ||
        isAuthEndpoint(originalRequest.url)
      ) {
        return Promise.reject(error)
      }

      const currentRoute = router.currentRoute.value
      const redirect = currentRoute.fullPath

      authStore.clearSession()

      if (currentRoute.name !== 'login') {
        await router.replace({
          name: 'login',
          query: { redirect },
        })
      }

      return Promise.reject(error)
    },
  )
}
