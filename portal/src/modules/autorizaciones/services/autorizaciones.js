import apiClient from '@/services/api/client'

function normalizarError(err) {
  const status = err?.response?.status ?? null
  const mensaje =
    err?.response?.data?.message ||
    err?.response?.data?.error ||
    err?.message ||
    'Error al comunicarse con el servidor.'

  return {
    status,
    message: mensaje,
    isConflict: status === 409,
    isNotFound: status === 404,
  }
}

export async function listarPedidosAutorizacion(params = {}) {
  try {
    const response = await apiClient.get('authorizations', { params })
    return response.data
  } catch (err) {
    throw normalizarError(err)
  }
}

export async function obtenerDetalleAutorizacion(requestId) {
  try {
    const response = await apiClient.get(`authorizations/${requestId}`)
    return response.data
  } catch (err) {
    throw normalizarError(err)
  }
}

export async function guardarAutorizacionPedido(requestId, payload) {
  try {
    const response = await apiClient.put(`authorizations/${requestId}`, payload)
    return response.data
  } catch (err) {
    throw normalizarError(err)
  }
}

export async function rechazarPedidoCompleto(requestId, payload) {
  try {
    const response = await apiClient.post(`authorizations/${requestId}/reject`, payload)
    return response.data
  } catch (err) {
    throw normalizarError(err)
  }
}