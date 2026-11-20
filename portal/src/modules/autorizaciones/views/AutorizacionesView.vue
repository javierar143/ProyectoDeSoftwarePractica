<template>
  <main class="autorizaciones-view">
    <header class="encabezado-modulo">
      <div>
        <h1>Autorización de Pedidos</h1>
        <p>Revisión, autorización nominada y rechazo de pedidos por sector.</p>
      </div>
      <div class="acciones-encabezado">
        <RouterLink
          to="/servicio-alimentacion/cupos"
          class="btn-cupos"
          aria-label="Administrar cupos por sector y comida"
        >
          <svg
            class="icono-btn"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            aria-hidden="true"
          >
            <path stroke-linecap="round" d="M4 6h12M4 10h12M4 14h8" />
            <circle cx="15" cy="14" r="2.2" />
          </svg>
          <span>Cupos</span>
        </RouterLink>

        <div class="selector-modo-vista" role="group" aria-label="Modo de vista del período">
          <button
            type="button"
            :class="['btn-modo', modoVista === 'diaria' ? 'activo' : '']"
            :disabled="cargando"
            @click="cambiarModoVista('diaria')"
          >
            Vista Diaria
          </button>
          <button
            type="button"
            :class="['btn-modo', modoVista === 'semanal' ? 'activo' : '']"
            :disabled="cargando"
            @click="cambiarModoVista('semanal')"
          >
            Vista Semanal
          </button>
        </div>
      </div>
    </header>

    <div
      v-if="mensajeFeedback.texto"
      :class="['alerta', `alerta-${mensajeFeedback.tipo}`]"
      role="alert"
    >
      <div class="alerta-contenido">
        <span>{{ mensajeFeedback.texto }}</span>
        <button
          v-if="mensajeFeedback.puedeReintentar"
          type="button"
          class="btn-reintentar"
          :disabled="cargando || guardando || exportandoCsv"
          @click="reintentarOperacion"
        >
          Reintentar
        </button>
      </div>
    </div>

    <NavegacionPeriodoAutorizaciones
      :hoy-iso="hoyIso"
      :fecha-desde="filtros.fecha_desde"
      :fecha-hasta="filtros.fecha_hasta"
      :dias-con-pedidos="diasConPedidosVisibles"
      :cargando="cargando"
      @navegar="navegarPeriodo"
      @ir-hoy="irAHoy"
      @seleccionar-dia="seleccionarDiaCalendario"
    />

    <BarraFiltrosAutorizaciones
      v-model:filtros="filtros"
      :sectores-disponibles="sectoresDisponibles"
      :mostrar-resumen="mostrarResumen"
      :cargando="cargando"
      :exportando-csv="exportandoCsv"
      @buscar="cargarTodo"
      @limpiar="limpiarFiltros"
      @toggle-resumen="mostrarResumen = !mostrarResumen"
      @exportar-csv="descargarCsv"
    />

    <PanelResumenTotalesAutorizaciones
      v-if="mostrarResumen && resumenPeriodo"
      :resumen="resumenPeriodo"
    />

    <div v-if="cargando" class="estado-carga" role="status">
      Cargando pedidos y fechas de autorización...
    </div>

    <div v-else-if="pedidos.length === 0" class="estado-vacio">
      No se encontraron pedidos para los filtros seleccionados.
    </div>

    <div v-else class="tabla-contenedor">
      <table class="tabla-pedidos">
        <thead>
          <tr>
            <th scope="col">ID Pedido</th>
            <th scope="col">Fecha</th>
            <th scope="col">Sector</th>
            <th scope="col">Pedidas</th>
            <th scope="col">Autorizadas</th>
            <th scope="col">Estado</th>
            <th scope="col">Acción</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="pedido in pedidos"
            :key="pedido.idPedido ?? pedido.id"
            :class="{ 'fila-pendiente': esPendienteAutorizacion(pedido) }"
          >
            <td class="dato-mono">#{{ pedido.idPedido ?? pedido.id }}</td>
            <td>{{ formatearFechaDdMmAaaa(pedido.fecha_desde || pedido.fecha) }}</td>
            <td>{{ resolverNombreSector(pedido) }}</td>
            <td class="dato-mono">{{ pedido.cantidad_pedida ?? '-' }}</td>
            <td class="dato-mono">{{ pedido.cantidad_autorizada ?? 0 }}</td>
            <td>
              <span :class="['badge-estado', `estado-${String(pedido.estado || '').toLowerCase()}`]">
                {{ esPendienteAutorizacion(pedido) ? 'Pendiente de autorizar' : (pedido.estado || '-') }}
              </span>
            </td>
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
      :sectores="sectoresDisponibles"
      @cerrar="pedidoSeleccionado = null"
      @confirmar-autorizacion="prepararConfirmacion('autorizar', $event)"
      @confirmar-rechazo="prepararConfirmacion('rechazar', $event)"
    />

    <ModalConfirmarAutorizacion
      v-if="confirmacionPendiente"
      :confirmacion="confirmacionPendiente"
      :guardando="guardando"
      @cancelar="confirmacionPendiente = null"
      @confirmar="ejecutarOperacionConfirmada"
    />
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import BarraFiltrosAutorizaciones from '../components/BarraFiltrosAutorizaciones.vue'
import DetallePedido from '../components/DetallePedido.vue'
import ModalConfirmarAutorizacion from '../components/ModalConfirmarAutorizacion.vue'
import NavegacionPeriodoAutorizaciones from '../components/NavegacionPeriodoAutorizaciones.vue'
import PanelResumenTotalesAutorizaciones from '../components/PanelResumenTotalesAutorizaciones.vue'
import { normalizeApiError } from '@/services/api/error-handler'
import {
  exportarPersonasAutorizadasCsv,
  exportarTotalesAutorizacionesCsv,
  guardarAutorizacionPedido,
  listarFechasAutorizacion,
  listarPedidosAutorizacion,
  listarSectoresApi,
  obtenerDetalleAutorizacion,
  obtenerResumenAutorizaciones,
  rechazarPedidoCompleto,
} from '../services/autorizaciones'

