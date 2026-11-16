<template>
  <button type="button" @click="handleLogout">
    Cerrar sesión
  </button>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

/**
 * Cierra la sesión y vuelve al inicio de sesión.
 */
async function handleLogout() {
  try {
    await authStore.logoutSession()
  } finally {
    await router.replace({ name: 'login' })
  }
}
</script>