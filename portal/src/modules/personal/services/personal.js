import apiClient from '@/services/api/client'

function limpiarParametros(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
  )
}

export async function listarPersonal(params = {}) {
  const { data } = await apiClient.get('/personnel', {
    params: limpiarParametros(params),
  })
  return data
}

export async function obtenerPersona(idPersona) {
  const { data } = await apiClient.get(`/personnel/${idPersona}`)
  return data
}

export async function listarPersonalDeSector(idSector, params = {}) {
  const { data } = await apiClient.get(`/sectors/${idSector}/personnel`, {
    params: limpiarParametros(params),
  })
  return data
}

export async function crearPersona(payload) {
  const { data } = await apiClient.post('/personnel', payload)
  return data
}

export async function modificarPersona(idPersona, payload) {
  const { data } = await apiClient.put(`/personnel/${idPersona}`, payload)
  return data
}

export async function eliminarPersona(idPersona) {
  const { data } = await apiClient.delete(`/personnel/${idPersona}`)
  return data
}

export async function listarTiposMenu() {
  const { data } = await apiClient.get('/menu-types')
  return data
}

export async function listarTiposPersonal() {
  const { data } = await apiClient.get('/personnel-types')
  return data
}

export async function listarSectores(estado = 'activos') {
  const { data } = await apiClient.get('/sectors', {
    params: { estado },
  })
  return data
}