<script setup>
import { computed, onMounted, ref } from 'vue'

import { useAuthStore } from '@/stores/auth'
import { normalizeApiError } from '@/services/api/error-handler'
import ApiErrorMessage from '@/modules/shared/components/ApiErrorMessage.vue'
import {
  listarPedidosSector,
  obtenerPedido,
  actualizarPedido,
  eliminarPedido,
  obtenerConfiguracionPedidos,
  obtenerDatosCargaPedido,
} from '../services/pedidos'

const authStore = useAuthStore()

const COMIDAS_BASE = [
  { idTipoComida: 1, label: 'Desayuno', inicial: 'D' },
  { idTipoComida: 2, label: 'Almuerzo', inicial: 'A' },
  { idTipoComida: 3, label: 'Merienda', inicial: 'M' },
  { idTipoComida: 4, label: 'Cena', inicial: 'C' },
]

const MENUS_BASE = [
  { idTipoMenu: 1, label: 'General' },
  { idTipoMenu: 2, label: 'Vegetariano' },
  { idTipoMenu: 3, label: 'Celíaco' },
]

const ESTADOS_FILTRO = [
  { value: '', label: 'Todos los estados' },
  { value: 'confirmado', label: 'Confirmado (pendiente)' },
  { value: 'autorizado', label: 'Autorizado' },
  { value: 'rechazado', label: 'Rechazado' },
]

function formatearFecha(isoStr) {
  if (!isoStr) return '—'
  const partes = String(isoStr).slice(0, 10).split('-')
  if (partes.length !== 3) return isoStr
  return `${partes[2]}/${partes[1]}/${partes[0]}`
}

function hoyLocalIso() {
  const ahora = new Date()
  const anio = ahora.getFullYear()
  const mes = String(ahora.getMonth() + 1).padStart(2, '0')
  const dia = String(ahora.getDate()).padStart(2, '0')
  return `${anio}-${mes}-${dia}`
}

const comidas = ref([...COMIDAS_BASE])
const menus = ref([...MENUS_BASE])
const horarioCorte = ref('18:00 del día anterior')

// Filtros y paginación
const filtroFechaDesde = ref('')
const filtroFechaHasta = ref('')
const filtroEstado = ref('')
const filtroComida = ref('')
const filtroMenu = ref('')
const page = ref(1)
const perPage = ref(10)
const totalItems = ref(0)

// Listado y estados UI
const pedidosLista = ref([])
const loadingLista = ref(false)
const accionEnCurso = ref(false)
const apiErrorMessage = ref(null)
const retryOperation = ref(null)
const mensajeExito = ref('')

// Catálogos de personas y cupos para detalle/edición
const catalogoPersonas = ref(new Map())
const personalSectorDisponibles = ref([])
const residentesDisponibles = ref([])
const cuposPorComida = ref({ 1: 0, 2: 0, 3: 0, 4: 0 })

// Panel de detalle / edición
const pedidoSeleccionado = ref(null)
const modoEdicion = ref(false)
const filasEdicion = ref([])
const personaSectorSeleccionadaId = ref('')
const busquedaResidente = ref('')
const errorEdicion = ref('')
const pedidoAEliminarId = ref(null)

const nombreSector = computed(() => {
  const usuario = authStore.user ?? {}
  return (
    usuario.sector?.nombre ||
    usuario.nombre_sector ||
    (usuario.idSector || usuario.id_sector
      ? `Sector #${usuario.idSector ?? usuario.id_sector}`
      : 'Sector asignado')
  )
})

const totalPaginas = computed(() => {
  if (!perPage.value) return 1
  return Math.max(1, Math.ceil(totalItems.value / perPage.value))
})

function obtenerSectorIdUsuario() {
  const usuario = authStore.user ?? {}
  return (
    usuario.idSector ??
    usuario.id_sector ??
    usuario.sector?.idSector ??
    usuario.sector?.id ??
    null
  )
}

function labelComida(idComida) {
  const item = comidas.value.find((c) => c.idTipoComida === Number(idComida))
  return item ? item.label : `Comida #${idComida}`
}

function labelMenu(idMenu) {
  const item = menus.value.find((m) => m.idTipoMenu === Number(idMenu))
  return item ? item.label : `Menú #${idMenu}`
}

function calcularTotalesPorComida(cantidadesMap = {}) {
  const totales = { 1: 0, 2: 0, 3: 0, 4: 0 }
  for (const [clave, valor] of Object.entries(cantidadesMap || {})) {
    const match = clave.match(/^comida_(\d+)_menu_(\d+)$/)
    if (match) {
      const idC = Number(match[1])
      totales[idC] = (totales[idC] ?? 0) + Number(valor || 0)
    }
  }
  return totales
}

