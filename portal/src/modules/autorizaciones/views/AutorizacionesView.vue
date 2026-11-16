<template>
  <main class="autorizaciones-view">
    <header class="encabezado-modulo">
      <div>
        <h1>Autorización de Pedidos</h1>
        <p>Revisión, autorización nominada y rechazo de pedidos por sector.</p>
      </div>
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
          :disabled="cargando"
          @click="cargarTodo"
        >
          Reintentar
        </button>
      </div>
    </div>

    <section class="navegacion-periodo" aria-label="Navegación de período y calendario">
      <div class="controles-periodo">
        <div class="grupo-botones-periodo">
          <button type="button" :disabled="cargando" @click="navegarPeriodo(-1)">
            ← Anterior
          </button>
          <button type="button" :disabled="cargando" @click="irAHoy">
            Hoy ({{ formatearFechaDdMmAaaa(hoyIso) }})
          </button>
          <button type="button" :disabled="cargando" @click="navegarPeriodo(1)">
            Siguiente →
          </button>
        </div>
        <span class="rango-activo-texto">
          Período:
          <strong>{{ formatearFechaDdMmAaaa(filtros.fecha_desde) }}</strong>
          <template v-if="filtros.fecha_hasta && filtros.fecha_hasta !== filtros.fecha_desde">
            al <strong>{{ formatearFechaDdMmAaaa(filtros.fecha_hasta) }}</strong>
          </template>
        </span>
      </div>

      <div class="calendario-dias" aria-label="Días con pedidos">
        <span class="calendario-etiqueta">Días con pedidos</span>
        <div v-if="diasConPedidosVisibles.length > 0" class="calendario-pills">
          <button
            v-for="dia in diasConPedidosVisibles"
            :key="dia"
            type="button"
            :class="[
              'btn-dia-cal con-pedidos',
              filtros.fecha_desde === dia ? 'seleccionado' : '',
            ]"
            :disabled="cargando"
            @click="seleccionarDiaCalendario(dia)"
          >
            <span class="dia-nombre">{{ formatearDiaCorto(dia) }}</span>
            <span class="fecha-ddmm">{{ formatearFechaDdMmAaaa(dia) }}</span>
            <span class="punto-pedido" aria-hidden="true">●</span>
          </button>
        </div>
        <span v-else class="sin-dias-pedidos">Sin días con pedidos en el período.</span>
      </div>
    </section>

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
              v-model="filtros.fecha_desde"
              type="date"
              class="date-overlay"
              aria-label="Seleccionar fecha desde en calendario"
              @change="alCambiarDateNativo('fecha_desde')"
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
              v-model="filtros.fecha_hasta"
              type="date"
              class="date-overlay"
              aria-label="Seleccionar fecha hasta en calendario"
              @change="alCambiarDateNativo('fecha_hasta')"
            />
          </div>
          <small v-if="erroresFiltro.fecha_hasta" class="error-filtro" role="alert">
            {{ erroresFiltro.fecha_hasta }}
          </small>
        </div>

        <div class="campo-filtro">
          <label for="filtro-sector">Sector</label>
          <select id="filtro-sector" v-model="filtros.sector">
            <option value="">Todos los sectores</option>
            <option v-for="sec in sectoresDisponibles" :key="sec.id" :value="sec.id">
              {{ sec.nombre }}{{ sec.estado === 'inactivo' ? ' (Inactivo)' : '' }}
            </option>
          </select>
        </div>

        <div class="campo-filtro">
          <label for="filtro-comida">Comida</label>
          <select id="filtro-comida" v-model="filtros.tipo_comida">
            <option value="">Todas las comidas</option>
            <option v-for="(nombre, id) in COMIDAS_POR_ID" :key="id" :value="id">
              {{ nombre }}
            </option>
          </select>
        </div>

        <div class="campo-filtro">
          <label for="filtro-menu">Tipo de menú</label>
          <select id="filtro-menu" v-model="filtros.tipo_menu">
            <option value="">Todos los menús</option>
            <option v-for="(nombre, id) in MENUS_POR_ID" :key="id" :value="id">
              {{ nombre }}
            </option>
          </select>
        </div>

        <div class="campo-filtro campo-corto">
          <label for="filtro-condicion">Condición</label>
          <select id="filtro-condicion" v-model="filtros.condicion">
            <option value="">Todas</option>
            <option value="regular">Regular</option>
            <option value="excepcion">Excepción</option>
          </select>
        </div>

        <div class="campo-filtro campo-corto">
          <label for="filtro-estado">Estado</label>
          <select id="filtro-estado" v-model="filtros.estado">
            <option value="">Todos</option>
            <option value="confirmado">Pendiente</option>
            <option value="autorizado">Autorizado</option>
            <option value="rechazado">Rechazado</option>
          </select>
        </div>
      </div>

      <div class="filtros-acciones-barra">
        <div class="filtros-botones">
          <button type="button" class="btn-primario" :disabled="cargando" @click="cargarTodo">
            Buscar
          </button>
          <button type="button" :disabled="cargando" @click="limpiarFiltros">
            Limpiar
          </button>
        </div>

        <div class="filtros-exportacion">
          <button
            type="button"
            class="btn-secundario"
            :disabled="cargando"
            @click="mostrarResumen = !mostrarResumen"
          >
            {{ mostrarResumen ? 'Ocultar totales' : 'Ver totales del período' }}
          </button>
          <button
            type="button"
            class="btn-csv"
            :disabled="cargando || exportandoCsv"
            @click="descargarCsv('personas')"
          >
            Exportar Personas (CSV)
          </button>
          <button
            type="button"
            class="btn-csv"
            :disabled="cargando || exportandoCsv"
            @click="descargarCsv('totales')"
          >
            Exportar Totales (CSV)
          </button>
        </div>
      </div>
    </section>

    <section
      v-if="mostrarResumen && resumenPeriodo"
      class="panel-resumen-totales"
      aria-label="Totales pedidos y autorizados del período"
    >
      <div class="tarjetas-indicadores">
        <div class="indicador-box">
          <span class="ind-label">Total pedidas</span>
          <strong class="ind-valor">{{ resumenPeriodo.total_pedido ?? 0 }}</strong>
          <small>
            Regulares: {{ resumenPeriodo.total_pedido_regulares ?? 0 }} · Excepción:
            {{ resumenPeriodo.total_pedido_excepciones ?? 0 }}
          </small>
        </div>
        <div class="indicador-box">
          <span class="ind-label">Total autorizadas</span>
          <strong class="ind-valor texto-verde">{{ resumenPeriodo.total_autorizado ?? 0 }}</strong>
        </div>
        <div class="indicador-box">
          <span class="ind-label">Diferencia (Pedidas - Autorizadas)</span>
          <strong class="ind-valor">{{ resumenPeriodo.diferencia ?? 0 }}</strong>
        </div>
      </div>

      <div v-if="(resumenPeriodo.desglose || []).length > 0" class="tabla-contenedor tabla-resumen-margin">
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
              v-for="(item, idx) in resumenPeriodo.desglose"
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
                <strong>{{ item.comida }}</strong> ({{ item.menu }})
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
import { computed, onMounted, ref } from 'vue'
import DetallePedido from '../components/DetallePedido.vue'
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

