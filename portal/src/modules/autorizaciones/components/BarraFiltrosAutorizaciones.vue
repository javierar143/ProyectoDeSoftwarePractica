<template>
  <section class="barra-filtros" aria-label="Filtros de autorización">
    <div class="filtros-fila-campos">
      <div class="campo-filtro campo-fecha">
        <label for="filtro-fecha-desde">Desde</label>
        <div class="caja-fecha-nativa">
          <input
            id="filtro-fecha-desde"
            v-model="filtrosTexto.fecha_desde"
            type="text"
            inputmode="numeric"
            placeholder="dd/mm/aaaa"
            maxlength="10"
            :class="{ 'input-invalido': erroresFiltro.fecha_desde }"
            @input="formatearInputFecha('fecha_desde')"
            @blur="validarFiltrosCliente"
          />
          <span class="icono-cal-nativo" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
              <line x1="8" y1="2" x2="8" y2="6" />
              <line x1="3" y1="10" x2="21" y2="10" />
            </svg>
          </span>
          <input
            :value="filtros.fecha_desde"
            type="date"
            class="date-overlay"
            aria-label="Seleccionar fecha desde en calendario"
            @change="alCambiarDateNativo('fecha_desde', $event.target.value)"
          />
        </div>
        <small v-if="erroresFiltro.fecha_desde" class="error-filtro" role="alert">
          {{ erroresFiltro.fecha_desde }}
        </small>
      </div>

      <div class="campo-filtro campo-fecha">
        <label for="filtro-fecha-hasta">Hasta</label>
        <div class="caja-fecha-nativa">
          <input
            id="filtro-fecha-hasta"
            v-model="filtrosTexto.fecha_hasta"
            type="text"
            inputmode="numeric"
            placeholder="dd/mm/aaaa"
            maxlength="10"
            :class="{ 'input-invalido': erroresFiltro.fecha_hasta }"
            @input="formatearInputFecha('fecha_hasta')"
            @blur="validarFiltrosCliente"
          />
          <span class="icono-cal-nativo" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
              <line x1="8" y1="2" x2="8" y2="6" />
              <line x1="3" y1="10" x2="21" y2="10" />
            </svg>
          </span>
          <input
            :value="filtros.fecha_hasta"
            type="date"
            class="date-overlay"
            aria-label="Seleccionar fecha hasta en calendario"
            @change="alCambiarDateNativo('fecha_hasta', $event.target.value)"
          />
        </div>
        <small v-if="erroresFiltro.fecha_hasta" class="error-filtro" role="alert">
          {{ erroresFiltro.fecha_hasta }}
        </small>
      </div>

      <div class="campo-filtro">
        <label for="filtro-sector">Sector</label>
        <select
          id="filtro-sector"
          :value="filtros.sector"
          @change="actualizarCampo('sector', $event.target.value)"
        >
          <option value="">Todos los sectores</option>
          <option v-for="sec in sectoresDisponibles" :key="sec.id" :value="sec.id">
            {{ sec.nombre }}{{ sec.estado === 'inactivo' ? ' (Inactivo)' : '' }}
          </option>
        </select>
      </div>

      <div class="campo-filtro">
        <label for="filtro-comida">Comida</label>
        <select
          id="filtro-comida"
          :value="filtros.tipo_comida"
          @change="actualizarCampo('tipo_comida', $event.target.value)"
        >
          <option value="">Todas las comidas</option>
          <option v-for="(nombre, id) in COMIDAS_POR_ID" :key="id" :value="id">
            {{ nombre }}
          </option>
        </select>
      </div>

      <div class="campo-filtro">
        <label for="filtro-menu">Tipo de menú</label>
        <select
          id="filtro-menu"
          :value="filtros.tipo_menu"
          @change="actualizarCampo('tipo_menu', $event.target.value)"
        >
          <option value="">Todos los menús</option>
          <option v-for="(nombre, id) in MENUS_POR_ID" :key="id" :value="id">
            {{ nombre }}
          </option>
        </select>
      </div>

      <div class="campo-filtro campo-corto">
        <label for="filtro-condicion">Condición</label>
        <select
          id="filtro-condicion"
          :value="filtros.condicion"
          @change="actualizarCampo('condicion', $event.target.value)"
        >
          <option value="">Todas</option>
          <option value="regular">Regular</option>
          <option value="excepcion">Excepción</option>
        </select>
      </div>

      <div class="campo-filtro campo-corto">
        <label for="filtro-estado">Estado</label>
        <select
          id="filtro-estado"
          :value="filtros.estado"
          @change="actualizarCampo('estado', $event.target.value)"
        >
          <option value="">Todos</option>
          <option value="confirmado">Pendiente</option>
          <option value="autorizado">Autorizado</option>
          <option value="rechazado">Rechazado</option>
        </select>
      </div>
    </div>

    <div class="filtros-acciones-barra">
      <div class="filtros-botones">
        <button type="button" class="btn-primario" :disabled="cargando" @click="ejecutarBusqueda">
          Buscar
        </button>
        <button type="button" :disabled="cargando" @click="$emit('limpiar')">
          Limpiar
        </button>
      </div>

      <div class="filtros-exportacion">
        <button
          type="button"
          class="btn-secundario"
          :disabled="cargando"
          @click="$emit('toggle-resumen')"
        >
          {{ mostrarResumen ? 'Ocultar totales' : 'Ver totales del período' }}
        </button>
        <button
          type="button"
          class="btn-csv"
          :disabled="cargando || exportandoCsv"
          @click="ejecutarExportacion('personas')"
        >
          Exportar Personas (CSV)
        </button>
        <button
          type="button"
          class="btn-csv"
          :disabled="cargando || exportandoCsv"
          @click="ejecutarExportacion('totales')"
        >
          Exportar Totales (CSV)
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  filtros: {
    type: Object,
    required: true,
  },
  sectoresDisponibles: {
    type: Array,
    default: () => [],
  },
  mostrarResumen: {
    type: Boolean,
    default: false,
  },
  cargando: {
    type: Boolean,
    default: false,
  },
  exportandoCsv: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'update:filtros',
  'buscar',
  'limpiar',
  'toggle-resumen',
  'exportar-csv',
])

