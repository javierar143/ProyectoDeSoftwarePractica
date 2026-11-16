/**
 * Endpoints que gestionan directamente la autenticación.
 * Sus errores son tratados por el store correspondiente.
 */
const AUTH_ENDPOINTS = [
  '/auth/login',
  '/auth/me',
  '/roles/operational',
  '/auth/refresh',
  '/auth/logout',
]

let restoreSessionPromise = null

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
 * Intenta recuperar la sesión y repetir la petición original.
 * Si la sesión no puede recuperarse, la elimina y redirige al login.
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

      if (error.response?.status !== 401 || !originalRequest) {
        return Promise.reject(error)
      }

      if (isAuthEndpoint(originalRequest.url)) {
        return Promise.reject(error)
      }

      if (originalRequest._retry) {
        authStore.clearSession()
        await router.replace({
          name: 'login',
          query: { redirect: router.currentRoute.value.fullPath },
        })

        return Promise.reject(error)
      }

      originalRequest._retry = true

      try {
        if (!restoreSessionPromise) {
          restoreSessionPromise = authStore.restoreSession().finally(() => {
            restoreSessionPromise = null
          })
        }

        const sessionRestored = await restoreSessionPromise

        if (!sessionRestored) {
          authStore.clearSession()
          await router.replace({
            name: 'login',
            query: { redirect: router.currentRoute.value.fullPath },
          })

          return Promise.reject(error)
        }

        return apiClient(originalRequest)
      } catch (restoreError) {
        authStore.clearSession()
        await router.replace({
          name: 'login',
          query: { redirect: router.currentRoute.value.fullPath },
        })

        return Promise.reject(restoreError)
      }
    },
  )
}