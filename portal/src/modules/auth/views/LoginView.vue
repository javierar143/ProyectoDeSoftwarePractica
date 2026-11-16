
<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { getRoleHomeRoute } from '@/router/navigation'
import { normalizeApiError } from '@/services/api/error-handler'
import ApiErrorMessage from '@/modules/shared/components/ApiErrorMessage.vue'

import {
  login,
  getCurrentUser,
  getOperationalRoles,
} from '../services/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const emailError = ref('')
const passwordError = ref('')
const emailInput = ref(null)
const apiErrorMessage = ref(null)
const loading = ref(false)

// Indica si el servidor no pudo confirmar el cierre de sesión anterior.
const logoutWarning = computed(
  () => route.query.logout === 'incomplete',
)

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

  loading.value = true
  let credentialsAccepted = false

  try {
    const data = await login(email.value.trim(), password.value)

    authStore.setToken(data.access_token)
    credentialsAccepted = true

    const user = await getCurrentUser()
    authStore.setUser(user)

    const roles = await getOperationalRoles()
    authStore.setOperationalRoles(roles)

    const redirect = route.query.redirect

    if (typeof redirect === 'string') {
      await router.replace(redirect)
    } else {
      const destination = getRoleHomeRoute(authStore.operationalRoleKey)

      await router.replace(
        destination
          ? { name: destination }
          : { name: 'access-denied' },
      )
    }
  } catch (error) {
    const apiError = normalizeApiError(error)

    authStore.clearSession()

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

      // Si los errores ya se muestran junto a los campos,
      // no repetimos el mensaje general.
      if (!emailError.value && !passwordError.value) {
        apiErrorMessage.value = apiError
      }
    }
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
          @retry="handleLogin"
        />

        <button type="submit" :disabled="loading">
          {{ loading ? 'Ingresando...' : 'Ingresar' }}
        </button>
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
