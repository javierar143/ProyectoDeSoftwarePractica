import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  getCurrentUser,
  getOperationalRoles,
  refreshAccessToken,
  logout as logoutRequest,
} from '@/modules/auth/services/auth'

const TOKEN_REFRESH_MARGIN_MS = 5 * 60 * 1000

/**
 * Centraliza el estado de autenticación del portal.
 */
export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token'))
  const user = ref(null)
  const operationalRoles = ref(null)

  let refreshTimer = null
  let refreshPromise = null
  let sessionExpiredHandler = null

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
   * Obtiene la fecha de vencimiento del JWT.
   * Se utiliza exclusivamente para programar la renovación preventiva.
   */
  function getTokenExpiration(tokenValue) {
    try {
      const payload = tokenValue.split('.')[1]

      if (!payload) {
        return null
      }

      const base64 = payload
        .replace(/-/g, '+')
        .replace(/_/g, '/')

      const normalizedBase64 = base64.padEnd(
        Math.ceil(base64.length / 4) * 4,
        '=',
      )

      const claims = JSON.parse(atob(normalizedBase64))

      return Number.isFinite(claims.exp)
        ? claims.exp * 1000
        : null
    } catch {
      return null
    }
  }

  /**
   * Programa la renovación únicamente para Sector Comedor.
   */
  function scheduleTokenRefresh() {
    if (refreshTimer !== null) {
      clearTimeout(refreshTimer)
      refreshTimer = null
    }

    if (
      !token.value ||
      operationalRoleKey.value !== 'sectorComedor'
    ) {
      return
    }

    const expirationTime = getTokenExpiration(token.value)

    if (!expirationTime) {
      return
    }

    const delay = Math.max(
      expirationTime - Date.now() - TOKEN_REFRESH_MARGIN_MS,
      0,
    )

    refreshTimer = setTimeout(() => {
      refreshTimer = null
      renewSectorAccessToken()
    }, delay)
  }

  /**
   * Guarda el access token y actualiza su renovación programada.
   */
  function setToken(accessToken) {
    token.value = accessToken
    localStorage.setItem('token', accessToken)

    scheduleTokenRefresh()
  }

  /**
   * Actualiza los datos del usuario autenticado.
   */
  function setUser(userData) {
    user.value = userData

    scheduleTokenRefresh()
  }

  /**
   * Actualiza los identificadores de roles obtenidos de la API.
   */
  function setOperationalRoles(roles) {
    operationalRoles.value = roles

    scheduleTokenRefresh()
  }

  /**
   * Registra la navegación que debe ejecutarse cuando expire la sesión.
   */
  function setSessionExpiredHandler(handler) {
    sessionExpiredHandler =
      typeof handler === 'function' ? handler : null
  }

  /**
   * Elimina los datos locales de autenticación y cancela la renovación.
   */
  function clearSession() {
    if (refreshTimer !== null) {
      clearTimeout(refreshTimer)
      refreshTimer = null
    }

    token.value = null
    user.value = null
    operationalRoles.value = null

    localStorage.removeItem('token')
  }

  /**
   * Finaliza la sesión cuando el refresh token ya no es válido.
   */
  async function expireSession() {
    clearSession()

    if (sessionExpiredHandler) {
      await sessionExpiredHandler()
    }
  }

  /**
   * Renueva preventivamente el access token de Sector Comedor.
   */
  async function renewSectorAccessToken() {
    if (
      !token.value ||
      operationalRoleKey.value !== 'sectorComedor'
    ) {
      return
    }

    if (refreshPromise) {
      return refreshPromise
    }

    const tokenBeingRenewed = token.value

    refreshPromise = (async () => {
      try {
        const data = await refreshAccessToken()

        if (!data.access_token) {
          await expireSession()
          return
        }

        // Evita restaurar una sesión que se cerró mientras se renovaba.
        if (
          token.value !== tokenBeingRenewed ||
          operationalRoleKey.value !== 'sectorComedor'
        ) {
          return
        }

        setToken(data.access_token)
      } catch (error) {
        // Si el refresh token fue rechazado, finaliza la sesión.
        if (error.response?.status === 401) {
          if (token.value === tokenBeingRenewed) {
            await expireSession()
          }

          return
        }

        // La falta de permisos no demuestra que la sesión haya vencido.
        if (error.response?.status === 403) {
          return
        }

        // El refresh crea un registro de token; no se repite si el resultado es incierto.
        if (!error.response || error.response.status >= 500) {
          return
        }

        if (token.value === tokenBeingRenewed) {
          await expireSession()
        }
      }
    })()

    try {
      await refreshPromise
    } finally {
      refreshPromise = null
    }
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
   * Restaura los datos de una sesión existente.
   *
   * Si la API devuelve 401, elimina la sesión local.
   * No intenta renovar el token después de recibir un 401.
   */
  async function restoreSession() {
    if (!token.value) {
      return false
    }

    try {
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
    setSessionExpiredHandler,
    clearSession,
    restoreSession,
    logoutSession,
  }
})
