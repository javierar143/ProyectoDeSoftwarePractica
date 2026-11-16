import apiClient from '@/services/api/client'

export async function listarPedidosAutorizacion(params = {}) {
  const { data } = await apiClient.get('/authorizations', { params })
  return data
}

export async function obtenerDetalleAutorizacion(idPedido) {
  const { data } = await apiClient.get(`/authorizations/${idPedido}`)
  return data
}

export async function guardarAutorizacionPedido(idPedido, payload) {
  const { data } = await apiClient.put(`/authorizations/${idPedido}`, payload)
  return data
}

export async function rechazarPedidoCompleto(idPedido, payload) {
  const { data } = await apiClient.post(`/authorizations/${idPedido}/reject`, payload)
  return data
}

export async function listarFechasAutorizacion(params = {}) {
  const { data } = await apiClient.get('/authorization-dates', { params })
  return data
}

export async function listarSectoresApi(estado = 'todos') {
  const { data } = await apiClient.get('/sectors', { params: { estado } })
  return data
}