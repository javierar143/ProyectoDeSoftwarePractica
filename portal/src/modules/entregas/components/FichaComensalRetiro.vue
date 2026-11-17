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
  border-radius: 12px;
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
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: #ccfbf1;
  border: 1px solid #99f6e4;
  color: #0f766e;
  font-size: 1.1rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ficha-nya {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 800;
  color: #0f172a;
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
  font-size: 0.8rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 6px;
}

.chip-dni {
  background: #e2e8f0;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.chip-sector {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #334155;
}

.chip-menu {
  background: #f0fdfa;
  border: 1px solid #99f6e4;
  color: #0f766e;
}

.btn-quitar-ficha {
  min-height: 48px;
  padding: 0.4rem 0.85rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #475569;
  font-weight: 700;
  cursor: pointer;
}

.grilla-comidas-ficha {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.65rem;
}

.boton-estado-comida {
  min-height: 76px;
  padding: 0.65rem 0.8rem;
  border-radius: 10px;
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
  font-size: 0.98rem;
  font-weight: 800;
  color: #0f172a;
}

.tag-en-curso {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 0.12rem 0.4rem;
  border-radius: 999px;
  background: #0f766e;
  color: #ffffff;
}

.comida-estado-linea {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.82rem;
  font-weight: 700;
}

/* 1. Entregada (Verde claro) */
.boton-estado-comida.estado-entregada {
  background: #f0fdf4;
  border-color: #86efac;
  color: #166534;
  cursor: not-allowed;
}

/* 2. Autorizada Pendiente vigente (Ámbar claro) */
.boton-estado-comida.estado-pendiente {
  background: #fffbeb;
  border-color: #fcd34d;
  color: #92400e;
}

.boton-estado-comida.estado-pendiente.seleccionada-para-entregar {
  background: #ecfdf5;
  border-color: #0f766e;
  color: #0f766e;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.18);
}

/* 3. No retirada - Turno ya vencido (Rojo suave bloqueado) */
.boton-estado-comida.estado-no-retirada {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #b91c1c;
  cursor: not-allowed;
}

/* 4. No Autorizada (Gris claro neutro) */
.boton-estado-comida.estado-no-autorizada {
  background: #f1f5f9;
  border-color: #e2e8f0;
  color: #64748b;
  cursor: not-allowed;
}

.boton-estado-comida.es-turno-actual {
  box-shadow: inset 0 0 0 1px #0f766e;
}

@media (max-width: 1024px) {
  .grilla-comidas-ficha {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>