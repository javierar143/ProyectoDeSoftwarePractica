import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import apiClient from './services/api/client'

import { useAuthStore } from './stores/auth'
import { useMaintenanceStore } from './stores/maintenance'
import { registerAuthResponseInterceptor } from './services/api/auth-interceptor'
import { registerMaintenanceInterceptor } from './services/api/maintenance-interceptor'

const app = createApp(App)

const pinia = createPinia()

app.use(pinia)

// Obtiene el store asociado a la instancia de Pinia.
const authStore = useAuthStore(pinia)
const maintenanceStore = useMaintenanceStore(pinia)

// Define la navegación cuando vence definitivamente la sesión.
authStore.setSessionExpiredHandler(async () => {
  const currentRoute = router.currentRoute.value

  if (currentRoute.name !== 'login' && currentRoute.name !== 'maintenance') {
    await router.replace({
      name: 'login',
      query: { redirect: currentRoute.fullPath },
    })
  }
})

// Registra el tratamiento global de respuestas 401.
registerAuthResponseInterceptor(apiClient, authStore, router)

// Registra el tratamiento global de respuestas 503.
registerMaintenanceInterceptor(apiClient, router, maintenanceStore)

// Instala el router después de registrar el interceptor.
app.use(router)

app.mount('#app')
