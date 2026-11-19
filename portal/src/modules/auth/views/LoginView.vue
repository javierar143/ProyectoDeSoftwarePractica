
<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { getRoleHomeRoute } from '@/router/navigation'
import { normalizeApiError } from '@/services/api/error-handler'
import ApiErrorMessage from '@/modules/shared/components/ApiErrorMessage.vue'
import { getPublicConfiguration } from '@/modules/system/services/configuration'

import {
  login,
  loginWithGoogle,
  getCurrentUser,
  getOperationalRoles,
} from '../services/auth'

const GOOGLE_SCRIPT_URL = 'https://accounts.google.com/gsi/client'
const GOOGLE_BUTTON_MIN_WIDTH = 120
const GOOGLE_BUTTON_MAX_WIDTH = 400
const googleClientId = ref('')
let googleScriptPromise = null

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const ACCOUNT_BLOCKED_MESSAGE =
  'La cuenta está bloqueada. Contactá al administrador.'

const email = ref('')
const password = ref('')
const emailError = ref('')
const passwordError = ref('')
const emailInput = ref(null)
const apiErrorMessage = ref(null)
const loading = ref(false)
const retryLoginOperation = ref(null)
const googleButton = ref(null)
const googleMessage = ref('')

const logoutWarning = computed(
  () => route.query.logout === 'incomplete',
)

watch(
  () => route.query.auth_error,
  (authError) => {
    if (authError === 'account_blocked') {
      apiErrorMessage.value = {
        message: ACCOUNT_BLOCKED_MESSAGE,
        canRetry: false,
      }
    }
  },
  { immediate: true },
)

/**
 * Determina el destino después del login.
 *
 * Si el usuario puede acceder a la ruta solicitada,
 * conserva el redirect.
 *
 * Si tiene otro rol operativo, lo dirige a su pantalla inicial.
 *
 * Si no tiene un rol operativo habilitado, muestra acceso denegado.
 */
function getPostLoginDestination() {
  const redirect = route.query.redirect
  const roleKey = authStore.operationalRoleKey

  if (typeof redirect === 'string' && redirect.trim()) {
    const requestedPath = redirect.trim()

    const redirectPath = requestedPath.startsWith('/')
      ? requestedPath
      : `/${requestedPath}`

    if (!redirectPath.startsWith('//')) {
      const resolvedRoute = router.resolve(redirectPath)

      const requiredRoles = resolvedRoute.meta.roles

      const roleIsAuthorized =
        !requiredRoles ||
        (Array.isArray(requiredRoles) &&
          requiredRoles.includes(roleKey))

      if (
        resolvedRoute.matched.length > 0 &&
        resolvedRoute.name !== 'login' &&
        roleIsAuthorized
      ) {
        return resolvedRoute.fullPath
      }
    }
  }

  const destination = getRoleHomeRoute(roleKey)

  return destination
    ? { name: destination }
    : { name: 'access-denied' }
}

/**
 * Valida los campos antes de enviar las credenciales.
 */
function validateForm() {
  emailError.value = ''
  passwordError.value = ''

  if (!email.value.trim()) {
    emailError.value = 'El email es obligatorio.'
    return false
  }

  if (!emailInput.value.checkValidity()) {
    emailError.value = 'Ingresá un email válido.'
    return false
  }

  if (!password.value) {
    passwordError.value = 'La contraseña es obligatoria.'
    return false
  }

  return true
}

/** Carga una sola vez el SDK oficial de Google Identity Services. */
function loadGoogleIdentityServices() {
  if (window.google?.accounts?.id) {
    return Promise.resolve(window.google)
  }

  if (googleScriptPromise) {
    return googleScriptPromise
  }

  googleScriptPromise = new Promise((resolve, reject) => {
    let script = document.querySelector(`script[src="${GOOGLE_SCRIPT_URL}"]`)
    const rejectAndRemoveScript = (error) => {
      script?.remove()
      reject(error)
    }

    const handleLoad = () => {
      if (window.google?.accounts?.id) {
        resolve(window.google)
      } else {
        rejectAndRemoveScript(
          new Error('Google Identity Services no está disponible.'),
        )
      }
    }

    const handleError = () => {
      rejectAndRemoveScript(
        new Error('No se pudo cargar Google Identity Services.'),
      )
    }

    if (!script) {
      script = document.createElement('script')
      script.src = GOOGLE_SCRIPT_URL
      script.async = true
      script.defer = true
      script.addEventListener('load', handleLoad, { once: true })
      script.addEventListener('error', handleError, { once: true })
      document.head.appendChild(script)
      return
    }

    script.addEventListener('load', handleLoad, { once: true })
    script.addEventListener('error', handleError, { once: true })
  }).catch((error) => {
    googleScriptPromise = null
    throw error
  })

  return googleScriptPromise
}

