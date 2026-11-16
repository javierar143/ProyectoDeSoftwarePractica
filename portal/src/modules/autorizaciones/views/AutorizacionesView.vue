<template>
  <main class="autorizaciones-view">
    <header class="encabezado-modulo">
      <h1>Autorización de Pedidos</h1>
      <p>Revisión, autorización nominada y rechazo de pedidos por sector.</p>
    </header>

    <div v-if="mensajeFeedback.texto" :class="['alerta', `alerta-${mensajeFeedback.tipo}`]" role="alert">
      {{ mensajeFeedback.texto }}
    </div>

    <section class="barra-filtros" aria-label="Filtros de autorización">
      <label>
        Desde
        <input v-model="filtros.fecha_desde" type="date" />
      </label>
      <label>
        Hasta
        <input v-model="filtros.fecha_hasta" type="date" />
      </label>
      <label>
        Estado
        <select v-model="filtros.estado">
          <option value="">Todos</option>
          <option value="confirmado">Confirmado</option>
          <option value="autorizado">Autorizado</option>
          <option value="rechazado">Rechazado</option>
        </select>
      </label>
      <label>
        Condición
        <select v-model="filtros.condicion">
          <option value="">Todas</option>
          <option value="regular">Regular</option>
          <option value="excepcion">Excepción</option>
        </select>
      </label>
      <div class="filtros-botones">
        <button type="button" class="btn-primario" :disabled="cargando" @click="cargarPedidos">
          Buscar
        </button>
        <button type="button" :disabled="cargando" @click="limpiarFiltros">
          Limpiar
        </button>
      </div>
    </section>

    <div v-if="cargando" class="estado-carga">Cargando pedidos...</div>

    <div v-else-if="pedidos.length === 0" class="estado-vacio">
      No se encontraron pedidos para los filtros seleccionados.
    </div>

    <div v-else class="tabla-contenedor">
      <table class="tabla-pedidos">
        <thead>
          <tr>
            <th>ID Pedido</th>
            <th>Fecha</th>
            <th>Sector</th>
            <th>Cantidad</th>
            <th>Estado</th>
            <th>Acción</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pedido in pedidos" :key="pedido.idPedido ?? pedido.id">
            <td>#{{ pedido.idPedido ?? pedido.id }}</td>
            <td>{{ (pedido.fecha_desde || pedido.fecha || '-').slice(0, 10) }}</td>
            <td>{{ resolverNombreSector(pedido) }}</td>
            <td>{{ pedido.cantidad_pedida ?? '-' }}</td>
            <td>{{ pedido.estado || '-' }}</td>
            <td>
              <button
                type="button"
                class="btn-detalle"
                @click="abrirDetallePedido(pedido.idPedido ?? pedido.id)"
              >
                Revisar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <DetallePedido
      v-if="pedidoSeleccionado"
      :detalle="pedidoSeleccionado"
      :guardando="guardando"
      @cerrar="pedidoSeleccionado = null"
      @confirmar-autorizacion="prepararConfirmacion('autorizar', $event)"
      @confirmar-rechazo="prepararConfirmacion('rechazar', $event)"
    />

    <div
      v-if="confirmacionPendiente"
      class="modal-confirmacion-backdrop"
      role="alertdialog"
      aria-modal="true"
    >
      <div class="modal-confirmacion-box">
        <h3>Confirmar operación</h3>

        <div v-if="confirmacionPendiente.tipo === 'autorizar'" class="detalle-confirmacion-lista">
          <p>
            ¿Confirmás registrar la autorización del
            <strong>pedido #{{ confirmacionPendiente.payload?.idPedido }}</strong>?
          </p>
          <p class="sub-resumen">
            Autorizadas:
            <strong>
              {{
                (confirmacionPendiente.payload?.resumenSolicitudes || []).filter(
                  (r) => r.estado === 'AUTORIZADA'
                ).length
              }}
            </strong>
            de
            <strong>{{ (confirmacionPendiente.payload?.resumenSolicitudes || []).length }}</strong>
          </p>
          <ul class="lista-resumen-sol">
            <li
              v-for="item in confirmacionPendiente.payload?.resumenSolicitudes || []"
              :key="item.idSolicitud"
              :class="item.estado === 'AUTORIZADA' ? 'item-aut' : 'item-no-aut'"
            >
              <span>
                <strong>#{{ item.idSolicitud }}</strong> · {{ item.persona }} —
                <strong>{{ item.comida }}</strong>
              </span>
              <span class="badge-mini">
                {{ item.estado === 'AUTORIZADA' ? '✓ Autorizada' : '✕ No autorizada' }}
              </span>
            </li>
          </ul>
        </div>

        <p v-else>
          ¿Confirmás rechazar el pedido #{{ confirmacionPendiente.payload?.idPedido }} completo por el
          motivo indicado? Esta acción no se puede deshacer.
        </p>

        <div class="confirmacion-acciones">
          <button type="button" :disabled="guardando" @click="confirmacionPendiente = null">
            Volver
          </button>
          <button
            type="button"
            class="btn-ejecutar"
            :disabled="guardando"
            @click="ejecutarOperacionConfirmada"
          >
            {{ guardando ? 'Procesando...' : 'Sí, confirmar' }}
          </button>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import DetallePedido from '../components/DetallePedido.vue'
