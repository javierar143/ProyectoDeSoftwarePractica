<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
  },
  sectores: {
    type: Array,
    default: () => [],
  },
  tiposComida: {
    type: Array,
    default: () => [],
  },
  tiposMenu: {
    type: Array,
    default: () => [],
  },
  cargando: {
    type: Boolean,
    default: false,
  },
  exportando: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'update:modelValue',
  'aplicar',
  'limpiar',
  'exportar-csv',
])

const filtrosLocales = ref({ ...props.modelValue })
const errorFechas = ref('')

watch(
  () => props.modelValue,
  (nuevo) => {
    filtrosLocales.value = { ...nuevo }
  },
  { deep: true }
)

function validarRangoFechas() {
  const { fecha_desde, fecha_hasta } = filtrosLocales.value
  if (fecha_desde && fecha_hasta && fecha_desde > fecha_hasta) {
    errorFechas.value = 'La fecha "Desde" no puede ser posterior a la fecha "Hasta".'
    return false
  }
  errorFechas.value = ''
  return true
}

function handleSubmit() {
  if (!validarRangoFechas()) return
  emit('update:modelValue', { ...filtrosLocales.value })
  emit('aplicar')
}

function handleLimpiar() {
  errorFechas.value = ''
  emit('limpiar')
}

function handleExportar(tipo) {
  if (!validarRangoFechas()) return
  if (!filtrosLocales.value.fecha_desde || !filtrosLocales.value.fecha_hasta) {
    errorFechas.value = 'Seleccioná "Fecha desde" y "Fecha hasta" para exportar a CSV.'
    return
  }
  emit('update:modelValue', { ...filtrosLocales.value })
  emit('exportar-csv', tipo)
}
</script>

<template>
  <section class="card-filtros" aria-label="Filtros de reportes">
    <form class="form-filtros" @submit.prevent="handleSubmit" novalidate>
      <div class="grid-filtros">
        <div class="campo">
          <label for="filtro-fecha-desde">Fecha desde</label>
          <input
            id="filtro-fecha-desde"
            v-model="filtrosLocales.fecha_desde"
            type="date"
          />
        </div>

        <div class="campo">
          <label for="filtro-fecha-hasta">Fecha hasta</label>
          <input
            id="filtro-fecha-hasta"
            v-model="filtrosLocales.fecha_hasta"
            type="date"
          />
        </div>

        <div class="campo">
          <label for="filtro-sector">Sector</label>
          <select id="filtro-sector" v-model="filtrosLocales.sector">
            <option value="">Todos los sectores</option>
            <option
              v-for="sec in sectores"
              :key="sec.idSector ?? sec.id"
              :value="sec.idSector ?? sec.id"
            >
              {{ sec.nombre }}
            </option>
          </select>
        </div>

        <div class="campo">
          <label for="filtro-comida">Tipo de comida</label>
          <select id="filtro-comida" v-model="filtrosLocales.tipo_comida">
            <option value="">Todas las comidas</option>
            <option
              v-for="com in tiposComida"
              :key="com.idTipoComida ?? com.id"
              :value="com.idTipoComida ?? com.id"
            >
              {{ com.nombre }}
            </option>
          </select>
        </div>

        <div class="campo">
          <label for="filtro-menu">Tipo de menú</label>
          <select id="filtro-menu" v-model="filtrosLocales.tipo_menu">
            <option value="">Todos los menús</option>
            <option
              v-for="menu in tiposMenu"
              :key="menu.idTipoMenu ?? menu.id"
              :value="menu.idTipoMenu ?? menu.id"
            >
              {{ menu.nombre }}
            </option>
          </select>
        </div>

        <div class="campo">
          <label for="filtro-estado">Estado</label>
          <select id="filtro-estado" v-model="filtrosLocales.estado">
            <option value="">Todos los estados</option>
            <option value="confirmado">Confirmado</option>
            <option value="autorizado">Autorizado</option>
            <option value="rechazado">Rechazado</option>
          </select>
        </div>

        <div class="campo">
          <label for="filtro-condicion">Condición</label>
          <select id="filtro-condicion" v-model="filtrosLocales.condicion">
            <option value="todas">Todas</option>
            <option value="regular">Regular</option>
            <option value="excepcion">Excepción</option>
          </select>
        </div>

        <div class="campo">
          <label for="filtro-agrupamiento">Evolución agrupada por</label>
          <select id="filtro-agrupamiento" v-model="filtrosLocales.agrupamiento">
            <option value="dia">Día</option>
            <option value="semana">Semana</option>
            <option value="mes">Mes</option>
          </select>
        </div>
      </div>

      <p v-if="errorFechas" class="error-validacion" role="alert">
        {{ errorFechas }}
      </p>

      <div class="acciones-filtros">
        <div class="grupo-botones">
          <button type="submit" class="btn-primario" :disabled="cargando">
            {{ cargando ? 'Consultando...' : 'Aplicar filtros' }}
          </button>
          <button
            type="button"
            class="btn-secundario"
            :disabled="cargando"
            @click="handleLimpiar"
          >
            Limpiar
          </button>
        </div>

        <div class="grupo-botones">
          <button
            type="button"
            class="btn-csv"
            :disabled="cargando || exportando"
            @click="handleExportar('authorizations')"
          >
            Exportar CSV Autorizaciones
          </button>
          <button
            type="button"
            class="btn-csv"
            :disabled="cargando || exportando"
            @click="handleExportar('deliveries')"
          >
            Exportar CSV Entregas
          </button>
        </div>
      </div>
    </form>
  </section>
</template>

<style scoped>
.card-filtros {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.grid-filtros {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.campo {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.campo label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #334155;
}

.campo input,
.campo select {
  padding: 0.5rem 0.65rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
  background: #ffffff;
}

.error-validacion {
  margin-top: 0.75rem;
  color: #b91c1c;
  font-size: 0.88rem;
  font-weight: 500;
}

.acciones-filtros {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid #f1f5f9;
}

.grupo-botones {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.btn-primario,
.btn-secundario,
.btn-csv {
  padding: 0.55rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
}

.btn-primario {
  background: #2563eb;
  color: #ffffff;
}

.btn-primario:disabled,
.btn-secundario:disabled,
.btn-csv:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secundario {
  background: #f8fafc;
  color: #334155;
  border-color: #cbd5e1;
}

.btn-csv {
  background: #ecfdf5;
  color: #047857;
  border-color: #a7f3d0;
}
</style>