function obtenerFechaLocalIso(offsetDias = 0, baseIso = null) {
  let fecha
  if (baseIso) {
    const [a, m, d] = String(baseIso).slice(0, 10).split('-').map(Number)
    fecha = new Date(a, (m || 1) - 1, d || 1)
  } else {
    fecha = new Date()
  }
  fecha.setDate(fecha.getDate() + offsetDias)
  return `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, '0')}-${String(fecha.getDate()).padStart(2, '0')}`
}

function formatearFechaDdMmAaaa(valorFecha) {
  if (!valorFecha) return '-'
  const partes = String(valorFecha).slice(0, 10).split('-')
  return partes.length === 3 ? `${partes[2]}/${partes[1]}/${partes[0]}` : String(valorFecha)
}

function inicioSemanaIso(isoDate) {
  const [a, m, d] = String(isoDate).slice(0, 10).split('-').map(Number)
  const fecha = new Date(a, (m || 1) - 1, d || 1)
  const diaSemana = fecha.getDay()
  fecha.setDate(fecha.getDate() + (diaSemana === 0 ? -6 : 1 - diaSemana))
  return `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, '0')}-${String(fecha.getDate()).padStart(2, '0')}`
}

const hoyIso = obtenerFechaLocalIso(0)
const modoVista = ref('diaria')

const filtros = ref({
  fecha_desde: hoyIso,
  fecha_hasta: hoyIso,
  sector: '',
  tipo_comida: '',
  tipo_menu: '',
  condicion: '',
  estado: '',
})

const pedidos = ref([])
const sectoresCatalogo = ref([])
const sectoresDetectados = ref({})
const fechasConPedidos = ref([])
const resumenPeriodo = ref(null)
const mostrarResumen = ref(false)
const pedidoSeleccionado = ref(null)
const confirmacionPendiente = ref(null)
const cargando = ref(false)
const guardando = ref(false)
const exportandoCsv = ref(false)
const mensajeFeedback = ref({ tipo: '', texto: '', puedeReintentar: false })
const operacionReintento = ref(null)

