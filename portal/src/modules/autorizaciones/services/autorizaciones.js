import apiClient from '@/services/api/client'

function limpiarParametros(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
  )
}

function descargarBlobComoArchivo(blobData, nombreArchivo) {
  const blob =
    blobData instanceof Blob
      ? blobData
      : new Blob([blobData], { type: 'text/csv;charset=utf-8;' })
  const blobUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = blobUrl
  link.setAttribute('download', nombreArchivo)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(blobUrl)
}

export async function listarPedidosAutorizacion(params = {}) {
  const { data } = await apiClient.get('/authorizations', {
    params: limpiarParametros(params),
  })
  return data
}

export async function listarFechasAutorizacion(params = {}) {
  const { data } = await apiClient.get('/authorization-dates', {
    params: limpiarParametros(params),
  })
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

export async function listarSectoresApi(estado = 'todos') {
  const { data } = await apiClient.get('/sectors', {
    params: { estado },
  })
  return data
}

export async function obtenerResumenAutorizaciones(params = {}) {
  const { data } = await apiClient.get('/summaries/authorizations', {
    params: limpiarParametros(params),
  })
  return data
}

export async function exportarPersonasAutorizadasCsv(params = {}) {
  const { data } = await apiClient.get('/authorized-meals', {
    params: limpiarParametros({ ...params, formato: 'csv' }),
    responseType: 'blob',
  })
  descargarBlobComoArchivo(data, 'personas_autorizadas.csv')
}

export async function exportarTotalesAutorizacionesCsv(params = {}) {
  const { data } = await apiClient.get('/summaries/authorizations', {
    params: limpiarParametros({ ...params, formato: 'csv' }),
    responseType: 'blob',
  })
  descargarBlobComoArchivo(data, 'totales_autorizaciones.csv')
}