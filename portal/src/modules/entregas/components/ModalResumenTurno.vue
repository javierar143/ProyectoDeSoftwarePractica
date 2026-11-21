<template>
  <div
    class="modal-kiosko-backdrop"
    role="dialog"
    aria-modal="true"
    aria-label="Resumen del turno y cierre de sesión"
  >
    <div class="modal-kiosko-card">
      <div class="modal-discreto-header">
        <div>
          <h2>Resumen Operativo · Sector Comedor</h2>
          <p class="modal-subtexto">
            Fecha: {{ fechaTexto }} · Turno activo: {{ comidaActual.nombre }}
          </p>
        </div>
        <div class="acciones-top-discreto">
          <button type="button" class="btn-secundario-claro" @click="$emit('cerrar')">
            Volver
          </button>
        </div>
      </div>

      <div class="tabs-modal-discreto">
        <button
          type="button"
          :class="['btn-modo-busq', tabActiva === 'totales' ? 'activo' : '']"
          @click="cargarTab('totales')"
        >
          Totales del día (Autorizadas vs. Entregadas)
        </button>
        <button
          type="button"
          :class="['btn-modo-busq', tabActiva === 'entregas' ? 'activo' : '']"
          @click="cargarTab('entregas')"
        >
          Entregas registradas en el turno ({{ comidaActual.nombre }})
        </button>
      </div>

      <ApiErrorMessage :error="errorApi" @retry="reintentarCarga" />
      <div v-if="cargando" class="caja-estado-vacio">Cargando información del día...</div>

      <div v-else-if="tabActiva === 'totales'">
        <div class="tarjetas-kpi-claras">
          <div class="kpi-box-claro">
            <span class="kpi-titulo">Total Autorizadas Hoy</span>
            <strong class="kpi-numero">{{ totalesCalculados.autorizadas }}</strong>
          </div>
          <div class="kpi-box-claro">
            <span class="kpi-titulo">Total Entregadas Hoy</span>
            <strong class="kpi-numero texto-verde-inst">
              {{ totalesCalculados.entregadas }}
            </strong>
          </div>
          <div class="kpi-box-claro">
            <span class="kpi-titulo">Pendientes de Retiro</span>
            <strong class="kpi-numero texto-ambar-inst">
              {{ totalesCalculados.pendientes }}
            </strong>
          </div>
          <div class="kpi-box-claro">
            <span class="kpi-titulo">No Retiradas</span>
            <strong class="kpi-numero texto-rojo-inst">
              {{ totalesCalculados.noRetiradas }}
            </strong>
          </div>
        </div>

        <div v-if="filasDesglose.length > 0" class="tabla-contenedor-claro">
          <table class="tabla-clara">
            <thead>
              <tr>
                <th>Comida</th>
                <th>Tipo de menú</th>
                <th>Autorizadas</th>
                <th>Entregadas</th>
                <th>Pendientes</th>
                <th>No retiradas</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(fila, idx) in filasDesglose" :key="idx">
                <td>
                  <strong>{{ fila.nombreComida }}</strong>
                  <span v-if="fila.vencida" class="badge-turno-vencido">Turno finalizado</span>
                </td>
                <td>{{ fila.nombreMenu }}</td>
                <td class="dato-num">{{ fila.autorizadas }}</td>
                <td class="dato-num texto-verde-inst">{{ fila.entregadas }}</td>
                <td class="dato-num texto-ambar-inst">{{ fila.pendientes }}</td>
                <td :class="['dato-num', fila.noRetiradas > 0 ? 'texto-rojo-inst' : '']">
                  {{ fila.noRetiradas }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="caja-estado-vacio">
          No hay comidas autorizadas registradas para el día de hoy.
        </div>
      </div>

      <div v-else>
        <div v-if="entregasTurno.length > 0" class="tabla-contenedor-claro">
          <table class="tabla-clara">
            <thead>
              <tr>
                <th>N.º Entrega</th>
                <th>Hora</th>
                <th>Comensal</th>
                <th>Comida / Menú</th>
                <th>Retirado por (Responsable)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in entregasTurno" :key="e.idEntrega">
                <td class="dato-num">#{{ e.idEntrega }}</td>
                <td>{{ extraerHora(e.fecha_hora) }} hs</td>
                <td>
                  <strong>{{ e.comensal_nombre || `Personal #${e.idPersonaComensal}` }}</strong>
                  <span v-if="e.comensal_dni" class="sub-dni-inline">
                    ({{ formatearPuntos(e.comensal_dni) }})
                  </span>
                </td>
                <td>
                  {{ NOMBRES_COMIDAS[e.idTipoComida] || `Comida #${e.idTipoComida}` }} ·
                  {{ NOMBRES_MENUS[e.idTipoMenu] || `Menú #${e.idTipoMenu}` }}
                </td>
                <td>
                  <strong>{{ e.responsable_nombre || `Personal #${e.idPersonalResponsable}` }}</strong>
                  <span v-if="e.responsable_dni" class="sub-dni-inline">
                    ({{ formatearPuntos(e.responsable_dni) }})
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="caja-estado-vacio">
          Todavía no se registraron entregas en el turno de {{ comidaActual.nombre }}.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ApiErrorMessage from '@/modules/shared/components/ApiErrorMessage.vue'
import { normalizeApiError } from '@/services/api/error-handler'
import { listarEntregasTurno, obtenerResumenEntregasDia } from '../services/entregas'

const props = defineProps({
  fechaHoyIso: {
    type: String,
    required: true,
  },
  fechaTexto: {
    type: String,
    required: true,
  },
  comidaActual: {
    type: Object,
    required: true,
  },
  comidasConfig: {
    type: Array,
    default: () => [],
  },
  minutosActuales: {
    type: Number,
    default: 0,
  },
})

defineEmits(['cerrar', 'logout'])

const NOMBRES_COMIDAS = {
  1: 'Desayuno',
  2: 'Almuerzo',
  3: 'Merienda',
  4: 'Cena',
}

const NOMBRES_MENUS = {
  1: 'General',
  2: 'Vegetariano',
  3: 'Celíaco',
}

const tabActiva = ref('totales')
const cargando = ref(false)
const errorApi = ref(null)
const parametrosReintento = ref(null)
const resumenDia = ref(null)
const entregasTurno = ref([])

function formatearPuntos(valor) {
  const limpio = String(valor || '').replace(/\D/g, '')
  return limpio.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

function esComidaDeTurnoFinalizado(idTipoComida) {
  const idNum = Number(idTipoComida)
  const cfg = props.comidasConfig.find((c) => Number(c.id) === idNum)
  if (!cfg) return false
  return props.minutosActuales > cfg.finMin && idNum < Number(props.comidaActual?.id || 1)
}

const filasDesglose = computed(() => {
  const lista = resumenDia.value?.desglose || []
  return lista.map((fila) => {
    const autorizadas = Number(fila.total_autorizado || 0)
    const entregadas = Number(fila.total_entregado || 0)
    const sinEntregar = Math.max(0, autorizadas - entregadas)
    const vencida = esComidaDeTurnoFinalizado(fila.idTipoComida)

    return {
      idTipoComida: fila.idTipoComida,
      idTipoMenu: fila.idTipoMenu,
      nombreComida: NOMBRES_COMIDAS[fila.idTipoComida] || `Comida #${fila.idTipoComida}`,
      nombreMenu: NOMBRES_MENUS[fila.idTipoMenu] || `Menú #${fila.idTipoMenu}`,
      autorizadas,
      entregadas,
      pendientes: vencida ? 0 : sinEntregar,
      noRetiradas: vencida ? sinEntregar : 0,
      vencida,
    }
  })
})

const totalesCalculados = computed(() => {
  let autorizadas = 0
  let entregadas = 0
  let pendientes = 0
  let noRetiradas = 0

  for (const f of filasDesglose.value) {
    autorizadas += f.autorizadas
    entregadas += f.entregadas
    pendientes += f.pendientes
    noRetiradas += f.noRetiradas
  }

  return { autorizadas, entregadas, pendientes, noRetiradas }
})

function extraerHora(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso).slice(11, 16)
  return d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', hour12: false })
}

async function cargarTab(tab, paramsOverride = null) {
  tabActiva.value = tab
  cargando.value = true
  errorApi.value = null
  const params = paramsOverride || (tab === 'totales'
    ? { fecha: props.fechaHoyIso }
    : { fecha: props.fechaHoyIso, tipo_comida: props.comidaActual.id })
  try {
    if (tab === 'totales') {
      resumenDia.value = await obtenerResumenEntregasDia(params)
    } else {
      const lista = await listarEntregasTurno(params)
      entregasTurno.value = Array.isArray(lista) ? lista : []
    }
    parametrosReintento.value = null
  } catch (err) {
    const status = err?.response?.status ?? err?.status
    if (status !== 503) {
      errorApi.value = normalizeApiError(err)
      parametrosReintento.value = { tab, params }
    }
  } finally {
    cargando.value = false
  }
}

function reintentarCarga() {
  if (cargando.value || !parametrosReintento.value) return
  return cargarTab(parametrosReintento.value.tab, parametrosReintento.value.params)
}

function recargarDatosAfectados() {
  if (tabActiva.value === 'totales') {
    return obtenerResumenEntregasDia({ fecha: props.fechaHoyIso }).then((data) => {
      resumenDia.value = data
    })
  }
  return listarEntregasTurno({
    fecha: props.fechaHoyIso,
    tipo_comida: props.comidaActual.id,
  }).then((data) => {
    entregasTurno.value = Array.isArray(data) ? data : []
  })
}

defineExpose({ recargarDatosAfectados })

onMounted(() => {
  cargarTab('totales')
})
</script>

<style scoped>
.modal-kiosko-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
  z-index: 90;
}

