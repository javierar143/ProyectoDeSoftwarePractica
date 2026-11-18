/**
 * Normaliza los errores recibidos desde la API.
 *
 * Conserva los mensajes del backend para errores de negocio,
 * pero evita exponer detalles internos ante errores de servidor.
 *
 * @param {object} error - Error devuelto por Axios.
 * @returns {object} Información normalizada del error.
 */
export function normalizeApiError(error) {
  const status = error.response?.status ?? null
  const data = error.response?.data ?? {}

  const backendMessage =
    data.error ||
    data.description ||
    data.message

  const isNetworkError = !error.response
  const isServerError = status >= 500
  const requestMethod = error.config?.method?.toLowerCase()
  const isWriteOperation = ['post', 'put', 'patch', 'delete'].includes(requestMethod)

  let message

  if (isNetworkError) {
    message = 'No se pudo conectar con el servidor. Verificá tu conexión.'
  } else if (status === 503) {
    message = 'El sistema se encuentra en mantenimiento.'
  } else if (isServerError) {
    message = 'Ocurrió un error en el servidor. Intentá nuevamente.'
  } else if (status === 401) {
    message = backendMessage || 'Tu sesión no está autorizada. Volvé a iniciar sesión.'
  } else if (status === 403) {
    message = backendMessage || 'No tenés permisos para realizar esta operación.'
  } else if (status === 404) {
    message = backendMessage || 'No se encontró el recurso solicitado.'
  } else if (status === 409) {
    message = backendMessage || 'El recurso cambió y la operación entró en conflicto. Actualizá los datos.'
  } else if (status === 400) {
    message = backendMessage || 'Los datos enviados no son válidos.'
  } else {
    message = backendMessage || 'Ocurrió un error inesperado.'
  }

  const possibleFieldErrors = data.field_errors ?? data.errors

  const fieldErrors =
    possibleFieldErrors &&
    typeof possibleFieldErrors === 'object' &&
    !Array.isArray(possibleFieldErrors)
      ? possibleFieldErrors
      : null

  return {
    status,
    message,
    fieldErrors,
    isNetworkError,
    isForbidden: status === 403,
    isNotFound: status === 404,
    isConflict: status === 409,
    isServerError,
    canRetry: !isWriteOperation && (isNetworkError || (isServerError && status !== 503)),
  }
}
