/**
 * Normaliza los errores recibidos desde la API.
 *
 * Conserva los mensajes del backend y proporciona información
 * adicional para que cada vista pueda decidir cómo mostrarlos.
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

  const message =
    backendMessage ||
    (!error.response
      ? 'No se pudo conectar con el servidor.'
      : 'Ocurrió un error inesperado. Intentá nuevamente.')

  return {
    status,
    message,
    fieldErrors: data.field_errors ?? data.errors ?? null,
    isNetworkError: !error.response,
    isConflict: status === 409,
  }
}