<script setup>
import { useCounterStore } from '../../../stores/counter'

const counter = useCounterStore()
</script>

<template>
  <main>
    <h1>Contador de prueba</h1>

    <p>Valor actual: {{ counter.count }}</p>
    <p>Valor duplicado: {{ counter.doubleCount }}</p>

    <button @click="counter.increment()">Incrementar</button>

    <p>
      <RouterLink to="/">Volver al inicio</RouterLink>
    </p>
  </main>
</template>