import {
  guardarAutorizacionPedido,
  listarPedidosAutorizacion,
  obtenerDetalleAutorizacion,
  rechazarPedidoCompleto,
} from '../services/autorizaciones'

const SECTORES_POR_ID = {
  1: 'Administración',
  2: 'Guardia',
  3: 'Quirófano',
  4: 'Internación',
  5: 'Laboratorio',
  6: 'Servicio de Alimentación',
}

function obtenerFechaLocalIso() {
  const hoy = new Date()
  const anio = hoy.getFullYear()
  const mes = String(hoy.getMonth() + 1).padStart(2, '0')
  const dia = String(hoy.getDate()).padStart(2, '0')
  return `${anio}-${mes}-${dia}`
}

const hoyIso = obtenerFechaLocalIso()

const filtros = ref({
  fecha_desde: hoyIso,
  fecha_hasta: hoyIso,
  sector: '',
  tipo_comida: '',
  tipo_menu: '',
  condicion: '',
  estado: 'confirmado',
})

const pedidos = ref([])
const pedidoSeleccionado = ref(null)
const confirmacionPendiente = ref(null)
const cargando = ref(false)
const guardando = ref(false)
const mensajeFeedback = ref({ tipo: '', texto: '' })

function resolverNombreSector(pedido) {
  if (pedido?.nombreSector) return pedido.nombreSector
  if (typeof pedido?.sector === 'string' && pedido.sector.trim()) return pedido.sector
  const idSector = Number(pedido?.idSector ?? pedido?.sector_id ?? pedido?.sector)
  if (Number.isInteger(idSector) && SECTORES_POR_ID[idSector]) {
    return SECTORES_POR_ID[idSector]
  }
  return idSector ? `Sector #${idSector}` : '-'
}

function limpiarParametrosVacios(obj) {
  return Object.fromEntries(
    Object.entries(obj).filter(([, val]) => val !== '' && val !== null && val !== undefined)
  )
}

async function cargarPedidos() {
  cargando.value = true
  mensajeFeedback.value = { tipo: '', texto: '' }
  try {
    const data = await listarPedidosAutorizacion(limpiarParametrosVacios(filtros.value))
    pedidos.value = Array.isArray(data) ? data : Array.isArray(data?.items) ? data.items : []
  } catch (err) {
    if (err?.isConflict) {
      mensajeFeedback.value = {
        tipo: 'advertencia',
        texto: err.message || 'El pedido cambió mientras se revisaba. Se actualizaron los datos.',
      }
    } else if (err?.status === 400) {
      mensajeFeedback.value = {
        tipo: 'error',
        texto: err.message || 'Los filtros ingresados no son válidos.',
      }
    } else {
      mensajeFeedback.value = {
        tipo: 'error',
        texto: err?.message || 'No se pudieron cargar los pedidos. Intentá nuevamente.',
      }
    }
  } finally {
    cargando.value = false
  }
}

function limpiarFiltros() {
  filtros.value = {
    fecha_desde: hoyIso,
    fecha_hasta: hoyIso,
    sector: '',
    tipo_comida: '',
    tipo_menu: '',
    condicion: '',
    estado: 'confirmado',
  }
  cargarPedidos()
}

async function abrirDetallePedido(idPedido) {
  mensajeFeedback.value = { tipo: '', texto: '' }
  try {
    pedidoSeleccionado.value = await obtenerDetalleAutorizacion(idPedido)
  } catch (err) {
    mensajeFeedback.value = {
      tipo: 'error',
      texto: err?.isNotFound
        ? 'El pedido seleccionado no existe o fue eliminado.'
        : err?.message || 'No se pudo obtener el detalle del pedido.',
    }
  }
}

