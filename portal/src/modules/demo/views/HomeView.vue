<script setup>
  import { useCounterStore } from '../../../stores/counter'

  const counter = useCounterStore()
</script>

<template>
  <main>
    <h1>Portal - Prueba de Etapa 2</h1>
    <p>Bienvenido a la aplicación.</p>
    <p>Contador compartido: {{ counter.count }}</p>

    <button @click="counter.increment()">
      Incrementar desde Inicio
    </button>

    <RouterLink to="/contador">Ir al contador</RouterLink>
  </main>
</template>
