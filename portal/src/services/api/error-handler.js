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

  let message

  if (isNetworkError) {
    message = 'No se pudo conectar con el servidor. Verificá tu conexión.'
  } else if (status === 503) {
    message = 'El sistema se encuentra en mantenimiento.'
  } else if (isServerError) {
    message = 'Ocurrió un error en el servidor. Intentá nuevamente.'
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
    canRetry: isNetworkError || isServerError,
  }
}