const COMIDAS_POR_ID = {
  1: 'Desayuno',
  2: 'Almuerzo',
  3: 'Merienda',
  4: 'Cena',
}

const MENUS_POR_ID = {
  1: 'General',
  2: 'Vegetariano',
  3: 'Celíaco',
}

function formatearFechaDdMmAaaa(valorFecha) {
  if (!valorFecha) return ''
  const iso = String(valorFecha).slice(0, 10)
  const partes = iso.split('-')
  if (partes.length !== 3) return String(valorFecha)
  return `${partes[2]}/${partes[1]}/${partes[0]}`
}

const filtrosTexto = ref({
  fecha_desde: formatearFechaDdMmAaaa(props.filtros.fecha_desde),
  fecha_hasta: formatearFechaDdMmAaaa(props.filtros.fecha_hasta),
})

const erroresFiltro = ref({
  fecha_desde: '',
  fecha_hasta: '',
})

watch(
  () => [props.filtros.fecha_desde, props.filtros.fecha_hasta],
  ([nuevaDesde, nuevaHasta]) => {
    filtrosTexto.value.fecha_desde = formatearFechaDdMmAaaa(nuevaDesde)
    filtrosTexto.value.fecha_hasta = formatearFechaDdMmAaaa(nuevaHasta)
    erroresFiltro.value.fecha_desde = ''
    erroresFiltro.value.fecha_hasta = ''
  }
)

function actualizarCampo(campo, valor) {
  emit('update:filtros', {
    ...props.filtros,
    [campo]: valor,
  })
}

function alCambiarDateNativo(campo, nuevoIso) {
  if (!nuevoIso) return
  filtrosTexto.value[campo] = formatearFechaDdMmAaaa(nuevoIso)
  erroresFiltro.value[campo] = ''
  emit('update:filtros', {
    ...props.filtros,
    [campo]: nuevoIso,
  })
}

function formatearInputFecha(campo) {
  const soloDigitos = String(filtrosTexto.value[campo] || '')
    .replace(/\D/g, '')
    .slice(0, 8)

  let resultado = soloDigitos
  if (soloDigitos.length > 4) {
    resultado = `${soloDigitos.slice(0, 2)}/${soloDigitos.slice(2, 4)}/${soloDigitos.slice(4)}`
  } else if (soloDigitos.length > 2) {
    resultado = `${soloDigitos.slice(0, 2)}/${soloDigitos.slice(2)}`
  }
  filtrosTexto.value[campo] = resultado
  erroresFiltro.value[campo] = ''
}

