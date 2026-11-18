<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useMaintenanceStore } from '@/stores/maintenance'
import { getRoleHomeRoute } from '@/router/navigation'
import {
  clearMaintenanceReturnRoute,
  getMaintenanceReturnRoute,
  getPublicConfiguration,
  MAINTENANCE_MESSAGE_DEFAULT,
} from '../services/configuration'

const POLL_INTERVAL_MS = 7000

const router = useRouter()
const authStore = useAuthStore()
const maintenanceStore = useMaintenanceStore()
const message = ref(MAINTENANCE_MESSAGE_DEFAULT)

let pollingTimer = null
let polling = false
let viewActive = false

async function restoreApplication() {
  let destination = getMaintenanceReturnRoute()
  let sessionIsValid = false

  if (destination && (!destination.startsWith('/') || destination.startsWith('//'))) {
    destination = null
  }

  if (authStore.token) {
    sessionIsValid = await authStore.restoreSession()
    // Un fallo de red o 500 no invalida el token: se vuelve a comprobar en el próximo sondeo.
    if (!sessionIsValid && authStore.token) return
  }

  if (!viewActive) return

  if (!sessionIsValid) {
    const result = await router.replace({
      name: 'login',
      ...(destination && destination !== '/login'
        ? { query: { redirect: destination } }
        : {}),
    })
    if (!result) {
      clearMaintenanceReturnRoute()
      maintenanceStore.finishMaintenance()
    }
    return
  }

  if (!destination || destination === '/login' || destination === '/maintenance') {
    destination = getRoleHomeRoute(authStore.operationalRoleKey)
  }

  const result = await router.replace(destination ? destination : { name: 'access-denied' })
  if (!result) {
    clearMaintenanceReturnRoute()
    maintenanceStore.finishMaintenance()
  }
}

async function pollServiceStatus() {
  if (!viewActive || polling) return
  polling = true

  try {
    const configuration = await getPublicConfiguration()
    if (!viewActive) return
    message.value = configuration.mensaje_mantenimiento || MAINTENANCE_MESSAGE_DEFAULT

    if (!configuration.modo_mantenimiento) {
      await restoreApplication()
    }
  } catch {
    // La vista permanece y el siguiente sondeo vuelve a consultar el estado.
  } finally {
    polling = false
  }
}

onMounted(() => {
  viewActive = true
  pollServiceStatus()
  pollingTimer = setInterval(pollServiceStatus, POLL_INTERVAL_MS)
})

onBeforeUnmount(() => {
  viewActive = false
  if (pollingTimer !== null) clearInterval(pollingTimer)
  pollingTimer = null
})
</script>

<template>
  <main class="maintenance-page">
    <section class="maintenance-card" role="status" aria-live="polite">
      <div class="icon-container">🛠️</div>
      <h1>Estamos realizando mejoras</h1>
      <p>{{ message }}</p>
      <p class="return-info">
        La aplicación volverá a estar disponible automáticamente cuando finalice el mantenimiento.
        No necesitás realizar ninguna acción.
      </p>
      <div><span class="badge">Modo Mantenimiento Activo</span></div>
    </section>
  </main>
</template>

<style scoped>
.maintenance-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 24px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
  background-color: #f4f7f6;
  color: #2c3e50;
}

.maintenance-card {
  box-sizing: border-box;
  width: min(100%, 560px);
  padding: 40px 30px;
  border-top: 5px solid #e67e22;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 10px 25px rgb(0 0 0 / 5%);
  text-align: center;
}

.icon-container { margin-bottom: 20px; font-size: 50px; }
h1 { margin-bottom: 15px; font-size: 24px; }
p { margin: 0; color: #52616b; font-size: 16px; line-height: 1.6; }
.return-info { margin-top: 16px; }
.badge {
  display: inline-block;
  margin-top: 25px;
  padding: 6px 14px;
  border-radius: 20px;
  background: rgb(230 126 34 / 10%);
  color: #e67e22;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
</style>
