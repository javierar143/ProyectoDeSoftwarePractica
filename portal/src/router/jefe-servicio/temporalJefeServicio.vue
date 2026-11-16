
<template>
  <main class="temporal-jefe-servicio">
    <h1>Jefe de Servicio</h1>

    <p>Acceso correcto al módulo Jefe de Servicio.</p>

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
.temporal-jefe-servicio {
  padding: 2rem;
  text-align: center;
}

h1 {
  margin-bottom: 1rem;
}
</style>