function parsearDdMmAaaaAIso(texto) {
  const limpio = String(texto || '').trim()
  if (!limpio) return { iso: '', error: '' }
  const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(limpio)
  if (!match) return { iso: null, error: 'Usá dd/mm/aaaa.' }

  const dia = Number(match[1])
  const mes = Number(match[2])
  const anio = Number(match[3])
  if (mes < 1 || mes > 12 || dia < 1 || dia > 31) {
    return { iso: null, error: 'Fecha inválida.' }
  }

  const fechaObj = new Date(anio, mes - 1, dia)
  const esValida =
    fechaObj.getFullYear() === anio &&
    fechaObj.getMonth() === mes - 1 &&
    fechaObj.getDate() === dia

  if (!esValida) return { iso: null, error: 'Fecha inexistente.' }
  const iso = `${anio}-${String(mes).padStart(2, '0')}-${String(dia).padStart(2, '0')}`
  return { iso, error: '' }
}

function validarFiltrosCliente() {
  const desdeRes = parsearDdMmAaaaAIso(filtrosTexto.value.fecha_desde)
  const hastaRes = parsearDdMmAaaaAIso(filtrosTexto.value.fecha_hasta)

  erroresFiltro.value.fecha_desde = desdeRes.error
  erroresFiltro.value.fecha_hasta = hastaRes.error

  if (desdeRes.error || hastaRes.error) return false

  if (desdeRes.iso && hastaRes.iso && desdeRes.iso > hastaRes.iso) {
    erroresFiltro.value.fecha_hasta = 'Hasta < Desde.'
    return false
  }

  emit('update:filtros', {
    ...props.filtros,
    fecha_desde: desdeRes.iso || props.filtros.fecha_desde,
    fecha_hasta: hastaRes.iso || props.filtros.fecha_hasta,
  })
  return true
}

function ejecutarBusqueda() {
  if (!validarFiltrosCliente()) return
  emit('buscar')
}

function ejecutarExportacion(tipo) {
  if (!validarFiltrosCliente()) return
  emit('exportar-csv', tipo)
}
</script>

<style scoped>
.barra-filtros {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.95rem 1.1rem;
  margin-bottom: 1.1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.filtros-fila-campos {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 0.75rem;
}

.campo-filtro {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #64748b;
  flex: 1 1 145px;
  min-width: 135px;
}

.campo-filtro.campo-fecha {
  flex: 0 0 142px;
  min-width: 142px;
}

.campo-filtro.campo-corto {
  flex: 0 1 125px;
  min-width: 115px;
}

.caja-fecha-nativa {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.caja-fecha-nativa input[type='text'] {
  width: 100%;
  height: 36px;
  padding: 0.3rem 1.85rem 0.3rem 0.55rem;
  border: 1px solid #cbd5e1;
  border-radius: 7px;
  background: #ffffff;
  color: #1e293b;
  font-size: 0.83rem;
  box-sizing: border-box;
}

.caja-fecha-nativa input[type='text'].input-invalido {
  border-color: #b91c1c;
  background: #fef2f2;
}

.icono-cal-nativo {
  position: absolute;
  right: 8px;
  color: #64748b;
  display: inline-flex;
  align-items: center;
  pointer-events: none;
}

.date-overlay {
  position: absolute;
  right: 0;
  top: 0;
  width: 32px;
  height: 36px;
  opacity: 0;
  cursor: pointer;
}

.campo-filtro select {
  height: 36px;
  padding: 0.3rem 0.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 7px;
  background: #ffffff;
  color: #1e293b;
  font-size: 0.83rem;
  width: 100%;
  box-sizing: border-box;
}

.error-filtro {
  font-size: 0.7rem;
  font-weight: 600;
  color: #b91c1c;
}

.filtros-acciones-barra {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}

.filtros-botones,
.filtros-exportacion {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
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

.btn-primario {
  background: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
}

.btn-primario:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-csv {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #1d4ed8;
}

.btn-csv:hover:not(:disabled) {
  background: #dbeafe;
}

button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 767px) {
  .campo-filtro,
  .campo-filtro.campo-fecha,
  .campo-filtro.campo-corto {
    flex: 1 1 100%;
  }

  .filtros-botones,
  .filtros-exportacion {
    width: 100%;
  }

  .filtros-botones button,
  .filtros-exportacion button {
    flex: 1;
  }
}
</style>