function obtenerFechaLocalIso(offsetDias = 0, baseIso = null) {
  let fecha
  if (baseIso) {
    const [a, m, d] = String(baseIso).slice(0, 10).split('-').map(Number)
    fecha = new Date(a, (m || 1) - 1, d || 1)
  } else {
    fecha = new Date()
  }
  fecha.setDate(fecha.getDate() + offsetDias)
  const anio = fecha.getFullYear()
  const mes = String(fecha.getMonth() + 1).padStart(2, '0')
  const dia = String(fecha.getDate()).padStart(2, '0')
  return `${anio}-${mes}-${dia}`
}

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

function inicioSemanaIso(isoDate) {
  const [a, m, d] = String(isoDate).slice(0, 10).split('-').map(Number)
  const fecha = new Date(a, (m || 1) - 1, d || 1)
  const diaSemana = fecha.getDay()
  const diffLunes = diaSemana === 0 ? -6 : 1 - diaSemana
  fecha.setDate(fecha.getDate() + diffLunes)
  const anio = fecha.getFullYear()
  const mes = String(fecha.getMonth() + 1).padStart(2, '0')
  const dia = String(fecha.getDate()).padStart(2, '0')
  return `${anio}-${mes}-${dia}`
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

const filtrosTexto = ref({
  fecha_desde: formatearFechaDdMmAaaa(hoyIso),
  fecha_hasta: formatearFechaDdMmAaaa(hoyIso),
})

const erroresFiltro = ref({
  fecha_desde: '',
  fecha_hasta: '',
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

const sectoresDisponibles = computed(() => {
  if (sectoresCatalogo.value.length > 0) {
    return sectoresCatalogo.value
  }
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
    if (d?.idSector && d?.sector) {
      nuevoMapa[Number(d.idSector)] = d.sector
    }
  }
  sectoresDetectados.value = nuevoMapa
}

function sincronizarTextoDesdeIso() {
  filtrosTexto.value.fecha_desde = formatearFechaDdMmAaaa(filtros.value.fecha_desde)
  filtrosTexto.value.fecha_hasta = formatearFechaDdMmAaaa(filtros.value.fecha_hasta)
  erroresFiltro.value.fecha_desde = ''
  erroresFiltro.value.fecha_hasta = ''
}

function alCambiarDateNativo(campo) {
  const iso = filtros.value[campo]
  if (iso) {
    filtrosTexto.value[campo] = formatearFechaDdMmAaaa(iso)
    erroresFiltro.value[campo] = ''
    validarFiltrosCliente()
  }
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

function parsearDdMmAaaaAIsos(texto) {
  const limpio = String(texto || '').trim()
  if (!limpio) return { iso: '', error: '' }
  const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(limpio)
  if (!match) {
    return { iso: null, error: 'Usá dd/mm/aaaa.' }
  }
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

  if (!esValida) {
    return { iso: null, error: 'Fecha inexistente.' }
  }

  const iso = `${anio}-${String(mes).padStart(2, '0')}-${String(dia).padStart(2, '0')}`
  return { iso, error: '' }
}

function validarFiltrosCliente() {
  const desdeRes = parsearDdMmAaaaAIsos(filtrosTexto.value.fecha_desde)
  const hastaRes = parsearDdMmAaaaAIsos(filtrosTexto.value.fecha_hasta)

  erroresFiltro.value.fecha_desde = desdeRes.error
  erroresFiltro.value.fecha_hasta = hastaRes.error

  if (desdeRes.error || hastaRes.error) {
    return false
  }

  if (desdeRes.iso && hastaRes.iso && desdeRes.iso > hastaRes.iso) {
    erroresFiltro.value.fecha_hasta = 'Hasta < Desde.'
    return false
  }

  if (desdeRes.iso) filtros.value.fecha_desde = desdeRes.iso
  if (hastaRes.iso) filtros.value.fecha_hasta = hastaRes.iso
  return true
}

function esPendienteAutorizacion(pedido) {
  return String(pedido?.estado || '').toLowerCase() === 'confirmado'
}

function resolverNombreSector(pedido) {
  const nombreDirecto =
    pedido?.nombreSector ||
    pedido?.sectorNombre ||
    pedido?.sector_nombre ||
    pedido?.nombre_sector
  if (typeof nombreDirecto === 'string' && nombreDirecto.trim()) {
    return nombreDirecto.trim()
  }
  if (typeof pedido?.sector === 'string' && pedido.sector.trim()) {
    return pedido.sector.trim()
  }
  const idSector = Number(pedido?.idSector ?? pedido?.sector_id ?? pedido?.sector)
  if (Number.isInteger(idSector) && mapaSectores.value[idSector]) {
    return mapaSectores.value[idSector]
  }
  return idSector ? `Sector #${idSector}` : '-'
}

function limpiarParametrosVacios(obj) {
  return Object.fromEntries(
    Object.entries(obj).filter(([, val]) => val !== '' && val !== null && val !== undefined)
  )
}

function manejarErrorHttp(err, mensajeGenerico) {
  const status = err?.status
  if (status === 503) {
    mensajeFeedback.value = {
      tipo: 'advertencia',
      texto: err?.message || 'El sistema se encuentra en mantenimiento. Intentá más tarde.',
      puedeReintentar: true,
    }
    return
  }
  if (status === 401) {
    mensajeFeedback.value = {
      tipo: 'advertencia',
      texto: err?.message || 'Tu sesión expiró o no está autenticada. Iniciá sesión nuevamente.',
      puedeReintentar: false,
    }
    return
  }
  if (status === 403) {
    mensajeFeedback.value = {
      tipo: 'error',
      texto: err?.message || 'No tenés permisos para realizar esta acción.',
      puedeReintentar: false,
    }
    return
  }
  if (status === 404 || err?.isNotFound) {
    mensajeFeedback.value = {
      tipo: 'error',
      texto: err?.message || 'El recurso solicitado no existe.',
      puedeReintentar: false,
    }
    return
  }
  if (status === 400) {
    mensajeFeedback.value = {
      tipo: 'error',
      texto: err?.message || 'Los datos o filtros ingresados no son válidos.',
      puedeReintentar: false,
    }
    return
  }
  if (err?.isConflict || status === 409) {
    mensajeFeedback.value = {
      tipo: 'advertencia',
      texto: err?.message || 'Conflicto de estado detectado. Se recargaron los datos.',
      puedeReintentar: false,
    }
    return
  }
  mensajeFeedback.value = {
    tipo: 'error',
    texto: mensajeGenerico || err?.message || 'Ocurrió un error inesperado. Intentá nuevamente.',
    puedeReintentar: true,
  }
}

async function cargarSectores() {
  if (typeof listarSectoresApi !== 'function') return
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
  if (typeof listarFechasAutorizacion !== 'function') return
  try {
    const params = limpiarParametrosVacios({
      fecha_desde: filtros.value.fecha_desde,
      fecha_hasta: filtros.value.fecha_hasta,
      sector: filtros.value.sector,
      tipo_comida: filtros.value.tipo_comida,
      tipo_menu: filtros.value.tipo_menu,
      estado: filtros.value.estado,
    })
    const res = await listarFechasAutorizacion(params)
    const lista = Array.isArray(res) ? res : Array.isArray(res?.fechas) ? res.fechas : []
    fechasConPedidos.value = lista.map((f) => String(f).slice(0, 10))
  } catch {
    fechasConPedidos.value = []
  }
}

async function cargarResumenPeriodo() {
  if (typeof obtenerResumenAutorizaciones !== 'function') return
  try {
    const params = limpiarParametrosVacios(filtros.value)
    const res = await obtenerResumenAutorizaciones(params)
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
    manejarErrorHttp(err, 'No se pudieron cargar los pedidos. Intentá nuevamente.')
  } finally {
    cargando.value = false
  }
}

async function cargarTodo() {
  if (!validarFiltrosCliente()) return
  await Promise.all([cargarPedidos(), cargarFechasCalendario(), cargarResumenPeriodo()])
}

async function descargarCsv(tipo) {
  if (!validarFiltrosCliente()) return
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
    if (tipo === 'personas') {
      await exportarPersonasAutorizadasCsv(params)
    } else {
      await exportarTotalesAutorizacionesCsv(params)
    }
  } catch (err) {
    manejarErrorHttp(err, 'No se pudo exportar el archivo CSV.')
  } finally {
    exportandoCsv.value = false
  }
}

function cambiarModoVista(nuevoModo) {
  modoVista.value = nuevoModo
  const base = filtros.value.fecha_desde || hoyIso
  if (nuevoModo === 'diaria') {
    filtros.value.fecha_desde = base
    filtros.value.fecha_hasta = base
  } else {
    const lunes = inicioSemanaIso(base)
    filtros.value.fecha_desde = lunes
    filtros.value.fecha_hasta = obtenerFechaLocalIso(6, lunes)
  }
  sincronizarTextoDesdeIso()
  cargarTodo()
}

function navegarPeriodo(direccion) {
  const paso = modoVista.value === 'semanal' ? 7 * direccion : 1 * direccion
  const nuevaBase = obtenerFechaLocalIso(paso, filtros.value.fecha_desde || hoyIso)
  if (modoVista.value === 'semanal') {
    const lunes = inicioSemanaIso(nuevaBase)
    filtros.value.fecha_desde = lunes
    filtros.value.fecha_hasta = obtenerFechaLocalIso(6, lunes)
  } else {
    filtros.value.fecha_desde = nuevaBase
    filtros.value.fecha_hasta = nuevaBase
  }
  sincronizarTextoDesdeIso()
  cargarTodo()
}

function irAHoy() {
  if (modoVista.value === 'semanal') {
    const lunes = inicioSemanaIso(hoyIso)
    filtros.value.fecha_desde = lunes
    filtros.value.fecha_hasta = obtenerFechaLocalIso(6, lunes)
  } else {
    filtros.value.fecha_desde = hoyIso
    filtros.value.fecha_hasta = hoyIso
  }
  sincronizarTextoDesdeIso()
  cargarTodo()
}

function seleccionarDiaCalendario(diaIso) {
  filtros.value.fecha_desde = diaIso
  if (modoVista.value === 'diaria') {
    filtros.value.fecha_hasta = diaIso
  }
  sincronizarTextoDesdeIso()
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
  sincronizarTextoDesdeIso()
  cargarTodo()
}

async function abrirDetallePedido(idPedido) {
  mensajeFeedback.value = { tipo: '', texto: '', puedeReintentar: false }
  try {
    pedidoSeleccionado.value = await obtenerDetalleAutorizacion(idPedido)
  } catch (err) {
    manejarErrorHttp(err, 'No se pudo obtener el detalle del pedido.')
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
        puedeReintentar: false,
      }
    } else if (tipo === 'rechazar') {
      await rechazarPedidoCompleto(payload.idPedido, {
        motivo: payload.motivo,
      })
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
    confirmacionPendiente.value = null
    manejarErrorHttp(err, 'Ocurrió un error al guardar la operación. Intentá nuevamente.')
    if (err?.isConflict || err?.status === 409) {
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
  color: #0f172a;
}

.encabezado-modulo p {
  margin: 0.2rem 0 0;
  font-size: 0.92rem;
  color: #475569;
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
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.12);
}

.navegacion-periodo {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.9rem 1.1rem;
  margin-bottom: 1rem;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
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
  font-size: 0.88rem;
  color: #334155;
}

.calendario-dias {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  border-top: 1px solid #f1f5f9;
  padding-top: 0.7rem;
}

.calendario-etiqueta {
  font-size: 0.74rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
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

.btn-dia-cal {
  min-height: 36px;
  padding: 0.3rem 0.65rem;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.82rem;
  border-radius: 8px;
}

.btn-dia-cal.con-pedidos {
  border-color: #0f766e;
  background: #ccfbf1;
  color: #0f766e;
  font-weight: 700;
}

.btn-dia-cal.con-pedidos.seleccionado {
  background: #115e59;
  border-color: #042f2e;
  color: #ffffff;
  box-shadow: inset 0 0 0 1px #99f6e4;
}

.punto-pedido {
  font-size: 0.6rem;
  line-height: 1;
}

.barra-filtros {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.95rem 1.1rem;
  margin-bottom: 1.1rem;
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
  color: #334155;
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
  border-radius: 8px;
  background: #ffffff;
  color: #0f172a;
  font-size: 0.83rem;
  box-sizing: border-box;
}

.caja-fecha-nativa input[type='text'].input-invalido {
  border-color: #dc2626;
  background: #fff5f5;
}

.icono-cal-nativo {
  position: absolute;
  right: 8px;
  color: #475569;
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
  border-radius: 8px;
  background: #ffffff;
  color: #0f172a;
  font-size: 0.83rem;
  width: 100%;
  box-sizing: border-box;
}

.campo-filtro input:focus,
.campo-filtro select:focus {
  outline: none;
  border-color: #0f766e;
  box-shadow: 0 0 0 2px rgba(15, 118, 110, 0.14);
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

.badge-estado.estado-confirmado {
  background: #fef3c7;
  color: #92400e;
  border-color: #f59e0b;
}

.badge-estado.estado-autorizado {
  background: #dcfce7;
  color: #166534;
  border-color: #86efac;
}

.badge-estado.estado-rechazado {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fca5a5;
}

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

.alerta-exito {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #86efac;
}

.alerta-advertencia {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fcd34d;
}

.alerta-error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.btn-reintentar {
  background: #ffffff;
  color: #0f172a;
}

.estado-carga,
.estado-vacio {
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
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
  max-width: 490px;
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
  padding: 0.38rem 0.8rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #0f172a;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

button:hover:not(:disabled) {
  background: #f1f5f9;
}

.btn-primario,
.btn-detalle,
.btn-ejecutar {
  background: #0f766e;
  border-color: #0f766e;
  color: #ffffff;
}

.btn-primario:hover:not(:disabled),
.btn-detalle:hover:not(:disabled),
.btn-ejecutar:hover:not(:disabled) {
  background: #115e59;
}

.btn-csv {
  background: #f0fdfa;
  border-color: #0f766e;
  color: #0f766e;
}

.btn-csv:hover:not(:disabled) {
  background: #ccfbf1;
}

button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 1024px) {
  .autorizaciones-view {
    padding: 1rem;
  }
}

@media (max-width: 767px) {
  .autorizaciones-view {
    padding: 0.85rem;
  }

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

  .rango-activo-texto {
    width: 100%;
  }
}
</style>