/** Configura GIS y dibuja su botón cuando existe un Client ID. */
async function initializeGoogleLogin() {
  try {
    const configuration = await getPublicConfiguration()
    googleClientId.value = configuration?.google_client_id?.trim() || ''

    if (!googleClientId.value) {
      googleMessage.value =
        'El inicio de sesión con Google no está disponible. Podés ingresar con email y contraseña.'
      return
    }

    const google = await loadGoogleIdentityServices()
    const buttonWidth = Math.min(
      Math.max(
        Math.floor(googleButton.value.clientWidth),
        GOOGLE_BUTTON_MIN_WIDTH,
      ),
      GOOGLE_BUTTON_MAX_WIDTH,
    )

    google.accounts.id.initialize({
      client_id: googleClientId.value,
      callback: handleGoogleCredential,
    })
    google.accounts.id.renderButton(googleButton.value, {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      text: 'signin_with',
      shape: 'rectangular',
      width: buttonWidth,
    })
  } catch {
    googleMessage.value =
      'No se pudo cargar el inicio de sesión con Google. Podés ingresar con email y contraseña.'
  }
}

/** Continúa con el flujo local solo si GIS entregó un credential. */
function handleGoogleCredential(response) {
  if (typeof response?.credential !== 'string' || !response.credential) {
    apiErrorMessage.value = {
      message: 'Google no devolvió una credencial válida. Intentá nuevamente.',
      canRetry: false,
    }
    return
  }

  const credential = response.credential
  executeLogin(() => loginWithGoogle(credential))
}

onMounted(initializeGoogleLogin)

/**
 * Ejecuta el proceso de autenticación y carga los datos del usuario.
 */
async function handleLogin() {
  apiErrorMessage.value = null
  emailError.value = ''
  passwordError.value = ''

  if (!validateForm()) {
    return
  }

  const credentials = {
    email: email.value.trim(),
    password: password.value,
  }
  executeLogin(() => login(credentials.email, credentials.password))
}

async function retryFailedOperation() {
  if (loading.value || typeof retryLoginOperation.value?.run !== 'function') return
  const operation = retryLoginOperation.value
  if (operation.type === 'login') {
    await executeLogin(operation.run)
    return
  }

  loading.value = true
  apiErrorMessage.value = null
  try {
    await operation.run()
    retryLoginOperation.value = null
  } catch (error) {
    const apiError = normalizeApiError(error)
    if (apiError.status === 401) authStore.clearSession()
    apiErrorMessage.value = apiError
    retryLoginOperation.value = operation.type === 'session' && apiError.canRetry && apiError.status !== 503
      ? operation
      : null
  } finally {
    loading.value = false
  }
}

async function completeAuthenticatedSession() {
  const user = await getCurrentUser()
  authStore.setUser(user)

  const roles = await getOperationalRoles()
  authStore.setOperationalRoles(roles)

  await router.replace(getPostLoginDestination())
}

