import apiClient from '@/services/api/client'

/**
 * Limpia los parámetros vacíos o nulos antes de enviarlos como query params.
 */
function limpiarFiltros(filtros = {}) {
  const params = {}
  Object.entries(filtros).forEach(([clave, valor]) => {
    if (valor !== null && valor !== undefined && valor !== '') {
      params[clave] = valor
    }
  })
  return params
}

/**
 * Obtiene el resumen de autorizaciones (pedidas regulares, excepciones, residentes, autorizadas y desglose).
 */
export async function obtenerResumenAutorizaciones(filtros = {}) {
  const { data } = await apiClient.get('/summaries/authorizations', {
    params: limpiarFiltros(filtros),
  })
  return data
}

/**
 * Obtiene el resumen de entregas (autorizadas vs entregadas, diferencia, desglose y agrupaciones).
 */
export async function obtenerResumenEntregas(filtros = {}) {
  const { data } = await apiClient.get('/summaries/deliveries', {
    params: limpiarFiltros(filtros),
  })
  return data
}

/**
 * Obtiene el resumen de pedidos agrupado por día, semana, mes, sector, comida o tipo de menú.
 */
export async function obtenerResumenPedidos(filtros = {}) {
  const { data } = await apiClient.get('/summaries/requests', {
    params: limpiarFiltros(filtros),
  })
  return data
}

/**
 * Descarga el reporte en formato CSV directamente desde el backend respetando los filtros activos.
 * tipo: 'authorizations' | 'deliveries'
 */
export async function exportarResumenCsv(tipo = 'authorizations', filtros = {}) {
  const endpoint =
    tipo === 'deliveries'
      ? '/summaries/deliveries'
      : '/summaries/authorizations'

  const response = await apiClient.get(endpoint, {
    params: {
      ...limpiarFiltros(filtros),
      formato: 'csv',
    },
    responseType: 'blob',
  })

  const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute(
    'download',
    tipo === 'deliveries'
      ? 'reporte_entregas.csv'
      : 'reporte_autorizaciones.csv'
  )
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

/**
 * Obtiene el catálogo de tipos de menú para poblar el filtro.
 */
export async function obtenerTiposMenu() {
  const { data } = await apiClient.get('/menu-types')
  return data
}

/**
 * Obtiene el listado de sectores (incluyendo inactivos para reportes históricos).
 */
export async function obtenerSectores() {
  const { data } = await apiClient.get('/sectors', {
    params: { estado: 'todos' },
  })
  return Array.isArray(data) ? data : (data.items ?? data.sectores ?? [])
}