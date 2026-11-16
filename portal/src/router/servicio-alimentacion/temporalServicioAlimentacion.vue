
<template>
  <main class="temporal-servicio-alimentacion">
    <h1>Servicio de Alimentación</h1>

    <p>Acceso correcto al módulo Servicio de Alimentación.</p>

    <p>
      Esta pantalla es temporal y se eliminará cuando se implemente
      la vista definitiva.
    </p>

    <LogoutButton />
  </main>
</template>

<script setup>
import LogoutButton from '@/modules/auth/components/LogoutButton.vue'
</script>

<style scoped>
.temporal-servicio-alimentacion {
  padding: 2rem;
  text-align: center;
}

h1 {
  margin-bottom: 1rem;
}
</style>