function calcularTotalesPorMenu(cantidadesMap = {}) {
  const totales = {}
  for (const [clave, valor] of Object.entries(cantidadesMap || {})) {
    const match = clave.match(/^comida_(\d+)_menu_(\d+)$/)
    if (match) {
      const idM = Number(match[2])
      totales[idM] = (totales[idM] ?? 0) + Number(valor || 0)
    }
  }
  return totales
}

function totalGeneralMap(cantidadesMap = {}) {
  return Object.values(cantidadesMap || {}).reduce(
    (acc, val) => acc + Number(val || 0),
    0,
  )
}

function puedeModificarOEliminar(pedido) {
  if (!pedido) return false
  if (String(pedido.estado).toLowerCase() !== 'confirmado') return false
  if (pedido.fecha_desde && pedido.fecha_desde < hoyLocalIso()) return false
  return true
}

function mapearPersonaBase(persona, esResidente = false) {
  const apellido = persona.apellido ?? ''
  const nombre = persona.nombre ?? ''
  const nombreCompleto =
    apellido && nombre
      ? `${apellido}, ${nombre}`
      : persona.nombreCompleto ||
        nombre ||
        `Persona #${persona.idPersonal ?? persona.id}`

  return {
    idPersonal: Number(persona.idPersonal ?? persona.id),
    nombre: nombreCompleto,
    dni: persona.dni ?? '',
    tipoMenu:
      persona.tipoMenu?.nombre ??
      persona.tipo_menu?.nombre ??
      persona.tipoMenu ??
      'General',
    esResidente,
  }
}

async function cargarCatalogosSector() {
  try {
    const configData = await obtenerConfiguracionPedidos().catch(() => null)
    if (configData?.horario_corte) {
      horarioCorte.value = `${configData.horario_corte} del día anterior`
    }

    const sectorId = obtenerSectorIdUsuario()
    const { personalSector, cuposSector, residentes } =
      await obtenerDatosCargaPedido(sectorId)

    const mapa = new Map()
    const listaSector = personalSector.map((p) => {
      const item = mapearPersonaBase(p, false)
      mapa.set(item.idPersonal, item)
      return item
    })

    const listaResidentes = residentes.map((r) => {
      const item = mapearPersonaBase(r, true)
      if (!mapa.has(item.idPersonal)) {
        mapa.set(item.idPersonal, item)
      }
      return item
    })

    catalogoPersonas.value = mapa
    personalSectorDisponibles.value = listaSector
    residentesDisponibles.value = listaResidentes

    const mapaCupos = { ...cuposPorComida.value }
    for (const c of cuposSector) {
      const idC = Number(c.idTipoComida ?? c.id_tipo_comida)
      if (idC) {
        mapaCupos[idC] = Number(c.cantComensales ?? c.cantidad ?? 0)
      }
    }
    cuposPorComida.value = mapaCupos
  } catch {
    // Si falla la carga auxiliar, el listado principal sigue operando
  }
}

async function cargarPedidos(paginaDestino = 1) {
  loadingLista.value = true
  apiErrorMessage.value = null
  retryOperation.value = null
  page.value = paginaDestino

  const params = { page: paginaDestino }
  if (filtroFechaDesde.value) params.fecha_desde = filtroFechaDesde.value
  if (filtroFechaHasta.value) params.fecha_hasta = filtroFechaHasta.value
  if (filtroEstado.value) params.estado = filtroEstado.value
  if (filtroComida.value) params.id_tipo_comida = Number(filtroComida.value)
  if (filtroMenu.value) params.id_tipo_menu = Number(filtroMenu.value)

  try {
    const data = await listarPedidosSector(params)
    pedidosLista.value = Array.isArray(data.items) ? data.items : []
    totalItems.value = Number(data.total ?? pedidosLista.value.length)
    perPage.value = Number(data.per_page ?? perPage.value)
  } catch (error) {
    const normalizado = normalizeApiError(error)
    apiErrorMessage.value = normalizado
    if (normalizado.canRetry) {
      retryOperation.value = () => cargarPedidos(paginaDestino)
    }
  } finally {
    loadingLista.value = false
  }
}

onMounted(async () => {
  await Promise.all([cargarCatalogosSector(), cargarPedidos(1)])
})

function aplicarFiltros() {
  mensajeExito.value = ''
  cerrarDetalle()
  cargarPedidos(1)
}

function limpiarFiltros() {
  filtroFechaDesde.value = ''
  filtroFechaHasta.value = ''
  filtroEstado.value = ''
  filtroComida.value = ''
  filtroMenu.value = ''
  mensajeExito.value = ''
  cerrarDetalle()
  cargarPedidos(1)
}