/** Comparte la carga de sesión y el manejo de errores entre ambos accesos. */
async function executeLogin(authenticate) {
  if (loading.value) {
    return
  }

  apiErrorMessage.value = null
  retryLoginOperation.value = null
  loading.value = true
  let credentialsAccepted = false
  let retryOperation = { type: 'login', run: authenticate }

  try {
    const data = await authenticate()

    authStore.setToken(data.access_token)
    credentialsAccepted = true

    retryOperation = { type: 'session', run: completeAuthenticatedSession }
    await completeAuthenticatedSession()
  } catch (error) {
    const apiError = normalizeApiError(error)

    if (apiError.code === 'ACCOUNT_BLOCKED') {
      authStore.markAccountBlocked()
      apiErrorMessage.value = {
        ...apiError,
        message: ACCOUNT_BLOCKED_MESSAGE,
        canRetry: false,
      }
      retryLoginOperation.value = null
    } else if (apiError.status === 401 && credentialsAccepted) {
      authStore.clearSession()
    }

    if (apiError.status === 401 && credentialsAccepted) {
      apiErrorMessage.value = {
        ...apiError,
        message: 'No se pudo establecer la sesión. Volvé a ingresar.',
        canRetry: false,
      }
    } else {
      const fields = apiError.fieldErrors ?? {}

      emailError.value = fields.email ?? ''
      passwordError.value = fields.password ?? ''

      if (!emailError.value && !passwordError.value) {
        apiErrorMessage.value = apiError
      }
    }

    retryLoginOperation.value = retryOperation.type === 'session' && apiError.canRetry && apiError.status !== 503
      ? retryOperation
      : null
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-container">
    <section class="login-card">
      <h1>Iniciar sesión</h1>

      <p
        v-if="logoutWarning"
        class="logout-warning"
        role="status"
      >
        La sesión local se cerró, pero no se pudo confirmar el cierre
        en el servidor.
      </p>

      <form @submit.prevent="handleLogin" novalidate>
        <div class="form-field">
          <label for="email">Email</label>

          <input
            id="email"
            ref="emailInput"
            v-model="email"
            type="email"
            autocomplete="username"
            required
            :aria-invalid="Boolean(emailError)"
            :aria-describedby="emailError ? 'email-error' : undefined"
            @input="emailError = ''"
          />

          <p v-if="emailError" id="email-error" class="field-error">
            {{ emailError }}
          </p>
        </div>

        <div class="form-field">
          <label for="password">Contraseña</label>

          <input
            id="password"
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
            :aria-invalid="Boolean(passwordError)"
            :aria-describedby="passwordError ? 'password-error' : undefined"
            @input="passwordError = ''"
          />

          <p
            v-if="passwordError"
            id="password-error"
            class="field-error"
          >
            {{ passwordError }}
          </p>
        </div>

        <ApiErrorMessage
          :error="apiErrorMessage"
          @retry="retryFailedOperation"
        />

        <button type="submit" :disabled="loading">
          {{ loading ? 'Ingresando...' : 'Ingresar' }}
        </button>

        <template v-if="googleClientId">
          <div class="login-divider" aria-hidden="true">o</div>
          <div ref="googleButton" class="google-button"></div>
        </template>
        <p v-if="googleMessage" class="google-message" role="status">
          {{ googleMessage }}
        </p>
      </form>
    </section>
  </main>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
  background-color: #f3f4f6;
  color: #1f2937;
  font-family: Arial, sans-serif;
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 32px;
  background-color: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

h1 {
  margin-bottom: 24px;
  color: #1d4ed8;
  text-align: center;
}

.logout-warning {
  margin-bottom: 18px;
  padding: 12px;
  color: #854d0e;
  background-color: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 6px;
  font-size: 14px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 18px;
}

label {
  font-weight: 600;
}

input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font: inherit;
}

input:focus {
  border-color: #2563eb;
  outline: 2px solid rgba(37, 99, 235, 0.2);
}

input[aria-invalid='true'] {
  border-color: #c62828;
}

.field-error {
  color: #c62828;
  font-size: 14px;
  margin: 0;
}

.login-divider {
  margin: 16px 0;
  color: #6b7280;
  text-align: center;
}

.google-button {
  display: flex;
  justify-content: center;
  min-height: 40px;
}

.google-message {
  margin: 10px 0 0;
  color: #4b5563;
  font-size: 14px;
  text-align: center;
}

button {
  width: 100%;
  padding: 10px 16px;
  color: #ffffff;
  background-color: #2563eb;
  border: 0;
  border-radius: 8px;
  font: inherit;
  cursor: pointer;
}

button:hover {
  background-color: #1d4ed8;
}

button:disabled {
  cursor: wait;
}

@media (max-width: 600px) {
  .login-card {
    padding: 24px;
  }
}
</style>
