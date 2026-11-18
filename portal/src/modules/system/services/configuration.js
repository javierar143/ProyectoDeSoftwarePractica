import apiClient from '@/services/api/client'

export const MAINTENANCE_RETURN_ROUTE_KEY = 'maintenanceReturnRoute'

export const MAINTENANCE_MESSAGE_DEFAULT =
  'La aplicación se encuentra temporalmente en mantenimiento. Estamos trabajando para restablecer el servicio. Cuando finalice el mantenimiento, la aplicación volverá a estar disponible automáticamente. No necesitás realizar ninguna acción.'

export async function getPublicConfiguration() {
  const { data } = await apiClient.get('/configuration')
  return data
}

export function saveMaintenanceReturnRoute(fullPath) {
  try {
    if (fullPath && fullPath !== '/maintenance') {
      sessionStorage.setItem(MAINTENANCE_RETURN_ROUTE_KEY, fullPath)
    }
  } catch {
    // La recuperación usará la ruta inicial del usuario como alternativa.
  }
}

export function getMaintenanceReturnRoute() {
  try {
    return sessionStorage.getItem(MAINTENANCE_RETURN_ROUTE_KEY)
  } catch {
    return null
  }
}

export function clearMaintenanceReturnRoute() {
  try {
    sessionStorage.removeItem(MAINTENANCE_RETURN_ROUTE_KEY)
  } catch {
    // No impide restaurar la sesión si el almacenamiento no está disponible.
  }
}
