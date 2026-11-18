<template>
  <div :inert="maintenanceStore.isTransitioning" :aria-hidden="maintenanceStore.isTransitioning">
    <RouterView />
  </div>

  <div
    v-if="maintenanceStore.isTransitioning"
    class="maintenance-transition"
    role="alert"
    aria-live="assertive"
    aria-modal="true"
  >
    <p>{{ maintenanceStore.transitionMessage }}</p>
  </div>
</template>

<script setup>
import { useMaintenanceStore } from '@/stores/maintenance'

const maintenanceStore = useMaintenanceStore()
</script>

<style>
.maintenance-transition {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgb(15 23 42 / 78%);
  color: #fff;
  cursor: wait;
}

.maintenance-transition p {
  max-width: 36rem;
  margin: 0;
  padding: 24px 32px;
  border-radius: 12px;
  background: #1e293b;
  box-shadow: 0 16px 40px rgb(0 0 0 / 30%);
  font-size: 1.1rem;
  line-height: 1.5;
  text-align: center;
}
</style>
