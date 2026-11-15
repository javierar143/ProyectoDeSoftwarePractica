
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../services/auth'

const router = useRouter()

const email = ref('')
const password = ref('')
const errorMessage = ref('')
const loading = ref(false)

async function handleLogin() {
  errorMessage.value = ''

  if (!email.value.trim() || !password.value) {
    errorMessage.value = 'Completá el email y la contraseña.'
    return
  }

  loading.value = true

  try {
    const data = await login(email.value.trim(), password.value)

    localStorage.setItem('token', data.access_token)

    
  } catch (error) {
    if (error.response?.status === 401) {
      errorMessage.value = 'Email o contraseña incorrectos.'
    } else if (error.response?.status === 400) {
      errorMessage.value =
        error.response.data.description ||
        error.response.data.message ||
        'Los datos enviados no son válidos.'
    } else {
      errorMessage.value = 'No se pudo conectar con el servidor.'
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

      <form @submit.prevent="handleLogin">
        <div class="form-field">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            autocomplete="username"
            required
          />
        </div>

        <div class="form-field">
          <label for="password">Contraseña</label>
          <input
            id="password"
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
          />
        </div>

        <p v-if="errorMessage" class="error-message" role="alert">
          {{ errorMessage }}
        </p>

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

.error-message {
  margin-bottom: 16px;
  color: #c62828;
}

@media (max-width: 600px) {
  .login-card {
    padding: 24px;
  }
}
</style>