const sectoresDisponibles = computed(() => {
  if (sectoresCatalogo.value.length > 0) return sectoresCatalogo.value
  return Object.entries(sectoresDetectados.value)
    .map(([id, nombre]) => ({ id: Number(id), nombre, estado: 'activo' }))
    .sort((a, b) => a.nombre.localeCompare(b.nombre))
})

const mapaSectores = computed(() => {
  const map = { ...sectoresDetectados.value }
  for (const sec of sectoresCatalogo.value) {
    const id = sec?.id ?? sec?.idSector
    if (id !== undefined && id !== null && sec?.nombre) {
      map[Number(id)] = sec.nombre
    }
  }
  return map
})

const diasConPedidosVisibles = computed(() => {
  const desde = filtros.value.fecha_desde || hoyIso
  const hasta = filtros.value.fecha_hasta || desde
  const combinadas = new Set(fechasConPedidos.value)
  for (const p of pedidos.value) {
    const f = String(p?.fecha_desde || p?.fecha || '').slice(0, 10)
    if (f) combinadas.add(f)
  }
  return Array.from(combinadas)
    .filter((dia) => dia >= desde && dia <= hasta)
    .sort()
})

function registrarSectoresDesdeDatos(listaPedidos = [], desgloseResumen = []) {
  const nuevoMapa = { ...sectoresDetectados.value }
  for (const p of listaPedidos) {
    if (p?.idSector && p?.nombreSector && !String(p.nombreSector).startsWith('Sector #')) {
      nuevoMapa[Number(p.idSector)] = p.nombreSector
    }
  }
  for (const d of desgloseResumen) {
    if (d?.idSector && d?.sector) nuevoMapa[Number(d.idSector)] = d.sector
  }
  sectoresDetectados.value = nuevoMapa
}

function esPendienteAutorizacion(pedido) {
  return String(pedido?.estado || '').toLowerCase() === 'confirmado'
}

function resolverNombreSector(pedido) {
  const nombreDirecto =
    pedido?.nombreSector || pedido?.sectorNombre || pedido?.sector_nombre || pedido?.nombre_sector
  if (typeof nombreDirecto === 'string' && nombreDirecto.trim()) return nombreDirecto.trim()
  if (typeof pedido?.sector === 'string' && pedido.sector.trim()) return pedido.sector.trim()
  const idSector = Number(pedido?.idSector ?? pedido?.sector_id ?? pedido?.sector)
  if (Number.isInteger(idSector) && mapaSectores.value[idSector]) return mapaSectores.value[idSector]
  return idSector ? `Sector #${idSector}` : '-'
}

function limpiarParametrosVacios(obj) {
  return Object.fromEntries(
    Object.entries(obj).filter(([, val]) => val !== '' && val !== null && val !== undefined)
  )
}

function manejarErrorHttp(err, mensajeGenerico, reintentar = null) {
  operacionReintento.value = reintentar
  const status = err?.status || err?.response?.status
  const normalized = normalizeApiError(err)
  const msg = status === 503
    ? (err?.response?.data?.error || err?.message)
    : (!err?.response || status >= 500)
      ? normalized.message
      : (err?.response?.data?.error || err?.message)
  if (status === 503) {
    mensajeFeedback.value = {
      tipo: 'advertencia',
      texto: msg || 'El sistema se encuentra en mantenimiento. Intentá más tarde.',
      puedeReintentar: true,
    }
    return
  }
  if (status === 401 || status === 403 || status === 404 || status === 400) {
    mensajeFeedback.value = {
      tipo: status === 401 ? 'advertencia' : 'error',
      texto: msg || mensajeGenerico || 'No se pudo completar la operación.',
      puedeReintentar: false,
    }
    return
  }
  if (err?.isConflict || status === 409) {
    mensajeFeedback.value = {
      tipo: 'advertencia',
      texto: msg || 'Conflicto de estado detectado. Se recargaron los datos.',
      puedeReintentar: false,
    }
    return
  }
  mensajeFeedback.value = {
    tipo: 'error',
    texto: mensajeGenerico || msg || 'Ocurrió un error inesperado. Intentá nuevamente.',
    puedeReintentar: true,
  }
}

