import apiClient from '@/services/api/client'

function limpiarParametros(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
  )
}

export async function buscarComidasAutorizadas(params = {}) {
  const { data } = await apiClient.get('/authorized-meals', {
    params: limpiarParametros(params),
  })
  return data
}

export async function registrarEntrega(payload) {
  const { data } = await apiClient.post('/deliveries', payload)
  return data
}

export async function listarEntregasTurno(params = {}) {
  const { data } = await apiClient.get('/deliveries', {
    params: limpiarParametros(params),
  })
  return data
}

export async function obtenerResumenEntregasDia(params = {}) {
  const { data } = await apiClient.get('/deliveries/summary', {
    params: limpiarParametros(params),
  })
  return data
}

export async function listarSectoresActivos() {
  const { data } = await apiClient.get('/sectors', {
    params: { estado: 'activo' },
  })
  return data
}

export async function obtenerConfiguracionHorarios() {
  const { data } = await apiClient.get('/configuration')
  return data
}

export async function chequearConexionApi(fechaHoy) {
  try {
    await apiClient.get('/deliveries/summary', {
      params: { fecha: fechaHoy },
    })
    return true
  } catch (err) {
    return Boolean(err?.status || err?.response?.status)
  }
}

export async function cerrarSesionApi() {
  try {
    await apiClient.post('/auth/logout')
  } catch {

  }
}