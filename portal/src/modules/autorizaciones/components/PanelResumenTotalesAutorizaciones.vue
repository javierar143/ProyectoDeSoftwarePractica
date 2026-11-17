<template>
  <section
    class="panel-resumen-totales"
    aria-label="Totales pedidos y autorizados del período"
  >
    <div class="tarjetas-indicadores">
      <div class="indicador-box">
        <span class="ind-label">Total pedidas</span>
        <strong class="ind-valor">{{ resumen.total_pedido ?? 0 }}</strong>
        <small>
          Regulares: {{ resumen.total_pedido_regulares ?? 0 }} · Excepción:
          {{ resumen.total_pedido_excepciones ?? 0 }}
        </small>
      </div>
      <div class="indicador-box">
        <span class="ind-label">Total autorizadas</span>
        <strong class="ind-valor texto-verde">{{ resumen.total_autorizado ?? 0 }}</strong>
      </div>
      <div class="indicador-box">
        <span class="ind-label">Diferencia (Pedidas - Autorizadas)</span>
        <strong class="ind-valor">{{ resumen.diferencia ?? 0 }}</strong>
      </div>
    </div>

    <div v-if="(resumen.desglose || []).length > 0" class="tabla-contenedor tabla-resumen-margin">
      <table class="tabla-pedidos">
        <thead>
          <tr>
            <th scope="col">Sector</th>
            <th scope="col">Comida</th>
            <th scope="col">Tipo de menú</th>
            <th scope="col">Regulares</th>
            <th scope="col">Excepción</th>
            <th scope="col">Pedidas</th>
            <th scope="col">Autorizadas</th>
            <th scope="col">Diferencia</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(item, idx) in resumen.desglose"
            :key="`${item.idSector}-${item.idTipoComida}-${item.idTipoMenu}-${idx}`"
          >
            <td>{{ item.sector }}</td>
            <td>{{ item.comida }}</td>
            <td>{{ item.tipo_menu }}</td>
            <td class="dato-mono">{{ item.cantidad_pedida_regulares }}</td>
            <td class="dato-mono">{{ item.cantidad_pedida_excepciones }}</td>
            <td class="dato-mono">{{ item.cantidad_pedida }}</td>
            <td class="dato-mono">{{ item.cantidad_autorizada }}</td>
            <td class="dato-mono">{{ item.diferencia }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
defineProps({
  resumen: {
    type: Object,
    required: true,
  },
})
</script>

<style scoped>
.panel-resumen-totales {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1rem 1.1rem;
  margin-bottom: 1.1rem;
}

.tarjetas-indicadores {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 0.75rem;
}

.indicador-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.75rem 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.ind-label {
  font-size: 0.76rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
}

.ind-valor {
  font-size: 1.35rem;
  font-weight: 700;
  color: #0f172a;
}

.texto-verde {
  color: #0f766e;
}

.tabla-resumen-margin {
  margin-top: 0.85rem;
}

.tabla-contenedor {
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #ffffff;
}

.tabla-pedidos {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.tabla-pedidos th,
.tabla-pedidos td {
  padding: 0.7rem 0.9rem;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
}

.tabla-pedidos tbody tr:last-child td {
  border-bottom: none;
}

.tabla-pedidos th {
  background: #f8fafc;
  color: #475569;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.dato-mono {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}
</style>