async function cargarSectores() {
  try {
    const data = await listarSectoresApi('todos')
    sectoresCatalogo.value = Array.isArray(data)
      ? data
      : Array.isArray(data?.items)
        ? data.items
        : Array.isArray(data?.sectores)
          ? data.sectores
          : []
  } catch {
    sectoresCatalogo.value = []
  }
}

async function cargarFechasCalendario() {
  try {
    const res = await listarFechasAutorizacion(
      limpiarParametrosVacios({
        fecha_desde: filtros.value.fecha_desde,
        fecha_hasta: filtros.value.fecha_hasta,
        sector: filtros.value.sector,
        tipo_comida: filtros.value.tipo_comida,
        tipo_menu: filtros.value.tipo_menu,
        estado: filtros.value.estado,
      })
    )
    const lista = Array.isArray(res) ? res : Array.isArray(res?.fechas) ? res.fechas : []
    fechasConPedidos.value = lista.map((f) => String(f).slice(0, 10))
  } catch {
    fechasConPedidos.value = []
  }
}

async function cargarResumenPeriodo() {
  try {
    const res = await obtenerResumenAutorizaciones(limpiarParametrosVacios(filtros.value))
    resumenPeriodo.value = res
    registrarSectoresDesdeDatos(pedidos.value, res?.desglose || [])
  } catch {
    resumenPeriodo.value = null
  }
}

async function cargarPedidos() {
  cargando.value = true
  mensajeFeedback.value = { tipo: '', texto: '', puedeReintentar: false }
  try {
    const data = await listarPedidosAutorizacion(limpiarParametrosVacios(filtros.value))
    pedidos.value = Array.isArray(data) ? data : Array.isArray(data?.items) ? data.items : []
    registrarSectoresDesdeDatos(pedidos.value, resumenPeriodo.value?.desglose || [])
  } catch (err) {
    const params = limpiarParametrosVacios({ ...filtros.value })
    const retry = err?.response?.status === 503 ? () => cargarTodo() : () => cargarPedidosConParametros(params)
    manejarErrorHttp(err, 'No se pudieron cargar los pedidos. Intentá nuevamente.', retry)
  } finally {
    cargando.value = false
  }
}

async function cargarPedidosConParametros(params) {
  cargando.value = true
  try {
    const data = await listarPedidosAutorizacion(params)
    pedidos.value = Array.isArray(data) ? data : Array.isArray(data?.items) ? data.items : []
    registrarSectoresDesdeDatos(pedidos.value, resumenPeriodo.value?.desglose || [])
    mensajeFeedback.value = { tipo: '', texto: '', puedeReintentar: false }
    operacionReintento.value = null
  } catch (err) {
    const retry = err?.response?.status === 503 ? () => cargarTodo() : () => cargarPedidosConParametros(params)
    manejarErrorHttp(err, 'No se pudieron cargar los pedidos. Intentá nuevamente.', retry)
  } finally { cargando.value = false }
}

async function reintentarOperacion() {
  const retry = operacionReintento.value
  if (typeof retry === 'function') await retry()
}

async function cargarTodo() {
  await Promise.all([cargarPedidos(), cargarFechasCalendario(), cargarResumenPeriodo()])
}

async function descargarCsv(tipo) {
  if (!filtros.value.fecha_desde || !filtros.value.fecha_hasta) {
    mensajeFeedback.value = {
      tipo: 'error',
      texto: 'Indicá el rango de fechas (Desde y Hasta) para exportar a CSV.',
      puedeReintentar: false,
    }
    return
  }

  exportandoCsv.value = true
  mensajeFeedback.value = { tipo: '', texto: '', puedeReintentar: false }
  try {
    const params = limpiarParametrosVacios(filtros.value)
    if (tipo === 'personas') await exportarPersonasAutorizadasCsv(params)
    else await exportarTotalesAutorizacionesCsv(params)
  } catch (err) {
    const params = limpiarParametrosVacios({ ...filtros.value })
    const retry = err?.response?.status === 503 ? () => cargarTodo() : () => descargarCsvConParametros(tipo, params)
    manejarErrorHttp(err, 'No se pudo exportar el archivo CSV.', retry)
  } finally {
    exportandoCsv.value = false
  }
}