let seqUid = 1
function construirFilasDesdeSolicitudes(solicitudes = []) {
  const porPersona = new Map()

  for (const sol of solicitudes) {
    const idP = Number(sol.idPersonal)
    if (!porPersona.has(idP)) {
      const info = catalogoPersonas.value.get(idP)
      porPersona.set(idP, {
        uid: seqUid++,
        idPersonal: idP,
        nombre: info?.nombre ?? `Persona #${idP}`,
        dni: info?.dni ?? '—',
        tipoMenu: info?.tipoMenu ?? labelMenu(sol.idTipoMenu),
        esResidente: info?.esResidente ?? false,
        comidas: { 1: false, 2: false, 3: false, 4: false },
      })
    }
    const fila = porPersona.get(idP)
    fila.comidas[Number(sol.idTipoComida)] = true
  }

  return Array.from(porPersona.values())
}

async function abrirPedido(pedido, editar = false) {
  if (accionEnCurso.value) return
  accionEnCurso.value = true
  apiErrorMessage.value = null
  errorEdicion.value = ''
  pedidoAEliminarId.value = null

  try {
    const detalle = await obtenerPedido(pedido.idPedido)
    pedidoSeleccionado.value = detalle
    filasEdicion.value = construirFilasDesdeSolicitudes(detalle.solicitudes ?? [])
    modoEdicion.value = editar && puedeModificarOEliminar(detalle)
  } catch (error) {
    apiErrorMessage.value = normalizeApiError(error)
  } finally {
    accionEnCurso.value = false
  }
}

function cerrarDetalle() {
  pedidoSeleccionado.value = null
  modoEdicion.value = false
  filasEdicion.value = []
  errorEdicion.value = ''
  personaSectorSeleccionadaId.value = ''
  busquedaResidente.value = ''
}

function incorporarPersonaEdicion(personaBase) {
  const yaExiste = filasEdicion.value.some(
    (f) => f.idPersonal === personaBase.idPersonal,
  )
  if (yaExiste) {
    errorEdicion.value = `${personaBase.nombre} ya figura en este pedido.`
    return false
  }

  errorEdicion.value = ''
  filasEdicion.value.push({
    uid: seqUid++,
    idPersonal: personaBase.idPersonal,
    nombre: personaBase.nombre,
    dni: personaBase.dni,
    tipoMenu: personaBase.tipoMenu,
    esResidente: personaBase.esResidente,
    comidas: { 1: false, 2: false, 3: false, 4: false },
  })
  return true
}

function agregarPersonaSectorEdicion() {
  const idBuscado = Number(personaSectorSeleccionadaId.value)
  if (!idBuscado) return
  const encontrada = personalSectorDisponibles.value.find(
    (p) => p.idPersonal === idBuscado,
  )
  if (encontrada && incorporarPersonaEdicion(encontrada)) {
    personaSectorSeleccionadaId.value = ''
  }
}

function agregarResidenteEdicion() {
  const consulta = busquedaResidente.value.trim().toLowerCase()
  if (!consulta) return
  const encontrado = residentesDisponibles.value.find(
    (r) =>
      r.nombre.toLowerCase().includes(consulta) ||
      String(r.dni).toLowerCase().includes(consulta),
  )
  if (!encontrado) {
    errorEdicion.value =
      'No se encontró un residente activo que coincida con la búsqueda.'
    return
  }
  if (incorporarPersonaEdicion(encontrado)) {
    busquedaResidente.value = ''
  }
}

function alternarComidaEdicion(fila, idTipoComida) {
  errorEdicion.value = ''
  fila.comidas[idTipoComida] = !fila.comidas[idTipoComida]
}

function quitarFilaEdicion(idx) {
  errorEdicion.value = ''
  filasEdicion.value.splice(idx, 1)
}

function esExcepcionEstimadaEdicion(indiceFila, idTipoComida) {
  const fila = filasEdicion.value[indiceFila]
  if (!fila || !fila.comidas[idTipoComida]) return false
  let contador = 0
  for (let i = 0; i <= indiceFila; i += 1) {
    if (filasEdicion.value[i].comidas[idTipoComida]) {
      contador += 1
    }
  }
  const limite = Number(cuposPorComida.value[idTipoComida] ?? 0)
  return contador > limite
}

