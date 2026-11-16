<template>
  <div class="logout-container">
    <button
      type="button"
      :disabled="loading"
      @click="handleLogout"
    >
      {{ loading ? 'Cerrando sesión...' : 'Cerrar sesión' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)

/**
 * Cierra la sesión y vuelve al inicio de sesión.
 *
 * Si falla la comunicación con el backend, limpia igualmente
 * la sesión local e informa que no se pudo confirmar el cierre remoto.
 */
async function handleLogout() {
  if (loading.value) {
    return
  }

  loading.value = true
  let logoutFailed = false

  try {
    await authStore.logoutSession()
  } catch (error) {
    logoutFailed = true
  } finally {
    await router.replace({
      name: 'login',
      query: logoutFailed ? { logout: 'incomplete' } : {},
    })
  }
}
</script>