async function descargarCsvConParametros(tipo, params) {
  exportandoCsv.value = true
  try {
    if (tipo === 'personas') await exportarPersonasAutorizadasCsv(params)
    else await exportarTotalesAutorizacionesCsv(params)
    mensajeFeedback.value = { tipo: '', texto: '', puedeReintentar: false }
    operacionReintento.value = null
  } catch (err) {
    const retry = err?.response?.status === 503 ? () => cargarTodo() : () => descargarCsvConParametros(tipo, params)
    manejarErrorHttp(err, 'No se pudo exportar el archivo CSV.', retry)
  } finally { exportandoCsv.value = false }
}

function cambiarModoVista(nuevoModo) {
  modoVista.value = nuevoModo
  const base = filtros.value.fecha_desde || hoyIso
  if (nuevoModo === 'diaria') {
    filtros.value = { ...filtros.value, fecha_desde: base, fecha_hasta: base }
  } else {
    const lunes = inicioSemanaIso(base)
    filtros.value = {
      ...filtros.value,
      fecha_desde: lunes,
      fecha_hasta: obtenerFechaLocalIso(6, lunes),
    }
  }
  cargarTodo()
}

function navegarPeriodo(direccion) {
  const paso = modoVista.value === 'semanal' ? 7 * direccion : 1 * direccion
  const nuevaBase = obtenerFechaLocalIso(paso, filtros.value.fecha_desde || hoyIso)
  if (modoVista.value === 'semanal') {
    const lunes = inicioSemanaIso(nuevaBase)
    filtros.value = {
      ...filtros.value,
      fecha_desde: lunes,
      fecha_hasta: obtenerFechaLocalIso(6, lunes),
    }
  } else {
    filtros.value = { ...filtros.value, fecha_desde: nuevaBase, fecha_hasta: nuevaBase }
  }
  cargarTodo()
}

function irAHoy() {
  if (modoVista.value === 'semanal') {
    const lunes = inicioSemanaIso(hoyIso)
    filtros.value = {
      ...filtros.value,
      fecha_desde: lunes,
      fecha_hasta: obtenerFechaLocalIso(6, lunes),
    }
  } else {
    filtros.value = { ...filtros.value, fecha_desde: hoyIso, fecha_hasta: hoyIso }
  }
  cargarTodo()
}

function seleccionarDiaCalendario(diaIso) {
  filtros.value = {
    ...filtros.value,
    fecha_desde: diaIso,
    fecha_hasta: modoVista.value === 'diaria' ? diaIso : filtros.value.fecha_hasta,
  }
  cargarTodo()
}

function limpiarFiltros() {
  modoVista.value = 'diaria'
  filtros.value = {
    fecha_desde: hoyIso,
    fecha_hasta: hoyIso,
    sector: '',
    tipo_comida: '',
    tipo_menu: '',
    condicion: '',
    estado: '',
  }
  cargarTodo()
}

async function abrirDetallePedido(idPedido) {
  mensajeFeedback.value = { tipo: '', texto: '', puedeReintentar: false }
  try {
    pedidoSeleccionado.value = await obtenerDetalleAutorizacion(idPedido)
  } catch (err) {
    const retry = err?.response?.status === 503 ? () => cargarTodo() : () => abrirDetallePedido(idPedido)
    manejarErrorHttp(err, 'No se pudo obtener el detalle del pedido.', retry)
  }
}

function prepararConfirmacion(tipo, payload) {
  confirmacionPendiente.value = { tipo, payload }
}

