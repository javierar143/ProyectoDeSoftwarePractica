<script setup>
defineProps({
  error: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['retry', 'refresh'])
</script>

<template>
  <section
    v-if="error"
    class="api-error"
    role="alert"
  >
    <p>{{ error.message }}</p>

    <button
      v-if="error.isConflict"
      type="button"
      @click="emit('refresh')"
    >
      Actualizar datos
    </button>

    <button
      v-else-if="error.canRetry"
      type="button"
      @click="emit('retry')"
    >
      Reintentar
    </button>
  </section>
</template>

<style scoped>
.api-error {
  padding: 12px 16px;
  margin: 12px 0;
  color: #9b1c1c;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
}

.api-error p {
  margin: 0;
}

button {
  margin-top: 10px;
  padding: 6px 12px;
  cursor: pointer;
}
</style>