async function guardarEdicionPedido() {
  if (!pedidoSeleccionado.value || accionEnCurso.value) return
  errorEdicion.value = ''
  apiErrorMessage.value = null
  mensajeExito.value = ''

  const diccionarioComidas = {}
  let totalComidas = 0
  for (const comida of comidas.value) {
    const idC = comida.idTipoComida
    const ids = []
    for (const fila of filasEdicion.value) {
      if (fila.comidas[idC] && !ids.includes(fila.idPersonal)) {
        ids.push(fila.idPersonal)
        totalComidas += 1
      }
    }
    if (ids.length > 0) {
      diccionarioComidas[idC] = ids
    }
  }

  if (totalComidas === 0) {
    errorEdicion.value =
      'Seleccioná al menos una comida para alguna persona antes de guardar.'
    return
  }

  accionEnCurso.value = true
  const idPedidoActual = pedidoSeleccionado.value.idPedido

  try {
    await actualizarPedido(idPedidoActual, { comidas: diccionarioComidas })
    mensajeExito.value = `Pedido #${idPedidoActual} actualizado correctamente.`
    modoEdicion.value = false
    await cargarPedidos(page.value)
    const detalleActualizado = await obtenerPedido(idPedidoActual)
    pedidoSeleccionado.value = detalleActualizado
    filasEdicion.value = construirFilasDesdeSolicitudes(
      detalleActualizado.solicitudes ?? [],
    )
  } catch (error) {
    const status = error?.response?.status
    const normalizado = normalizeApiError(error)
    if (status === 409) {
      apiErrorMessage.value = {
        ...normalizado,
        message:
          error?.response?.data?.error ||
          'El pedido ya fue autorizado o rechazado y no puede modificarse.',
        canRetry: false,
      }
      modoEdicion.value = false
      await cargarPedidos(page.value)
    } else {
      errorEdicion.value = normalizado.message
    }
  } finally {
    accionEnCurso.value = false
  }
}

function solicitarConfirmacionEliminar(pedido) {
  if (!puedeModificarOEliminar(pedido)) return
  pedidoAEliminarId.value = pedido.idPedido
  mensajeExito.value = ''
  apiErrorMessage.value = null
}

async function confirmarEliminarPedido(idPedido) {
  if (accionEnCurso.value) return
  accionEnCurso.value = true
  apiErrorMessage.value = null
  mensajeExito.value = ''

  try {
    await eliminarPedido(idPedido)
    pedidoAEliminarId.value = null
    if (pedidoSeleccionado.value?.idPedido === idPedido) {
      cerrarDetalle()
    }
    mensajeExito.value = `Pedido #${idPedido} eliminado correctamente.`
    const nuevaPagina =
      pedidosLista.value.length === 1 && page.value > 1
        ? page.value - 1
        : page.value
    await cargarPedidos(nuevaPagina)
  } catch (error) {
    const status = error?.response?.status
    const normalizado = normalizeApiError(error)
    pedidoAEliminarId.value = null
    if (status === 409) {
      apiErrorMessage.value = {
        ...normalizado,
        message:
          error?.response?.data?.error ||
          'El pedido ya fue autorizado o rechazado y no puede eliminarse.',
        canRetry: false,
      }
      await cargarPedidos(page.value)
    } else {
      apiErrorMessage.value = normalizado
    }
  } finally {
    accionEnCurso.value = false
  }
}
</script>

