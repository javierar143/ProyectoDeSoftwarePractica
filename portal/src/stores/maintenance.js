import { defineStore } from 'pinia'
import { ref } from 'vue'

import { saveMaintenanceReturnRoute } from '@/modules/system/services/configuration'

const MAINTENANCE_TRANSITION_DELAY_MS = 3_000
const MAINTENANCE_TRANSITION_MESSAGE =
  'Sin conexión con el servidor. Verificando conexión automáticamente...'

export const useMaintenanceStore = defineStore('maintenance', () => {
  const isTransitioning = ref(false)
  const isMaintenanceActive = ref(false)

  let transitionTimer = null

  function beginTransition(router, returnPath = router.currentRoute.value.fullPath) {
    if (
      isTransitioning.value ||
      isMaintenanceActive.value ||
      router.currentRoute.value.name === 'maintenance'
    ) {
      return false
    }

    saveMaintenanceReturnRoute(returnPath)
    isTransitioning.value = true

    transitionTimer = setTimeout(async () => {
      transitionTimer = null
      try {
        if (router.currentRoute.value.name !== 'maintenance') {
          const navigationFailure = await router.replace({ name: 'maintenance' })
          if (navigationFailure) return
        }

        if (router.currentRoute.value.name === 'maintenance') {
          isMaintenanceActive.value = true
          isTransitioning.value = false
        }
      } catch {
        // Keep the application blocked if navigation cannot reach maintenance.
      }
    }, MAINTENANCE_TRANSITION_DELAY_MS)

    return true
  }

  function finishMaintenance() {
    if (transitionTimer !== null) {
      clearTimeout(transitionTimer)
      transitionTimer = null
    }

    isTransitioning.value = false
    isMaintenanceActive.value = false
  }

  return {
    isTransitioning,
    isMaintenanceActive,
    transitionMessage: MAINTENANCE_TRANSITION_MESSAGE,
    beginTransition,
    finishMaintenance,
  }
})
