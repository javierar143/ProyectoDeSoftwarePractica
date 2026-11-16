
import apiClient from '@/services/api/client'

/**
 * Autentica al usuario mediante email y contraseña.
 */
export async function login(email, password) {
  const response = await apiClient.post('/auth/login', {
    email,
    password,
  })

  return response.data
}

/**
 * Obtiene los datos del usuario autenticado.
 */
export async function getCurrentUser() {
  const response = await apiClient.get('/auth/me')

  return response.data
}

/**
 * Obtiene los identificadores de los roles operativos.
 */
export async function getOperationalRoles() {
  const response = await apiClient.get('/roles/operational')

  return response.data
}

/**
 * Solicita un nuevo access token utilizando la cookie refresh.
 */
export async function refreshAccessToken() {
  const response = await apiClient.post('/auth/refresh')
  return response.data
}

/**
 * Cierra la sesión del usuario en el backend.
 */
export async function logout() {
  const response = await apiClient.post('/auth/logout')
  return response.data
}
