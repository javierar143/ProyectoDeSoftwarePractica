<template>
  <main class="access-denied">
    <h1>Acceso denegado</h1>

    <p>
      Tu usuario no tiene un rol operativo habilitado para acceder al portal.
    </p>

   <LogoutButton />
  </main>
</template>

<script setup>
import LogoutButton from '../components/LogoutButton.vue'
</script>

<style scoped>
.access-denied {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  text-align: center;
  padding: 2rem;
}
</style>