function prepararConfirmacion(tipo, payload) {
  confirmacionPendiente.value = { tipo, payload }
}

async function ejecutarOperacionConfirmada() {
  if (!confirmacionPendiente.value) return
  const { tipo, payload } = confirmacionPendiente.value
  guardando.value = true

  try {
    if (tipo === 'autorizar') {
      await guardarAutorizacionPedido(payload.idPedido, {
        solicitudes: payload.solicitudes,
        ultima_modificacion: payload.ultima_modificacion,
      })
      mensajeFeedback.value = {
        tipo: 'exito',
        texto: `Autorización del pedido #${payload.idPedido} guardada correctamente.`,
      }
    } else if (tipo === 'rechazar') {
      await rechazarPedidoCompleto(payload.idPedido, {
        motivo: payload.motivo,
      })
      mensajeFeedback.value = {
        tipo: 'exito',
        texto: `Pedido #${payload.idPedido} rechazado correctamente.`,
      }
    }

    confirmacionPendiente.value = null
    pedidoSeleccionado.value = null
    await cargarPedidos()
  } catch (err) {
    confirmacionPendiente.value = null

    if (err?.isConflict) {
      mensajeFeedback.value = {
        tipo: 'advertencia',
        texto:
          err.message ||
          'Conflicto de estado (el pedido fue modificado o tiene entregas). Se recargaron los datos.',
      }
      await cargarPedidos()
      if (pedidoSeleccionado.value?.idPedido === payload.idPedido) {
        pedidoSeleccionado.value = await obtenerDetalleAutorizacion(payload.idPedido)
      }
    } else if (err?.status === 400) {
      mensajeFeedback.value = {
        tipo: 'error',
        texto: err.message || 'Datos inválidos al procesar la operación.',
      }
    } else {
      mensajeFeedback.value = {
        tipo: 'error',
        texto: err?.message || 'Ocurrió un error al guardar la operación. Intentá nuevamente.',
      }
    }
  } finally {
    guardando.value = false
  }
}

onMounted(() => {
  cargarPedidos()
})
</script>

<style scoped>
.autorizaciones-view {
  padding: 1rem;
  max-width: 1200px;
  margin: 0 auto;
}

.encabezado-modulo h1 {
  margin: 0;
  font-size: 1.5rem;
}

.encabezado-modulo p {
  margin: 0.25rem 0 1rem;
  color: #475569;
}

.barra-filtros {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: flex-end;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 0.85rem 1rem;
  margin-bottom: 1rem;
}

.barra-filtros label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
  font-weight: 600;
}

.barra-filtros input,
.barra-filtros select {
  padding: 0.4rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #fff;
}

.filtros-botones {
  display: flex;
  gap: 0.5rem;
}

.tabla-contenedor {
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.tabla-pedidos {
  width: 100%;
  border-collapse: collapse;
}

.tabla-pedidos th,
.tabla-pedidos td {
  padding: 0.65rem 0.8rem;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
}

.alerta {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-weight: 600;
}

.alerta-exito {
  background: #dcfce7;
  color: #166534;
}

.alerta-advertencia {
  background: #fef3c7;
  color: #92400e;
}

.alerta-error {
  background: #fee2e2;
  color: #991b1b;
}

.estado-carga,
.estado-vacio {
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  padding: 2rem;
  text-align: center;
  color: #475569;
}

.modal-confirmacion-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 60;
}

.modal-confirmacion-box {
  background: #ffffff;
  border-radius: 12px;
  padding: 1.35rem;
  max-width: 480px;
  width: 100%;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.25);
}

.modal-confirmacion-box h3 {
  margin: 0 0 0.65rem;
}

.detalle-confirmacion-lista p {
  margin: 0 0 0.45rem;
}

.sub-resumen {
  font-size: 0.85rem;
  color: #475569;
}

.lista-resumen-sol {
  list-style: none;
  margin: 0.5rem 0 0;
  padding: 0;
  max-height: 220px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.84rem;
}

.lista-resumen-sol li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  border-radius: 7px;
  border: 1px solid #e2e8f0;
}

.lista-resumen-sol li.item-aut {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #14532d;
}

.lista-resumen-sol li.item-no-aut {
  background: #f8fafc;
  color: #64748b;
}

.badge-mini {
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
}

.confirmacion-acciones {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
}

button {
  min-height: 36px;
  padding: 0.4rem 0.85rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
}

.btn-primario,
.btn-detalle,
.btn-ejecutar {
  background: #0f766e;
  border-color: #0f766e;
  color: #ffffff;
}
</style>