<template>
  <main class="pedidos-container" aria-labelledby="titulo-pedidos-sector">
    <header class="pedidos-header">
      <div>
        <h1 id="titulo-pedidos-sector">Pedidos del sector</h1>
        <p class="pedidos-subtitulo">
          {{ nombreSector }} · Horario de corte: {{ horarioCorte }}
        </p>
      </div>
      <div class="header-acciones">
        <RouterLink class="btn-principal" to="/jefe-servicio/pedidos/nuevo">
          Nuevo pedido
        </RouterLink>
        <RouterLink class="btn-secundario" to="/inicio/jefe-servicio">
          Volver al inicio
        </RouterLink>
      </div>
    </header>

    <p v-if="mensajeExito" class="mensaje-exito" role="status">
      {{ mensajeExito }}
    </p>

    <ApiErrorMessage :error="apiErrorMessage" @retry="retryOperation" />

    <!-- Filtros -->
    <section class="panel" aria-labelledby="titulo-filtros">
      <h2 id="titulo-filtros">Filtrar pedidos</h2>
      <form class="filtros-grid" @submit.prevent="aplicarFiltros">
        <div class="form-field">
          <label for="filtro-desde">Fecha desde</label>
          <input
            id="filtro-desde"
            v-model="filtroFechaDesde"
            type="date"
            :disabled="loadingLista"
          />
        </div>

        <div class="form-field">
          <label for="filtro-hasta">Fecha hasta</label>
          <input
            id="filtro-hasta"
            v-model="filtroFechaHasta"
            type="date"
            :disabled="loadingLista"
          />
        </div>

        <div class="form-field">
          <label for="filtro-estado">Estado</label>
          <select id="filtro-estado" v-model="filtroEstado" :disabled="loadingLista">
            <option
              v-for="est in ESTADOS_FILTRO"
              :key="est.value"
              :value="est.value"
            >
              {{ est.label }}
            </option>
          </select>
        </div>

        <div class="form-field">
          <label for="filtro-comida">Tipo de comida</label>
          <select id="filtro-comida" v-model="filtroComida" :disabled="loadingLista">
            <option value="">Todas las comidas</option>
            <option
              v-for="c in comidas"
              :key="c.idTipoComida"
              :value="c.idTipoComida"
            >
              {{ c.label }}
            </option>
          </select>
        </div>

        <div class="form-field">
          <label for="filtro-menu">Tipo de menú</label>
          <select id="filtro-menu" v-model="filtroMenu" :disabled="loadingLista">
            <option value="">Todos los menús</option>
            <option
              v-for="m in menus"
              :key="m.idTipoMenu"
              :value="m.idTipoMenu"
            >
              {{ m.label }}
            </option>
          </select>
        </div>

        <div class="filtros-botones">
          <button type="submit" class="btn-principal" :disabled="loadingLista">
            Buscar
          </button>
          <button
            type="button"
            class="btn-secundario"
            :disabled="loadingLista"
            @click="limpiarFiltros"
          >
            Limpiar
          </button>
        </div>
      </form>
    </section>

    <!-- Listado de pedidos -->
    <section class="panel" aria-labelledby="titulo-listado">
      <div class="panel-cabecera">
        <h2 id="titulo-listado">
          Listado de pedidos ({{ totalItems }})
        </h2>
      </div>

      <p v-if="loadingLista" class="estado-info" role="status">
        Cargando pedidos del sector...
      </p>

      <p v-else-if="pedidosLista.length === 0" class="estado-info" role="status">
        No se encontraron pedidos para los filtros seleccionados.
      </p>

      <div v-else class="tabla-scroll">
        <table class="tabla-pedidos">
          <thead>
            <tr>
              <th scope="col">ID</th>
              <th scope="col">Fecha</th>
              <th scope="col">Estado</th>
              <th scope="col">Pedidos por comida</th>
              <th scope="col">Pedidos por menú</th>
              <th scope="col">Autorizados</th>
              <th scope="col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="pedido in pedidosLista" :key="pedido.idPedido">
              <td><strong>#{{ pedido.idPedido }}</strong></td>
              <td>{{ formatearFecha(pedido.fecha_desde) }}</td>
              <td>
                <span :class="['badge-estado', `estado-${pedido.estado}`]">
                  {{ pedido.estado }}
                </span>
              </td>
              <td>
                <div class="resumen-celda">
                  <span
                    v-for="c in comidas"
                    :key="c.idTipoComida"
                    class="chip-dato"
                  >
                    {{ c.inicial }}:
                    {{
                      calcularTotalesPorComida(pedido.cantidades_pedidas)[
                        c.idTipoComida
                      ] ?? 0
                    }}
                  </span>
                </div>
              </td>
              <td>
                <div class="resumen-celda">
                  <span
                    v-for="(cant, idM) in calcularTotalesPorMenu(
                      pedido.cantidades_pedidas,
                    )"
                    :key="idM"
                    class="chip-dato"
                  >
                    {{ labelMenu(idM) }}: {{ cant }}
                  </span>
                </div>
              </td>
              <td>
                <template v-if="pedido.cantidades_autorizadas">
                  <strong>
                    {{ totalGeneralMap(pedido.cantidades_autorizadas) }}
                  </strong>
                  / {{ totalGeneralMap(pedido.cantidades_pedidas) }}
                </template>
                <span v-else class="texto-secundario">Pendiente</span>
              </td>
              <td>
                <div class="acciones-fila">
                  <button
                    type="button"
                    class="btn-accion"
                    :disabled="accionEnCurso"
                    @click="abrirPedido(pedido, false)"
                  >
                    Ver detalle
                  </button>

                  <button
                    v-if="puedeModificarOEliminar(pedido)"
                    type="button"
                    class="btn-accion btn-editar"
                    :disabled="accionEnCurso"
                    @click="abrirPedido(pedido, true)"
                  >
                    Editar
                  </button>

                  <button
                    v-if="puedeModificarOEliminar(pedido)"
                    type="button"
                    class="btn-accion btn-eliminar"
                    :disabled="accionEnCurso"
                    @click="solicitarConfirmacionEliminar(pedido)"
                  >
                    Eliminar
                  </button>
                </div>

                <!-- Confirmación inline de borrado -->
                <div
                  v-if="pedidoAEliminarId === pedido.idPedido"
                  class="confirmacion-eliminar"
                  role="alert"
                >
                  <span>¿Eliminar pedido #{{ pedido.idPedido }}?</span>
                  <button
                    type="button"
                    class="btn-eliminar-confirmar"
                    :disabled="accionEnCurso"
                    @click="confirmarEliminarPedido(pedido.idPedido)"
                  >
                    {{ accionEnCurso ? 'Eliminando...' : 'Sí, eliminar' }}
                  </button>
                  <button
                    type="button"
                    class="btn-cancelar-mini"
                    :disabled="accionEnCurso"
                    @click="pedidoAEliminarId = null"
                  >
                    Cancelar
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Paginación -->
      <nav
        v-if="totalPaginas > 1"
        class="paginacion"
        aria-label="Paginación de pedidos"
      >
        <button
          type="button"
          class="btn-secundario"
          :disabled="loadingLista || page <= 1"
          @click="cargarPedidos(page - 1)"
        >
          Anterior
        </button>
        <span>Página {{ page }} de {{ totalPaginas }}</span>
        <button
          type="button"
          class="btn-secundario"
          :disabled="loadingLista || page >= totalPaginas"
          @click="cargarPedidos(page + 1)"
        >
          Siguiente
        </button>
      </nav>
    </section>

    <!-- Panel de detalle o edición -->
    <section
      v-if="pedidoSeleccionado"
      class="panel"
      aria-labelledby="titulo-detalle-pedido"
    >
      <div class="panel-cabecera">
        <div>
          <h2 id="titulo-detalle-pedido">
            {{ modoEdicion ? 'Editar' : 'Detalle del' }} pedido #{{
              pedidoSeleccionado.idPedido
            }}
          </h2>
          <p class="pedidos-subtitulo">
            Fecha: {{ formatearFecha(pedidoSeleccionado.fecha_desde) }} · Estado:
            <strong>{{ pedidoSeleccionado.estado }}</strong>
          </p>
        </div>
        <div class="header-acciones">
          <button
            v-if="!modoEdicion && puedeModificarOEliminar(pedidoSeleccionado)"
            type="button"
            class="btn-principal"
            :disabled="accionEnCurso"
            @click="modoEdicion = true"
          >
            Habilitar edición
          </button>
          <button
            type="button"
            class="btn-secundario"
            :disabled="accionEnCurso"
            @click="cerrarDetalle"
          >
            Cerrar
          </button>
        </div>
      </div>

      <p
        v-if="pedidoSeleccionado.motivo_rechazo || pedidoSeleccionado.motivoRechazo"
        class="aviso-rechazo"
        role="status"
      >
        <strong>Motivo del rechazo:</strong>
        {{
          pedidoSeleccionado.motivo_rechazo || pedidoSeleccionado.motivoRechazo
        }}
      </p>

      <!-- Resumen pedido vs autorizado -->
      <div class="resumen-comparativo">
        <div class="caja-resumen">
          <h3>Cantidades pedidas</h3>
          <ul>
            <li
              v-for="(cant, clave) in pedidoSeleccionado.cantidades_pedidas"
              :key="`ped-${clave}`"
            >
              {{ clave.replace('comida_', 'Comida #').replace('_menu_', ' · Menú #') }}:
              <strong>{{ cant }}</strong>
            </li>
          </ul>
        </div>

        <div
          v-if="pedidoSeleccionado.cantidades_autorizadas"
          class="caja-resumen caja-autorizado"
        >
          <h3>Cantidades autorizadas (solo lectura)</h3>
          <ul>
            <li
              v-for="(cant, clave) in pedidoSeleccionado.cantidades_autorizadas"
              :key="`aut-${clave}`"
            >
              {{ clave.replace('comida_', 'Comida #').replace('_menu_', ' · Menú #') }}:
              <strong>{{ cant }}</strong>
            </li>
          </ul>
        </div>
      </div>

      <!-- Modo solo lectura -->
      <div v-if="!modoEdicion" class="tabla-scroll">
        <table class="tabla-pedidos">
          <thead>
            <tr>
              <th scope="col">Persona</th>
              <th scope="col">Comida</th>
              <th scope="col">Menú</th>
              <th scope="col">Condición cupo</th>
              <th scope="col">Autorización</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="sol in pedidoSeleccionado.solicitudes"
              :key="sol.idSolicitud"
            >
              <td>
                {{
                  catalogoPersonas.get(Number(sol.idPersonal))?.nombre ??
                  `Persona #${sol.idPersonal}`
                }}
              </td>
              <td>{{ labelComida(sol.idTipoComida) }}</td>
              <td>{{ labelMenu(sol.idTipoMenu) }}</td>
              <td>
                <span
                  :class="[
                    'chip-cupo',
                    sol.condicionCupo === 'excepcion' ? 'cupo-exc' : 'cupo-reg',
                  ]"
                >
                  {{ sol.condicionCupo }}
                </span>
              </td>
              <td>{{ sol.estadoAutorizacion }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Modo edición -->
      <form v-else @submit.prevent="guardarEdicionPedido" novalidate>
        <div class="controles-edicion">
          <div class="grupo-agregar">
            <select
              v-model="personaSectorSeleccionadaId"
              aria-label="Seleccionar personal fijo del sector"
              :disabled="accionEnCurso || personalSectorDisponibles.length === 0"
            >
              <option value="">Agregar personal fijo del sector...</option>
              <option
                v-for="p in personalSectorDisponibles"
                :key="p.idPersonal"
                :value="p.idPersonal"
              >
                {{ p.nombre }} (DNI {{ p.dni }})
              </option>
            </select>
            <button
              type="button"
              class="btn-secundario"
              :disabled="accionEnCurso || !personaSectorSeleccionadaId"
              @click="agregarPersonaSectorEdicion"
            >
              Agregar del sector
            </button>
          </div>

          <div class="grupo-agregar">
            <input
              v-model="busquedaResidente"
              type="search"
              placeholder="Buscar residente por nombre o DNI"
              aria-label="Buscar residente por nombre o DNI"
              :disabled="accionEnCurso"
            />
            <button
              type="button"
              class="btn-secundario"
              :disabled="accionEnCurso || !busquedaResidente.trim()"
              @click="agregarResidenteEdicion"
            >
              Agregar residente
            </button>
          </div>
        </div>

        <div class="tabla-scroll">
          <table class="tabla-pedidos">
            <thead>
              <tr>
                <th scope="col">Persona</th>
                <th scope="col">Menú</th>
                <th
                  v-for="comida in comidas"
                  :key="comida.idTipoComida"
                  scope="col"
                  class="col-centrada"
                >
                  {{ comida.label }}
                </th>
                <th scope="col">Acción</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(fila, idx) in filasEdicion" :key="fila.uid">
                <td>
                  <strong>{{ fila.nombre }}</strong>
                  <div class="texto-secundario">DNI {{ fila.dni }}</div>
                </td>
                <td>{{ fila.tipoMenu }}</td>
                <td
                  v-for="comida in comidas"
                  :key="comida.idTipoComida"
                  class="col-centrada"
                >
                  <button
                    type="button"
                    :class="[
                      'btn-comida',
                      {
                        seleccionada: Boolean(fila.comidas[comida.idTipoComida]),
                        excepcion: esExcepcionEstimadaEdicion(
                          idx,
                          comida.idTipoComida,
                        ),
                      },
                    ]"
                    :aria-pressed="Boolean(fila.comidas[comida.idTipoComida])"
                    :disabled="accionEnCurso"
                    @click="alternarComidaEdicion(fila, comida.idTipoComida)"
                  >
                    <span v-if="fila.comidas[comida.idTipoComida]">
                      {{
                        esExcepcionEstimadaEdicion(idx, comida.idTipoComida)
                          ? 'EXC'
                          : '✓'
                      }}
                    </span>
                  </button>
                </td>
                <td>
                  <button
                    type="button"
                    class="btn-accion btn-eliminar"
                    :disabled="accionEnCurso"
                    @click="quitarFilaEdicion(idx)"
                  >
                    Quitar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-if="errorEdicion" class="field-error" role="alert">
          {{ errorEdicion }}
        </p>

        <div class="acciones-footer">
          <button
            type="button"
            class="btn-secundario"
            :disabled="accionEnCurso"
            @click="modoEdicion = false"
          >
            Cancelar edición
          </button>
          <button
            type="submit"
            class="btn-principal"
            :disabled="accionEnCurso || filasEdicion.length === 0"
          >
            {{ accionEnCurso ? 'Guardando...' : 'Guardar cambios' }}
          </button>
        </div>
      </form>
    </section>
  </main>
