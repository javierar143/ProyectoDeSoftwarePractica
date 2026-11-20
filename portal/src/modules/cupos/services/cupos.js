import apiClient from '@/services/api/client'

/**
 * Lista los cupos vigentes con filtros por sector, tipo de comida, orden y paginación.
 *
 * @param {object} params
 * @returns {Promise<{ items: Array, total: number, page: number, per_page: number }>}
 */
export async function listarCupos(params = {}) {
  const response = await apiClient.get('/quotas', { params })
  const data = response?.data ?? {}
  return {
    items: Array.isArray(data.items) ? data.items : Array.isArray(data) ? data : [],
    total: Number(data.total ?? (Array.isArray(data.items) ? data.items.length : 0)),
    page: Number(data.page ?? params.page ?? 1),
    per_page: Number(data.per_page ?? 25),
  }
}

/**
 * Crea un nuevo cupo vigente para un sector y tipo de comida.
 *
 * @param {{ idSector: number, idTipoComida: number, cantComensales: number }} payload
 * @returns {Promise<object>}
 */
export async function crearCupo(payload) {
  const response = await apiClient.post('/quotas', payload)
  return response?.data ?? {}
}

/**
 * Modifica un cupo existente (aplica a pedidos posteriores al cambio).
 *
 * @param {number|string} quotaId
 * @param {{ idSector: number, idTipoComida: number, cantComensales: number }} payload
 * @returns {Promise<object>}
 */
export async function actualizarCupo(quotaId, payload) {
  const response = await apiClient.put(`/quotas/${quotaId}`, payload)
  return response?.data ?? {}
}

/**
 * Da de baja lógica un cupo existente.
 *
 * @param {number|string} quotaId
 * @returns {Promise<void>}
 */
export async function eliminarCupo(quotaId) {
  await apiClient.delete(`/quotas/${quotaId}`)
}

/**
 * Obtiene sectores activos (y todos opcionalmente) desde /api/sectors.
 *
 * @param {'activo'|'todos'} estado
 * @returns {Promise<Array>}
 */
export async function listarSectoresCupos(estado = 'activo') {
  const response = await apiClient.get('/sectors', { params: { estado } })
  if (Array.isArray(response?.data)) return response.data
  if (Array.isArray(response?.data?.items)) return response.data.items
  return []
}
