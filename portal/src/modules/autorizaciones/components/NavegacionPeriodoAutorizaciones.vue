<template>
  <section class="navegacion-periodo" aria-label="Navegación de período y calendario">
    <div class="controles-periodo">
      <div class="grupo-botones-periodo">
        <button type="button" :disabled="cargando" @click="$emit('navegar', -1)">
          ← Anterior
        </button>
        <button type="button" :disabled="cargando" @click="$emit('ir-hoy')">
          Hoy ({{ formatearFechaDdMmAaaa(hoyIso) }})
        </button>
        <button type="button" :disabled="cargando" @click="$emit('navegar', 1)">
          Siguiente →
        </button>
      </div>
      <span class="rango-activo-texto">
        Período:
        <strong>{{ formatearFechaDdMmAaaa(fechaDesde) }}</strong>
        <template v-if="fechaHasta && fechaHasta !== fechaDesde">
          al <strong>{{ formatearFechaDdMmAaaa(fechaHasta) }}</strong>
        </template>
      </span>
    </div>

    <div class="calendario-dias" aria-label="Días con pedidos">
      <span class="calendario-etiqueta">Días con pedidos</span>
      <div v-if="diasConPedidos.length > 0" class="calendario-pills">
        <button
          v-for="dia in diasConPedidos"
          :key="dia"
          type="button"
          :class="['btn-dia-cal con-pedidos', fechaDesde === dia ? 'seleccionado' : '']"
          :disabled="cargando"
          @click="$emit('seleccionar-dia', dia)"
        >
          <span class="dia-nombre">{{ formatearDiaCorto(dia) }}</span>
          <span class="fecha-ddmm">{{ formatearFechaDdMmAaaa(dia) }}</span>
          <span class="punto-pedido" aria-hidden="true">●</span>
        </button>
      </div>
      <span v-else class="sin-dias-pedidos">Sin días con pedidos en el período.</span>
    </div>
  </section>
</template>

<script setup>
defineProps({
  hoyIso: {
    type: String,
    required: true,
  },
  fechaDesde: {
    type: String,
    default: '',
  },
  fechaHasta: {
    type: String,
    default: '',
  },
  diasConPedidos: {
    type: Array,
    default: () => [],
  },
  cargando: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['navegar', 'ir-hoy', 'seleccionar-dia'])

function formatearFechaDdMmAaaa(valorFecha) {
  if (!valorFecha) return '-'
  const iso = String(valorFecha).slice(0, 10)
  const partes = iso.split('-')
  if (partes.length !== 3) return String(valorFecha)
  return `${partes[2]}/${partes[1]}/${partes[0]}`
}

function formatearDiaCorto(isoDate) {
  const [a, m, d] = String(isoDate).slice(0, 10).split('-').map(Number)
  const fecha = new Date(a, (m || 1) - 1, d || 1)
  return fecha.toLocaleDateString('es-AR', { weekday: 'short' }).replace('.', '')
}
</script>

<style scoped>
.navegacion-periodo {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.9rem 1.1rem;
  margin-bottom: 1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.controles-periodo {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
}

.grupo-botones-periodo {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem;
}

.rango-activo-texto {
  font-size: 0.86rem;
  color: #475569;
}

.calendario-dias {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  border-top: 1px solid #e2e8f0;
  padding-top: 0.7rem;
}

.calendario-etiqueta {
  font-size: 0.74rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.calendario-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.sin-dias-pedidos {
  font-size: 0.82rem;
  color: #64748b;
}

button {
  min-height: 36px;
  padding: 0.38rem 0.8rem;
  border-radius: 7px;
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #1e293b;
}

button:hover:not(:disabled) {
  background: #f8fafc;
}

button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-dia-cal {
  padding: 0.3rem 0.65rem;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.82rem;
}

.btn-dia-cal.con-pedidos {
  border-color: #93c5fd;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 600;
}

.btn-dia-cal.con-pedidos.seleccionado {
  background: #2563eb;
  border-color: #1d4ed8;
  color: #ffffff;
}

.punto-pedido {
  font-size: 0.6rem;
  line-height: 1;
}

@media (max-width: 767px) {
  .rango-activo-texto {
    width: 100%;
  }
}
</style>