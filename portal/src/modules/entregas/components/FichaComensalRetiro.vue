<template>
  <article class="ficha-comensal-clara">
    <div class="ficha-comensal-top">
      <div class="comensal-identidad">
        <div class="avatar-iniciales" aria-hidden="true">
          {{ iniciales }}
        </div>
        <div>
          <h3 class="ficha-nya">{{ persona.apellido }}, {{ persona.nombre }}</h3>
          <div class="ficha-chips-meta">
            <span class="chip-dni">DNI {{ dniConPuntos }}</span>
            <span class="chip-sector">{{ persona.sector }}</span>
            <span class="chip-menu">Menú {{ persona.menuPrincipal }}</span>
          </div>
        </div>
      </div>

      <button
        type="button"
        class="btn-quitar-ficha"
        @click="$emit('quitar', persona.idPersonal)"
      >
        Quitar
      </button>
    </div>

    <div
      class="grilla-comidas-ficha"
      role="group"
      :aria-label="`Comidas del día para ${persona.nombre}`"
    >
      <button
        v-for="comida in comidasConfig"
        :key="comida.id"
        type="button"
        :disabled="!puedeSeleccionar(comida)"
        :class="[
          'boton-estado-comida',
          claseVisual(comida),
          comidaEnCursoId === comida.id ? 'es-turno-actual' : '',
          estaMarcada(comida.id) ? 'seleccionada-para-entregar' : '',
        ]"
        @click="$emit('toggle-comida', persona, comida.id)"
      >
        <div class="comida-cabecera-card">
          <span class="comida-nombre-card">{{ comida.nombre }}</span>
          <span v-if="comidaEnCursoId === comida.id" class="tag-en-curso">En curso</span>
        </div>

        <div class="comida-estado-linea">
          <span class="icono-estado" aria-hidden="true">{{ icono(comida) }}</span>
          <span class="texto-estado">{{ textoEstado(comida) }}</span>
        </div>
      </button>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  persona: {
    type: Object,
    required: true,
  },
  comidasConfig: {
    type: Array,
    required: true,
  },
  comidaEnCursoId: {
    type: Number,
    required: true,
  },
  minutosActuales: {
    type: Number,
    required: true,
  },
  seleccionadasIds: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['quitar', 'toggle-comida'])

const iniciales = computed(() => {
  const ap = (props.persona.apellido || '').trim().charAt(0)
  const no = (props.persona.nombre || '').trim().charAt(0)
  return `${ap}${no}`.toUpperCase() || 'P'
})

const dniConPuntos = computed(() => {
  const limpio = String(props.persona.dni || '').replace(/\D/g, '')
  return limpio.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
})

function esComidaVencida(comida) {
  const c = props.persona.comidas?.[comida.id]
  if (!c || c.entregada) return false
  return props.minutosActuales > comida.finMin && comida.id < props.comidaEnCursoId
}

function puedeSeleccionar(comida) {
  const c = props.persona.comidas?.[comida.id]
  if (!c || c.entregada) return false
  if (esComidaVencida(comida)) return false
  return true
}

function estaMarcada(idComida) {
  const c = props.persona.comidas?.[idComida]
  if (!c) return false
  return props.seleccionadasIds.includes(c.idSolicitud)
}

function claseVisual(comida) {
  const c = props.persona.comidas?.[comida.id]
  if (!c) return 'estado-no-autorizada'
  if (c.entregada) return 'estado-entregada'
  if (esComidaVencida(comida)) return 'estado-no-retirada'
  return 'estado-pendiente'
}

function icono(comida) {
  const c = props.persona.comidas?.[comida.id]
  if (!c) return '✕'
  if (c.entregada) return '✓'
  if (esComidaVencida(comida)) return '⊘'
  return '●'
}

function textoEstado(comida) {
  const c = props.persona.comidas?.[comida.id]
  if (!c) return 'No autorizada'
  if (c.entregada) {
    return c.hora_entrega ? `Entregada (${c.hora_entrega})` : 'Entregada'
  }
  if (esComidaVencida(comida)) {
    return 'No retirada'
  }
  return 'Autorizada · Pendiente'
}
</script>

<style scoped>
.ficha-comensal-clara {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem 1.15rem;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.ficha-comensal-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.comensal-identidad {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.avatar-iniciales {
  width: 46px;
  height: 46px;
  border-radius: 10px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1d4ed8;
  font-size: 1.05rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ficha-nya {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
}

.ficha-chips-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.3rem;
}

.chip-dni,
.chip-sector,
.chip-menu {
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.18rem 0.55rem;
  border-radius: 6px;
}

.chip-dni {
  background: #e2e8f0;
  color: #1e293b;
  font-variant-numeric: tabular-nums;
}

.chip-sector {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #475569;
}

.chip-menu {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1d4ed8;
}

.btn-quitar-ficha {
  min-height: 40px;
  padding: 0.35rem 0.8rem;
  border-radius: 7px;
  border: 1px solid #fecaca;
  background: #fef2f2;
  color: #b91c1c;
  font-weight: 600;
  cursor: pointer;
}

.grilla-comidas-ficha {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.65rem;
}

.boton-estado-comida {
  min-height: 74px;
  padding: 0.65rem 0.8rem;
  border-radius: 8px;
  border: 2px solid #e2e8f0;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.35rem;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.comida-cabecera-card {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.3rem;
}

.comida-nombre-card {
  font-size: 0.95rem;
  font-weight: 700;
  color: #1e293b;
}

.tag-en-curso {
  font-size: 0.66rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 0.12rem 0.42rem;
  border-radius: 999px;
  background: #2563eb;
  color: #ffffff;
}

.comida-estado-linea {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  font-weight: 600;
}

.boton-estado-comida.estado-entregada {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #15803d;
  cursor: not-allowed;
}

.boton-estado-comida.estado-pendiente {
  background: #fffbeb;
  border-color: #fde68a;
  color: #b45309;
}

.boton-estado-comida.estado-pendiente.seleccionada-para-entregar {
  background: #eff6ff;
  border-color: #2563eb;
  color: #1d4ed8;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.16);
}

.boton-estado-comida.estado-no-retirada {
  background: #fef2f2;
  border-color: #fecaca;
  color: #b91c1c;
  cursor: not-allowed;
}

.boton-estado-comida.estado-no-autorizada {
  background: #f1f5f9;
  border-color: #e2e8f0;
  color: #64748b;
  cursor: not-allowed;
}

.boton-estado-comida.es-turno-actual {
  box-shadow: inset 0 0 0 1px #2563eb;
}

@media (max-width: 1024px) {
  .grilla-comidas-ficha {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
