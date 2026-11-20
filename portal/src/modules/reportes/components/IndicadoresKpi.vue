<script setup>
defineProps({
  resumenAutorizaciones: {
    type: Object,
    required: true,
  },
  resumenEntregas: {
    type: Object,
    required: true,
  },
})
</script>

<template>
  <section class="grid-kpi" aria-label="Indicadores principales">
    <article class="kpi-card">
      <span class="kpi-label">Pedidas regulares</span>
      <strong class="kpi-valor">{{ resumenAutorizaciones.total_pedido_regulares ?? 0 }}</strong>
    </article>

    <article class="kpi-card">
      <span class="kpi-label">Pedidas por excepción</span>
      <strong class="kpi-valor kpi-alerta">{{ resumenAutorizaciones.total_pedido_excepciones ?? 0 }}</strong>
    </article>

    <article class="kpi-card">
      <span class="kpi-label">Pedidas residentes</span>
      <strong class="kpi-valor">{{ resumenAutorizaciones.total_pedido_residentes ?? 0 }}</strong>
    </article>

    <article class="kpi-card">
      <span class="kpi-label">Total autorizadas</span>
      <strong class="kpi-valor kpi-azul">{{ resumenAutorizaciones.total_autorizado ?? 0 }}</strong>
    </article>

    <article class="kpi-card">
      <span class="kpi-label">Total entregadas</span>
      <strong class="kpi-valor kpi-verde">{{ resumenEntregas.total_entregado ?? 0 }}</strong>
    </article>

    <article class="kpi-card">
      <span class="kpi-label">Diferencia (Pedidas − Autorizadas)</span>
      <strong class="kpi-valor">{{ resumenAutorizaciones.diferencia ?? 0 }}</strong>
    </article>

    <article class="kpi-card">
      <span class="kpi-label">Diferencia (Autorizadas − Entregadas)</span>
      <strong class="kpi-valor">{{ resumenEntregas.diferencia ?? 0 }}</strong>
    </article>
  </section>
</template>

<style scoped>
.grid-kpi {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(175px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.kpi-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem 1.15rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.kpi-label {
  font-size: 0.82rem;
  color: #64748b;
  font-weight: 600;
}

.kpi-valor {
  font-size: 1.75rem;
  line-height: 1.1;
  color: #0f172a;
}

.kpi-azul {
  color: #2563eb;
}

.kpi-verde {
  color: #059669;
}

.kpi-alerta {
  color: #d97706;
}
</style>