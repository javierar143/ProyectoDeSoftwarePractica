import apiClient from '@/services/api/client'

/**
 * Obtiene la configuración general del sistema necesaria para pedidos.
 *
 * @returns {Promise<object>}
 */
export async function obtenerConfiguracionPedidos() {
  const response = await apiClient.get('/configuration')
  return response?.data ?? {}
}

/**
 * Busca el identificador numérico correspondiente al tipo de personal "Residente".
 *
 * @returns {Promise<number|null>}
 */
async function obtenerIdTipoResidente() {
  try {
    const response = await apiClient.get('/personnel-types')
    const tipos = Array.isArray(response?.data?.items)
      ? response.data.items
      : Array.isArray(response?.data)
        ? response.data
        : []

    const tipoResidente = tipos.find(
      (t) => String(t?.nombre ?? '').trim().toLowerCase() === 'residente',
    )

    if (!tipoResidente) return null
    const id = Number(tipoResidente.id ?? tipoResidente.idTipoPersonal)
    return Number.isNaN(id) ? null : id
  } catch {
    return null
  }
}

/**
 * Obtiene el personal activo del sector, los cupos del sector y los residentes activos.
 *
 * @param {number|string|null} idSector - Identificador del sector del Jefe de Servicio.
 * @returns {Promise<{ personalSector: Array, cuposSector: Array, residentes: Array }>}
 */
export async function obtenerDatosCargaPedido(idSector) {
  let personalSector = []
  let cuposSector = []

  if (idSector !== null && idSector !== undefined) {
    const [personalRes, cuposRes] = await Promise.all([
      apiClient.get(`/sectors/${idSector}/personnel`, {
        params: { estado: 'activos' },
      }),
      apiClient.get('/quotas', {
        params: { sector_id: idSector },
      }),
    ])

    personalSector = Array.isArray(personalRes?.data?.items)
      ? personalRes.data.items
      : Array.isArray(personalRes?.data)
        ? personalRes.data
        : []

    cuposSector = Array.isArray(cuposRes?.data?.items)
      ? cuposRes.data.items
      : Array.isArray(cuposRes?.data)
        ? cuposRes.data
        : []
  }

  const idTipoResidente = await obtenerIdTipoResidente()
  const residentesRes =
    idTipoResidente !== null
      ? await apiClient
          .get('/personnel', {
            params: {
              id_tipo_personal: idTipoResidente,
              estado: 'activos',
            },
          })
          .catch(() => null)
      : null

  const residentes = Array.isArray(residentesRes?.data?.items)
    ? residentesRes.data.items
    : Array.isArray(residentesRes?.data)
      ? residentesRes.data
      : []

  return {
    personalSector,
    cuposSector,
    residentes,
  }
}

/**
 * Envía un nuevo pedido de comidas para el sector del usuario autenticado.
 *
 * @param {object} payload - Datos del pedido a crear.
 * @returns {Promise<object>}
 */
export async function crearPedido(payload) {
  const response = await apiClient.post('/requests', payload)
  return response?.data ?? {}
}

/**
 * Lista los pedidos del sector según filtros y paginación.
 *
 * @param {object} params - Parámetros de consulta.
 * @returns {Promise<object>}
 */
export async function listarPedidosSector(params = {}) {
  const response = await apiClient.get('/requests', { params })
  return response?.data ?? {}
}

/**
 * Obtiene el detalle de un pedido por su ID.
 *
 * @param {number|string} requestId - ID del pedido.
 * @returns {Promise<object>}
 */
export async function obtenerPedido(requestId) {
  const response = await apiClient.get(`/requests/${requestId}`)
  return response?.data ?? {}
}

/**
 * Actualiza un pedido existente en estado confirmado.
 *
 * @param {number|string} requestId - ID del pedido.
 * @param {object} payload - Datos actualizados del pedido.
 * @returns {Promise<object>}
 */
export async function actualizarPedido(requestId, payload) {
  const response = await apiClient.put(`/requests/${requestId}`, payload)
  return response?.data ?? {}
}

/**
 * Elimina un pedido existente en estado confirmado.
 *
 * @param {number|string} requestId - ID del pedido.
 * @returns {Promise<void>}
 */
export async function eliminarPedido(requestId) {
  await apiClient.delete(`/requests/${requestId}`)
}