async function ejecutarOperacionConfirmada() {
  if (!confirmacionPendiente.value || guardando.value) return
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
        puedeReintentar: false,
      }
    } else if (tipo === 'rechazar') {
      await rechazarPedidoCompleto(payload.idPedido, { motivo: payload.motivo })
      mensajeFeedback.value = {
        tipo: 'exito',
        texto: `Pedido #${payload.idPedido} rechazado correctamente.`,
        puedeReintentar: false,
      }
    }

    confirmacionPendiente.value = null
    pedidoSeleccionado.value = null
    await cargarTodo()
  } catch (err) {
    const status = err?.response?.status ?? err?.status
    const puedeReintentar = !err?.response || status === 500
    if (!puedeReintentar) confirmacionPendiente.value = null
    const retry = status === 503 ? () => cargarTodo() : (puedeReintentar ? () => ejecutarOperacionConfirmada() : null)
    manejarErrorHttp(
      err,
      'Ocurrió un error al guardar la operación. Intentá nuevamente.',
      retry,
    )
    if (err?.isConflict || err?.status === 409 || err?.response?.status === 409) {
      await cargarTodo()
      if (pedidoSeleccionado.value?.idPedido === payload.idPedido) {
        pedidoSeleccionado.value = await obtenerDetalleAutorizacion(payload.idPedido)
      }
    }
  } finally {
    guardando.value = false
  }
}

onMounted(async () => {
  await Promise.all([cargarSectores(), cargarTodo()])
})
</script>

<style scoped>
.autorizaciones-view {
  padding: 1.25rem 1.5rem;
  max-width: 1320px;
  margin: 0 auto;
  color: #0f172a;
}

.encabezado-modulo {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.encabezado-modulo h1 {
  margin: 0;
  font-size: 1.65rem;
  font-weight: 700;
  letter-spacing: -0.015em;
}

.encabezado-modulo p {
  margin: 0.2rem 0 0;
  font-size: 0.92rem;
  color: #475569;
}

.acciones-encabezado {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem;
}

.btn-cupos {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 40px;
  padding: 0.4rem 0.95rem;
  border: 1px solid #0f766e;
  border-radius: 10px;
  background: #f0fdfa;
  color: #0f766e;
  font-size: 0.86rem;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  transition: background-color 0.15s, color 0.15s;
}

.btn-cupos:hover {
  background: #0f766e;
  color: #ffffff;
}

.icono-btn {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.selector-modo-vista {
  display: inline-flex;
  gap: 0.25rem;
  background: #f1f5f9;
  padding: 0.25rem;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
}

.btn-modo {
  border: 1px solid transparent;
  background: transparent;
  color: #334155;
  border-radius: 8px;
  min-height: 36px;
  padding: 0.35rem 0.85rem;
  font-size: 0.86rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-modo.activo {
  background: #0f766e;
  color: #ffffff;
}

.tabla-contenedor {
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
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
  vertical-align: middle;
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
  letter-spacing: 0.04em;
}

.fila-pendiente {
  background: #fffbeb;
}

.dato-mono {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.badge-estado {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
}

.badge-estado.estado-confirmado { background: #fef3c7; color: #92400e; border-color: #f59e0b; }
.badge-estado.estado-autorizado { background: #dcfce7; color: #166534; border-color: #86efac; }
.badge-estado.estado-rechazado { background: #fee2e2; color: #991b1b; border-color: #fca5a5; }

.alerta {
  padding: 0.75rem 1rem;
  border-radius: 10px;
  margin-bottom: 1rem;
  font-weight: 600;
  font-size: 0.88rem;
}

.alerta-contenido {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.alerta-exito { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
.alerta-advertencia { background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
.alerta-error { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }

.estado-carga,
.estado-vacio {
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  color: #475569;
}

button {
  min-height: 36px;
  padding: 0.38rem 0.8rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #0f172a;
}

.btn-detalle {
  background: #0f766e;
  border-color: #0f766e;
  color: #ffffff;
}

.btn-detalle:hover:not(:disabled) {
  background: #115e59;
}
</style>