.modal-kiosko-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.4rem;
  max-width: 880px;
  width: 100%;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.22);
  display: flex;
  flex-direction: column;
  gap: 1rem;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: #1e293b;
}

.modal-discreto-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.modal-discreto-header h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
}

.modal-subtexto {
  margin: 0.2rem 0 0;
  font-size: 0.88rem;
  color: #64748b;
}

.acciones-top-discreto {
  display: flex;
  gap: 0.5rem;
}

.btn-secundario-claro,
.btn-cerrar-sesion {
  min-height: 42px;
  padding: 0.45rem 1rem;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-secundario-claro {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #1e293b;
}

.btn-cerrar-sesion {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
}

.tabs-modal-discreto {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.35rem;
  background: #f1f5f9;
  padding: 0.3rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
}

.btn-modo-busq {
  min-height: 40px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: #475569;
  font-size: 0.86rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-modo-busq.activo {
  background: #2563eb;
  color: #ffffff;
}

.tarjetas-kpi-claras {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin-bottom: 0.9rem;
}

.kpi-box-claro {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.8rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.kpi-titulo {
  font-size: 0.74rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
}

.kpi-numero {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
}

.texto-verde-inst {
  color: #15803d;
}

.texto-ambar-inst {
  color: #b45309;
}

.texto-rojo-inst {
  color: #b91c1c;
}

.badge-turno-vencido {
  display: inline-block;
  margin-left: 0.45rem;
  padding: 0.12rem 0.45rem;
  font-size: 0.7rem;
  font-weight: 600;
  border-radius: 999px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
}

.tabla-contenedor-claro {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow-x: auto;
}

.tabla-clara {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.86rem;
}

.tabla-clara th,
.tabla-clara td {
  padding: 0.65rem 0.85rem;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
}

.tabla-clara th {
  background: #f8fafc;
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.sub-dni-inline {
  margin-left: 0.35rem;
  color: #64748b;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.dato-num {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.caja-estado-vacio {
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  padding: 2rem 1.5rem;
  text-align: center;
  color: #64748b;
}

@media (max-width: 767px) {
  .tarjetas-kpi-claras {
    grid-template-columns: repeat(2, 1fr);
  }

  .tabs-modal-discreto {
    grid-template-columns: 1fr;
  }
}
</style>