</template>

<style scoped>
.pedidos-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px;
  color: #1f2937;
}

.pedidos-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 18px;
}

.pedidos-header h1 {
  margin: 0;
  color: #1d4ed8;
}

.pedidos-subtitulo {
  margin: 4px 0 0;
  color: #4b5563;
  font-size: 14px;
}

.header-acciones {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.panel {
  background-color: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 18px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.panel h2 {
  margin: 0 0 14px;
  font-size: 18px;
}

.panel-cabecera {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 14px;
}

.panel-cabecera h2 {
  margin: 0;
}

.filtros-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

label {
  font-weight: 600;
  font-size: 14px;
}

input[type='date'],
input[type='search'],
select {
  width: 100%;
  min-height: 44px;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background-color: #ffffff;
  color: #1f2937;
  font: inherit;
}

.filtros-botones {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.tabla-scroll {
  overflow-x: auto;
}

.tabla-pedidos {
  width: 100%;
  border-collapse: collapse;
}

.tabla-pedidos th,
.tabla-pedidos td {
  padding: 10px 8px;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
  font-size: 14px;
  vertical-align: top;
}

.col-centrada {
  text-align: center;
}

.badge-estado {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  text-transform: capitalize;
}

.estado-confirmado {
  background-color: #fef3c7;
  color: #92400e;
}

.estado-autorizado {
  background-color: #dcfce7;
  color: #166534;
}

.estado-rechazado {
  background-color: #fee2e2;
  color: #991b1b;
}

.resumen-celda {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.chip-dato {
  background-color: #f3f4f6;
  border-radius: 6px;
  padding: 2px 6px;
  font-size: 12px;
  font-weight: 600;
}

.acciones-fila {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.btn-accion {
  min-height: 36px;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background-color: #ffffff;
  color: #1f2937;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.btn-editar {
  border-color: #93c5fd;
  background-color: #eff6ff;
  color: #1d4ed8;
}

.btn-eliminar {
  border-color: #fca5a5;
  background-color: #fee2e2;
  color: #991b1b;
}

.confirmacion-eliminar {
  margin-top: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #991b1b;
}

.btn-eliminar-confirmar {
  padding: 4px 10px;
  border: 0;
  border-radius: 6px;
  background-color: #dc2626;
  color: #ffffff;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.btn-cancelar-mini {
  padding: 4px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background-color: #ffffff;
  font: inherit;
  cursor: pointer;
}

.paginacion {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  font-size: 14px;
  font-weight: 600;
}

.resumen-comparativo {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.caja-resumen {
  padding: 12px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #f9fafb;
}

.caja-autorizado {
  background-color: #f0fdf4;
  border-color: #bbf7d0;
}

.caja-resumen h3 {
  margin: 0 0 8px;
  font-size: 15px;
}

.caja-resumen ul {
  margin: 0;
  padding-left: 18px;
  font-size: 14px;
}

.chip-cupo {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  text-transform: capitalize;
}

.cupo-reg {
  background-color: #dbeafe;
  color: #1e40af;
}

.cupo-exc {
  background-color: #fef3c7;
  color: #92400e;
}

.controles-edicion {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}

.grupo-agregar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.grupo-agregar > select,
.grupo-agregar > input {
  flex: 1 1 220px;
}

.btn-comida {
  width: 48px;
  height: 44px;
  border: 1px solid #9ca3af;
  border-radius: 8px;
  background-color: #f3f4f6;
  color: #1f2937;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.btn-comida.seleccionada {
  background-color: #2563eb;
  border-color: #1d4ed8;
  color: #ffffff;
}

.btn-comida.seleccionada.excepcion {
  background-color: #b45309;
  border-color: #92400e;
  color: #ffffff;
}

.acciones-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.btn-principal,
.btn-secundario {
  min-height: 44px;
  padding: 10px 16px;
  border-radius: 8px;
  font: inherit;
  font-weight: 600;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.btn-principal {
  border: 0;
  background-color: #2563eb;
  color: #ffffff;
}

.btn-secundario {
  border: 1px solid #d1d5db;
  background-color: #ffffff;
  color: #1f2937;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.mensaje-exito {
  padding: 12px 14px;
  border-radius: 8px;
  margin-bottom: 14px;
  font-size: 14px;
  font-weight: 600;
  background-color: #dcfce7;
  color: #166534;
}

.estado-info {
  padding: 12px 14px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  background-color: #f3f4f6;
  color: #374151;
}

.aviso-rechazo {
  padding: 12px 14px;
  border-radius: 8px;
  margin-bottom: 14px;
  background-color: #fee2e2;
  color: #991b1b;
  font-size: 14px;
}

.texto-secundario {
  font-size: 13px;
  color: #4b5563;
}

.field-error {
  margin: 10px 0 0;
  color: #c62828;
  font-size: 14px;
}

@media (min-width: 768px) {
  .pedidos-container {
    padding: 24px;
  }

  .pedidos-header,
  .panel-cabecera {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }

  .filtros-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .resumen-comparativo {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1025px) {
  .filtros-grid {
    grid-template-columns: repeat(6, 1fr);
  }
}
</style>
