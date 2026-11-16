/**
 * Registra el tratamiento global de respuestas 503.
 *
 * Cuando la API informa que el servicio no está disponible,
 * redirige a la pantalla de mantenimiento.
 *
 * @param {import('axios').AxiosInstance} apiClient - Cliente HTTP.
 * @param {import('vue-router').Router} router - Router de la aplicación.
 */
export function registerMaintenanceInterceptor(apiClient, router) {
  apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response?.status === 503) {
        if (router.currentRoute.value.name !== 'maintenance') {
          await router.replace({ name: 'maintenance' })
        }
      }

      return Promise.reject(error)
    },
  )
}