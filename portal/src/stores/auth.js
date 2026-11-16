
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  getCurrentUser,
  getOperationalRoles,
  refreshAccessToken,
  logout as logoutRequest,
} from '@/modules/auth/services/auth'

/**
 * Centraliza el estado de autenticación del portal.
 */
export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token'))
  const user = ref(null)
  const operationalRoles = ref(null)

  const isAuthenticated = computed(
    () => Boolean(token.value && user.value),
  )

  const operationalRoleKey = computed(() => {
    if (!user.value || !operationalRoles.value) {
      return null
    }

    const matchingRole = Object.entries(
      operationalRoles.value,
    ).find(
      ([, roleId]) => roleId === user.value.idRol,
    )

    return matchingRole?.[0] ?? null
  })

  /**
   * Guarda el access token en el almacenamiento persistente.
   */
  function setToken(accessToken) {
    token.value = accessToken
    localStorage.setItem('token', accessToken)
  }

  /**
   * Actualiza los datos del usuario autenticado.
   */
  function setUser(userData) {
    user.value = userData
  }

  /**
   * Actualiza los identificadores de roles obtenidos de la API.
   */
  function setOperationalRoles(roles) {
    operationalRoles.value = roles
  }

  /**
   * Elimina los datos locales de autenticación.
   */
  function clearSession() {
    token.value = null
    user.value = null
    operationalRoles.value = null

    localStorage.removeItem('token')
  }
  /**
 * Cierra la sesión y elimina los datos locales de autenticación.
 */
async function logoutSession() {
  try {
    await logoutRequest()
  } finally {
    clearSession()
  }
}

/**
 * Consulta los datos necesarios para reconstruir la sesión.
 */
async function loadSessionData() {
  const [userData, roles] = await Promise.all([
    getCurrentUser(),
    getOperationalRoles(),
  ])

  setUser(userData)
  setOperationalRoles(roles)
}

/**
 * Recupera la sesión y renueva el access token si venció.
 */
async function restoreSession() {
  if (!token.value) {
    return false
  }

  try {
    await loadSessionData()
    return true
  } catch (error) {
    if (error.response?.status !== 401) {
      return false
    }
  }

  try {
    const data = await refreshAccessToken()

    if (!data.access_token) {
      clearSession()
      return false
    }

    setToken(data.access_token)
    await loadSessionData()

    return true
  } catch (error) {
    if (error.response?.status === 401) {
      clearSession()
    }

    return false
  }
}


  return {
    token,
    user,
    operationalRoles,
    isAuthenticated,
    operationalRoleKey,
    setToken,
    setUser,
    setOperationalRoles,
    clearSession,
    restoreSession,
    logoutSession,
  }
})
