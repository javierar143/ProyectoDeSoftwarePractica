<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useAuthStore } from '@/stores/auth'
import { normalizeApiError } from '@/services/api/error-handler'
import ApiErrorMessage from '@/modules/shared/components/ApiErrorMessage.vue'
import {
  obtenerConfiguracionPedidos,
  obtenerDatosCargaPedido,
  crearPedido,
} from '../services/pedidos'

const authStore = useAuthStore()

const OPCIONES_PERIODICIDAD = [
  { value: 'diaria', label: 'Diaria' },
  { value: 'semanal', label: 'Semanal' },
  { value: 'mensual', label: 'Mensual' },
]

const COMIDAS_BASE = [
  { idTipoComida: 1, label: 'Desayuno', inicial: 'D' },
  { idTipoComida: 2, label: 'Almuerzo', inicial: 'A' },
  { idTipoComida: 3, label: 'Merienda', inicial: 'M' },
  { idTipoComida: 4, label: 'Cena', inicial: 'C' },
]

function hoyLocalIso() {
  const ahora = new Date()
  const anio = ahora.getFullYear()
  const mes = String(ahora.getMonth() + 1).padStart(2, '0')
  const dia = String(ahora.getDate()).padStart(2, '0')
  return `${anio}-${mes}-${dia}`
}

function sumarDiasIso(isoStr, dias) {
  if (!isoStr) return ''
  const [y, m, d] = isoStr.split('-').map(Number)
  const fecha = new Date(y, m - 1, d + dias)
  const anio = fecha.getFullYear()
  const mes = String(fecha.getMonth() + 1).padStart(2, '0')
  const dia = String(fecha.getDate()).padStart(2, '0')
  return `${anio}-${mes}-${dia}`
}

function formatearFecha(isoStr) {
  if (!isoStr) return '—'
  const partes = String(isoStr).slice(0, 10).split('-')
  if (partes.length !== 3) return isoStr
  return `${partes[2]}/${partes[1]}/${partes[0]}`
}

const comidas = ref([...COMIDAS_BASE])
const fechaMinimaPermitida = ref(hoyLocalIso())
const horarioCorte = ref('18:00 del día anterior')

const fechaDesde = ref(sumarDiasIso(hoyLocalIso(), 1))
const fechaHasta = ref(sumarDiasIso(hoyLocalIso(), 1))
const periodicidad = ref('diaria')
const diasExcluidos = ref([])

const fechaDesdeError = ref('')
const fechaHastaError = ref('')
const diasError = ref('')
const comidasError = ref('')

const filas = ref([])
const personalSectorDisponibles = ref([])
const personaSectorSeleccionadaId = ref('')
const residentesDisponibles = ref([])
const busquedaResidente = ref('')
const cuposPorComida = ref({ 1: 0, 2: 0, 3: 0, 4: 0 })

const loadingDatos = ref(false)
const loading = ref(false)
const apiErrorMessage = ref(null)
const retryOperation = ref(null)
const mensajeConfirmacion = ref('')
const fechasConflicto = ref([])
const solicitudesConfirmadas = ref([])

const nombreSector = computed(() => {
  return (
    authStore.user?.sector?.nombre ||
    authStore.user?.nombre_sector ||
    (authStore.user?.idSector ? `Sector #${authStore.user.idSector}` : 'Sector asignado')
  )
})

const fechasPeriodo = computed(() => {
  const inicio = fechaDesde.value
  const fin = periodicidad.value === 'diaria' ? fechaDesde.value : fechaHasta.value
  if (!inicio || !fin || fin < inicio) return []

  const lista = []
  let actual = inicio
  while (actual <= fin) {
    lista.push(actual)
    actual = sumarDiasIso(actual, 1)
  }
  return lista
})

const diasActivos = computed(() => {
  return fechasPeriodo.value.filter((dia) => !diasExcluidos.value.includes(dia))
})

const textoPeriodo = computed(() => {
  if (!fechaDesde.value) return '—'
  const fin = periodicidad.value === 'diaria' ? fechaDesde.value : fechaHasta.value || fechaDesde.value
  if (!fin || fin === fechaDesde.value) return formatearFecha(fechaDesde.value)
  return `${formatearFecha(fechaDesde.value)} – ${formatearFecha(fin)}`
})

watch(fechaDesde, () => {
  fechaDesdeError.value = ''
})

watch(fechaHasta, () => {
  fechaHastaError.value = ''
})

watch(diasExcluidos, () => {
  diasError.value = ''
})

function seleccionarPeriodicidad(nuevaPeriodicidad) {
  periodicidad.value = nuevaPeriodicidad
  diasExcluidos.value = []
  diasError.value = ''
  const base = fechaDesde.value || fechaMinimaPermitida.value

  if (nuevaPeriodicidad === 'diaria') {
    fechaHasta.value = base
  } else if (nuevaPeriodicidad === 'semanal') {
    fechaHasta.value = sumarDiasIso(base, 6)
  } else if (nuevaPeriodicidad === 'mensual') {
    fechaHasta.value = sumarDiasIso(base, 29)
  }
}

function alternarDia(diaIso) {
  if (diasExcluidos.value.includes(diaIso)) {
    diasExcluidos.value = diasExcluidos.value.filter((d) => d !== diaIso)
  } else {
    diasExcluidos.value.push(diaIso)
  }
}

function esExcepcionEstimada(indiceFila, idTipoComida) {
  const fila = filas.value[indiceFila]
  if (!fila || !fila.comidas[idTipoComida]) return false

  let contador = 0
  for (let i = 0; i <= indiceFila; i += 1) {
    if (filas.value[i].comidas[idTipoComida]) {
      contador += 1
    }
  }
  const limite = Number(cuposPorComida.value[idTipoComida] ?? 0)
  return contador > limite
}

const resumenPorComida = computed(() => {
  const mapa = {}
  for (const comida of comidas.value) {
    const idC = comida.idTipoComida
    const limite = Number(cuposPorComida.value[idC] ?? 0)
    let total = 0
    filas.value.forEach((fila) => {
      if (fila.comidas[idC]) total += 1
    })
    const regulares = Math.min(total, limite)
    const excepciones = Math.max(0, total - limite)
    const porcentaje = limite > 0 ? Math.min(100, Math.round((regulares / limite) * 100)) : 0
    mapa[idC] = { total, regulares, excepciones, porcentaje }
  }
  return mapa
})

const totalSolicitudesSeleccionadas = computed(() => {
  return Object.values(resumenPorComida.value).reduce(
    (acc, item) => acc + item.total,
    0,
  )
})

const resumenPorMenu = computed(() => {
  const porMenu = new Map()
  for (const fila of filas.value) {
    const menu = fila.tipoMenu || 'General'
    if (!porMenu.has(menu)) {
      porMenu.set(menu, { menu, porComida: {}, total: 0 })
    }
    const entry = porMenu.get(menu)
    for (const comida of comidas.value) {
      const idC = comida.idTipoComida
      if (fila.comidas[idC]) {
        entry.porComida[idC] = (entry.porComida[idC] ?? 0) + 1
        entry.total += 1
      }
    }
  }
  return Array.from(porMenu.values())
})

const totalesFilaMenu = computed(() => {
  const porComida = { 1: 0, 2: 0, 3: 0, 4: 0 }
  let total = 0
  for (const item of resumenPorMenu.value) {
    for (const c of comidas.value) {
      const val = item.porComida[c.idTipoComida] ?? 0
      porComida[c.idTipoComida] += val
      total += val
    }
  }
  return { porComida, total }
})

let seqUid = 1
function mapearPersonaAFila(persona, esResidente = false) {
  const apellido = persona.apellido ?? ''
  const nombre = persona.nombre ?? ''
  const nombreCompleto =
    apellido && nombre
      ? `${apellido}, ${nombre}`
      : persona.nombreCompleto || nombre || `Persona #${persona.idPersonal ?? persona.id}`

  return {
    uid: seqUid++,
    idPersonal: Number(persona.idPersonal ?? persona.id),
    nombre: nombreCompleto,
    dni: persona.dni ?? '',
    tipoMenu:
      persona.tipoMenu?.nombre ??
      persona.tipo_menu?.nombre ??
      persona.tipoMenu ??
      'General',
    esResidente,
    comidas: {
      1: false,
      2: false,
      3: false,
      4: false,
    },
  }
}

async function cargarDatosIniciales() {
  loadingDatos.value = true
  apiErrorMessage.value = null

  try {
    const configData = await obtenerConfiguracionPedidos().catch(() => null)
    if (configData?.horario_corte) {
      horarioCorte.value = `${configData.horario_corte} del día anterior`
    }

    const usuario = authStore.user ?? {}
    const sectorId =
      usuario.idSector ??
      usuario.id_sector ??
      usuario.sector?.idSector ??
      usuario.sector?.id ??
      null
    const { personalSector, cuposSector, residentes } =
      await obtenerDatosCargaPedido(sectorId)

    const mapeadoSector = personalSector.map((p) => mapearPersonaAFila(p, false))
    personalSectorDisponibles.value = mapeadoSector
    filas.value = mapeadoSector.map((p) => ({
      ...p,
      uid: seqUid++,
      comidas: { ...p.comidas },
    }))

    const mapaCupos = { ...cuposPorComida.value }
    for (const c of cuposSector) {
      const idC = Number(c.idTipoComida ?? c.id_tipo_comida)
      if (idC) {
        mapaCupos[idC] = Number(c.cantComensales ?? c.cantidad ?? 0)
      }
    }
    cuposPorComida.value = mapaCupos

    residentesDisponibles.value = residentes.map((r) =>
      mapearPersonaAFila(r, true),
    )
  } catch (error) {
    apiErrorMessage.value = normalizeApiError(error)
  } finally {
    loadingDatos.value = false
  }
}

onMounted(cargarDatosIniciales)

function incorporarPersonaSiNoExiste(persona) {
  const yaIncluido = filas.value.some(
    (f) => f.idPersonal === persona.idPersonal,
  )
  if (yaIncluido) {
    apiErrorMessage.value = {
      message: `${persona.nombre} ya figura en el pedido.`,
      canRetry: false,
    }
    return false
  }

  apiErrorMessage.value = null
  filas.value.push({
    ...persona,
    uid: seqUid++,
    comidas: { ...persona.comidas },
  })
  return true
}

function agregarPersonaDelSector() {
  const idBuscado = Number(personaSectorSeleccionadaId.value)
  if (!idBuscado) return

  const encontrada = personalSectorDisponibles.value.find(
    (p) => p.idPersonal === idBuscado,
  )
  if (!encontrada) return

  if (incorporarPersonaSiNoExiste(encontrada)) {
    personaSectorSeleccionadaId.value = ''
  }
}

function agregarTodoPersonalSector() {
  let agregados = 0
  for (const persona of personalSectorDisponibles.value) {
    const yaIncluido = filas.value.some(
      (f) => f.idPersonal === persona.idPersonal,
    )
    if (!yaIncluido) {
      filas.value.push({
        ...persona,
        uid: seqUid++,
        comidas: { ...persona.comidas },
      })
      agregados += 1
    }
  }
  if (agregados > 0) {
    apiErrorMessage.value = null
  } else if (personalSectorDisponibles.value.length > 0) {
    apiErrorMessage.value = {
      message: 'Todo el personal fijo activo del sector ya está incluido en el pedido.',
      canRetry: false,
    }
  }
}

function agregarResidenteFiltrado() {
  const consulta = busquedaResidente.value.trim().toLowerCase()
  if (!consulta) return

  const encontrado = residentesDisponibles.value.find(
    (r) =>
      r.nombre.toLowerCase().includes(consulta) ||
      String(r.dni).toLowerCase().includes(consulta),
  )

  if (!encontrado) {
    apiErrorMessage.value = {
      message: 'No se encontró un residente activo que coincida con la búsqueda.',
      canRetry: false,
    }
    return
  }

  if (incorporarPersonaSiNoExiste(encontrado)) {
    busquedaResidente.value = ''
  }
}

function alternarComidaPersona(fila, idTipoComida) {
  comidasError.value = ''
  fila.comidas[idTipoComida] = !fila.comidas[idTipoComida]
}

function alternarTodosComida(idTipoComida) {
  if (!filas.value.length) return
  comidasError.value = ''
  const todasMarcadas = filas.value.every((f) => Boolean(f.comidas[idTipoComida]))
  filas.value.forEach((f) => {
    f.comidas[idTipoComida] = !todasMarcadas
  })
}

function alternarTodasComidasPersona(fila) {
  comidasError.value = ''
  const todas = comidas.value.every((c) => Boolean(fila.comidas[c.idTipoComida]))
  comidas.value.forEach((c) => {
    fila.comidas[c.idTipoComida] = !todas
  })
}

function quitarFila(idx) {
  filas.value.splice(idx, 1)
}

function validateForm() {
  fechaDesdeError.value = ''
  fechaHastaError.value = ''
  diasError.value = ''
  comidasError.value = ''

  let valido = true

  if (!fechaDesde.value) {
    fechaDesdeError.value = 'La fecha desde es obligatoria.'
    valido = false
  } else if (fechaDesde.value < fechaMinimaPermitida.value) {
    fechaDesdeError.value =
      'No se pueden cargar pedidos para fechas pasadas o con corte vencido.'
    valido = false
  }

  if (periodicidad.value !== 'diaria') {
    if (!fechaHasta.value) {
      fechaHastaError.value = 'La fecha hasta es obligatoria para este período.'
      valido = false
    } else if (fechaHasta.value < fechaDesde.value) {
      fechaHastaError.value =
        'La fecha hasta no puede ser anterior a la fecha desde.'
      valido = false
    }
  }

  if (diasActivos.value.length === 0) {
    diasError.value = 'Debe quedar al menos un día activo en el período.'
    valido = false
  }

  if (totalSolicitudesSeleccionadas.value === 0) {
    comidasError.value =
      'Seleccioná al menos una comida para alguna persona del listado.'
    valido = false
  }

  return valido
}

function construirPayload() {
  const diccionarioComidas = {}
  for (const comida of comidas.value) {
    const idC = comida.idTipoComida
    const ids = []
    for (const fila of filas.value) {
      if (fila.comidas[idC] && !ids.includes(fila.idPersonal)) {
        ids.push(fila.idPersonal)
      }
    }
    if (ids.length > 0) {
      diccionarioComidas[idC] = ids
    }
  }

  return {
    fecha_desde: fechaDesde.value,
    fecha_hasta:
      periodicidad.value === 'diaria' ? fechaDesde.value : fechaHasta.value,
    periodicidad: periodicidad.value,
    dias_excluidos: diasExcluidos.value,
    comidas: diccionarioComidas,
  }
}

async function enviarPedido() {
  if (loading.value) return
  apiErrorMessage.value = null
  mensajeConfirmacion.value = ''
  fechasConflicto.value = []
  solicitudesConfirmadas.value = []
  retryOperation.value = null

  if (!validateForm()) return

  loading.value = true
  try {
    const data = await crearPedido(construirPayload())
    const creados = Array.isArray(data.pedidos) ? data.pedidos : [data]
    solicitudesConfirmadas.value = creados.flatMap((p) => p.solicitudes ?? [])
    mensajeConfirmacion.value = `Pedido confirmado (${creados.length} ${
      creados.length === 1 ? 'pedido diario' : 'pedidos diarios'
    }).`
  } catch (error) {
    const status = error?.response?.status
    const normalizado = normalizeApiError(error)
    const fields = normalizado.fieldErrors ?? {}

    if (status === 400) {
      fechaDesdeError.value = fields.fecha_desde ?? ''
      fechaHastaError.value = fields.fecha_hasta ?? ''
      diasError.value = fields.dias_excluidos ?? fields.dias ?? ''
      comidasError.value = fields.comidas ?? ''
    }

    if (status === 409) {
      const data = error?.response?.data ?? {}
      fechasConflicto.value = Array.isArray(data.fechas_conflicto)
        ? data.fechas_conflicto
        : []
      apiErrorMessage.value = {
        ...normalizado,
        message:
          data.error ||
          data.message ||
          'Ya existe un pedido para este sector en alguna de las fechas indicadas.',
        canRetry: false,
      }
      return
    }

    apiErrorMessage.value = normalizado
    if (normalizado.canRetry) {
      retryOperation.value = enviarPedido
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="vista-crear-pedido">
    <!-- Espacio reservado para la barra de navegación del layout -->
    <slot name="navbar" />

    <main class="pedido-container" aria-labelledby="titulo-nuevo-pedido">
      <header class="pedido-header">
        <div>
          <p class="pedido-sector">{{ nombreSector }}</p>
          <h1 id="titulo-nuevo-pedido">Nuevo pedido</h1>
        </div>
        <div class="header-acciones">
          <RouterLink class="btn-secundario" to="/inicio/jefe-servicio">
            Inicio
          </RouterLink>
        </div>
      </header>

      <p v-if="mensajeConfirmacion" class="mensaje-confirmacion" role="status">
        {{ mensajeConfirmacion }}
      </p>

      <div v-if="fechasConflicto.length" class="aviso-conflicto" role="status">
        <p>Fechas con pedido existente para este sector:</p>
        <ul>
          <li v-for="item in fechasConflicto" :key="item.fecha">
            {{ formatearFecha(item.fecha) }}
            <RouterLink
              v-if="item.requestId"
              class="enlace-accion"
              :to="`/jefe-servicio/pedidos/${item.requestId}/editar`"
            >
              Editar pedido #{{ item.requestId }}
            </RouterLink>
          </li>
        </ul>
      </div>

      <ApiErrorMessage :error="apiErrorMessage" @retry="retryOperation" />

      <!-- Barra superior: Periodicidad, Período y Horario de corte -->
      <section class="panel panel-superior" aria-labelledby="titulo-periodo">
        <div class="barra-config">
          <div class="bloque-config">
            <span id="titulo-periodo" class="etiqueta-bloque">Periodicidad</span>
            <div class="grupo-botones" role="group" aria-labelledby="titulo-periodo">
              <button
                v-for="opcion in OPCIONES_PERIODICIDAD"
                :key="opcion.value"
                type="button"
                :class="['btn-opcion', { activo: periodicidad === opcion.value }]"
                :aria-pressed="periodicidad === opcion.value"
                :disabled="loading || loadingDatos"
                @click="seleccionarPeriodicidad(opcion.value)"
              >
                {{ opcion.label }}
              </button>
            </div>
          </div>

          <div class="bloque-config">
            <span class="etiqueta-bloque">Período</span>
            <div class="pill-periodo" aria-live="polite">
              {{ textoPeriodo }}
            </div>
          </div>

          <div class="bloque-config bloque-corte">
            <span class="etiqueta-bloque">Horario de corte</span>
            <div class="pill-corte">
              <svg class="icono-mini" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <circle cx="10" cy="10" r="7.5" />
                <path stroke-linecap="round" d="M10 6v4.2l2.8 1.6" />
              </svg>
              <span>Corte: {{ horarioCorte }}</span>
            </div>
          </div>
        </div>

        <div class="campos-fechas">
          <div class="form-field">
            <label for="fecha-desde">
              Fecha desde <span class="formato-inline">({{ formatearFecha(fechaDesde) }})</span>
            </label>
            <input
              id="fecha-desde"
              v-model="fechaDesde"
              type="date"
              :min="fechaMinimaPermitida"
              :disabled="loading || loadingDatos"
              :aria-invalid="Boolean(fechaDesdeError)"
              :aria-describedby="fechaDesdeError ? 'fecha-desde-error' : undefined"
            />
            <p v-if="fechaDesdeError" id="fecha-desde-error" class="field-error" role="alert">
              {{ fechaDesdeError }}
            </p>
          </div>

          <div v-if="periodicidad !== 'diaria'" class="form-field">
            <label for="fecha-hasta">
              Fecha hasta <span class="formato-inline">({{ formatearFecha(fechaHasta) }})</span>
            </label>
            <input
              id="fecha-hasta"
              v-model="fechaHasta"
              type="date"
              :min="fechaDesde || fechaMinimaPermitida"
              :disabled="loading || loadingDatos"
              :aria-invalid="Boolean(fechaHastaError)"
              :aria-describedby="fechaHastaError ? 'fecha-hasta-error' : undefined"
            />
            <p v-if="fechaHastaError" id="fecha-hasta-error" class="field-error" role="alert">
              {{ fechaHastaError }}
            </p>
          </div>
        </div>

        <div v-if="fechasPeriodo.length > 1" class="dias-periodo">
          <span class="etiqueta-bloque">Días incluidos (podés desmarcar días a excluir)</span>
          <div class="lista-dias">
            <label
              v-for="diaIso in fechasPeriodo"
              :key="diaIso"
              :class="['dia-item', { excluido: diasExcluidos.includes(diaIso) }]"
            >
              <input
                type="checkbox"
                :checked="!diasExcluidos.includes(diaIso)"
                :disabled="loading || loadingDatos"
                @change="alternarDia(diaIso)"
              />
              <span>{{ formatearFecha(diaIso) }}</span>
            </label>
          </div>
          <p v-if="diasError" class="field-error" role="alert">{{ diasError }}</p>
        </div>
      </section>

      <!-- Cuerpo principal: Matriz de personas (izquierda) + Cupos y totales (derecha) -->
      <div class="pedido-cuerpo">
        <section class="panel" aria-labelledby="titulo-comensales">
          <div class="panel-cabecera">
            <h2 id="titulo-comensales">
              Personal incluido <span class="contador-badge">({{ filas.length }})</span>
            </h2>

            <div class="acciones-rapidas">
              <button
                type="button"
                class="btn-secundario btn-compacto"
                :disabled="loading || loadingDatos || personalSectorDisponibles.length === 0"
                @click="agregarTodoPersonalSector"
              >
                Incluir todo el sector
              </button>
            </div>
          </div>

          <div class="controles-incorporacion">
            <div class="campo-incorporar">
              <label for="select-personal-sector">Agregar personal fijo del sector</label>
              <div class="grupo-inline">
                <select
                  id="select-personal-sector"
                  v-model="personaSectorSeleccionadaId"
                  :disabled="loading || loadingDatos || personalSectorDisponibles.length === 0"
                  @change="apiErrorMessage = null"
                >
                  <option value="">Seleccionar personal del sector...</option>
                  <option
                    v-for="persona in personalSectorDisponibles"
                    :key="persona.idPersonal"
                    :value="persona.idPersonal"
                  >
                    {{ persona.nombre }} (DNI {{ persona.dni }})
                  </option>
                </select>
                <button
                  type="button"
                  class="btn-secundario btn-compacto"
                  :disabled="loading || loadingDatos || !personaSectorSeleccionadaId"
                  @click="agregarPersonaDelSector"
                >
                  Agregar
                </button>
              </div>
            </div>

            <div class="campo-incorporar">
              <label for="buscar-residente">Agregar residente</label>
              <div class="barra-busqueda">
                <svg class="barra-busqueda__lupa" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <circle cx="9" cy="9" r="6" />
                  <path stroke-linecap="round" d="m13.5 13.5 4 4" />
                </svg>
                <input
                  id="buscar-residente"
                  v-model="busquedaResidente"
                  type="search"
                  placeholder="Buscar por apellido, nombre o DNI..."
                  :disabled="loading || loadingDatos"
                  @input="apiErrorMessage = null"
                />
                <button
                  type="button"
                  class="btn-secundario btn-compacto"
                  :disabled="loading || loadingDatos || !busquedaResidente.trim()"
                  @click="agregarResidenteFiltrado"
                >
                  Agregar
                </button>
              </div>
            </div>
          </div>

          <p v-if="loadingDatos" class="estado-info" role="status">
            Cargando datos del sector...
          </p>

          <p v-else-if="filas.length === 0" class="estado-info" role="status">
            No hay personas incorporadas al pedido. Agregá personal del sector o un residente.
          </p>

          <form v-else @submit.prevent="enviarPedido" novalidate>
            <div class="tabla-scroll">
              <table class="tabla-pedido">
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
                      <div class="cabecera-comida">
                        <span>{{ comida.label }}</span>
                        <button
                          type="button"
                          class="btn-link-accion"
                          :disabled="loading"
                          @click="alternarTodosComida(comida.idTipoComida)"
                        >
                          Todos
                        </button>
                      </div>
                    </th>
                    <th scope="col" class="col-centrada">Fila</th>
                    <th scope="col" class="col-centrada">Acción</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(fila, idx) in filas" :key="fila.uid">
                    <td>
                      <div class="nombre-persona">{{ fila.nombre }}</div>
                      <div class="dato-secundario">
                        <span>DNI {{ fila.dni || '—' }}</span>
                        <span :class="fila.esResidente ? 'etiqueta-residente' : 'etiqueta-fijo'">
                          {{ fila.esResidente ? 'Residente' : 'Fijo' }}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span class="etiqueta-menu">{{ fila.tipoMenu }}</span>
                    </td>
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
                            excepcion: esExcepcionEstimada(idx, comida.idTipoComida),
                          },
                        ]"
                        :aria-pressed="Boolean(fila.comidas[comida.idTipoComida])"
                        :aria-label="`${comida.label} para ${fila.nombre}`"
                        :disabled="loading"
                        @click="alternarComidaPersona(fila, comida.idTipoComida)"
                      >
                        <span v-if="fila.comidas[comida.idTipoComida]">
                          {{ esExcepcionEstimada(idx, comida.idTipoComida) ? 'EXC' : '✓' }}
                        </span>
                      </button>
                    </td>
                    <td class="col-centrada">
                      <button
                        type="button"
                        class="btn-link-accion"
                        :disabled="loading"
                        @click="alternarTodasComidasPersona(fila)"
                      >
                        Todas
                      </button>
                    </td>
                    <td class="col-centrada">
                      <button
                        type="button"
                        class="btn-quitar"
                        :aria-label="`Quitar a ${fila.nombre}`"
                        title="Quitar persona"
                        :disabled="loading"
                        @click="quitarFila(idx)"
                      >
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                          <path stroke-linecap="round" d="M5 5l10 10M15 5 5 15" />
                        </svg>
                        <span>Quitar</span>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <p v-if="comidasError" class="field-error error-bloque" role="alert">
              {{ comidasError }}
            </p>

            <div
              v-if="diasActivos.length > 0 && totalSolicitudesSeleccionadas > 0"
              class="previa-dias"
            >
              <h3>
                Detalle por día ({{ diasActivos.length }}
                {{ diasActivos.length === 1 ? 'día activo' : 'días activos' }})
              </h3>
              <div class="tarjetas-dias">
                <article v-for="diaIso in diasActivos" :key="diaIso" class="tarjeta-dia">
                  <strong>{{ formatearFecha(diaIso) }}</strong>
                  <span>{{ totalSolicitudesSeleccionadas }} comidas/día</span>
                </article>
              </div>
            </div>

            <div class="acciones-footer">
              <span class="resumen-seleccion" aria-live="polite">
                {{ totalSolicitudesSeleccionadas }} comida(s) seleccionadas ·
                {{ diasActivos.length }} día(s)
              </span>
              <button
                type="submit"
                class="btn-principal"
                :disabled="loading || loadingDatos || filas.length === 0"
              >
                {{ loading ? 'Confirmando pedido...' : 'Confirmar pedido' }}
              </button>
            </div>
          </form>
        </section>

        <!-- Panel lateral derecho: Cupo por comida + Totales por menú -->
        <aside class="panel panel-lateral" aria-labelledby="titulo-cupos">
          <div class="bloque-lateral">
            <h2 id="titulo-cupos" class="titulo-lateral">Cupo del sector por comida</h2>
            <ul class="lista-cupos">
              <li
                v-for="comida in comidas"
                :key="comida.idTipoComida"
                class="item-cupo"
              >
                <div class="item-cupo__cabecera">
                  <strong>{{ comida.label }}</strong>
                  <span class="item-cupo__valores">
                    {{ resumenPorComida[comida.idTipoComida]?.regulares ?? 0 }}/{{
                      cuposPorComida[comida.idTipoComida] ?? 0
                    }}
                    regulares
                    <template
                      v-if="(resumenPorComida[comida.idTipoComida]?.excepciones ?? 0) > 0"
                    >
                      · <span class="texto-exc">{{ resumenPorComida[comida.idTipoComida].excepciones }} exc.</span>
                    </template>
                  </span>
                </div>
                <div class="barra-cupo" aria-hidden="true">
                  <span :style="{ width: `${resumenPorComida[comida.idTipoComida]?.porcentaje ?? 0}%` }"></span>
                </div>
              </li>
            </ul>
          </div>

          <div class="bloque-lateral">
            <h2 class="titulo-lateral">Totales por tipo de menú</h2>
            <div class="tabla-scroll">
              <table class="tabla-resumen">
                <thead>
                  <tr>
                    <th scope="col">Menú</th>
                    <th v-for="comida in comidas" :key="comida.idTipoComida" scope="col" class="num">
                      {{ comida.inicial }}
                    </th>
                    <th scope="col" class="num">Total</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="itemMenu in resumenPorMenu" :key="itemMenu.menu">
                    <td>{{ itemMenu.menu }}</td>
                    <td v-for="comida in comidas" :key="comida.idTipoComida" class="num">
                      {{ itemMenu.porComida[comida.idTipoComida] ?? 0 }}
                    </td>
                    <td class="num"><strong>{{ itemMenu.total }}</strong></td>
                  </tr>
                  <tr v-if="resumenPorMenu.length === 0">
                    <td :colspan="comidas.length + 2" class="texto-vacio">
                      Sin comidas seleccionadas
                    </td>
                  </tr>
                </tbody>
                <tfoot v-if="resumenPorMenu.length > 0">
                  <tr>
                    <th scope="row">Total</th>
                    <td v-for="comida in comidas" :key="comida.idTipoComida" class="num">
                      {{ totalesFilaMenu.porComida[comida.idTipoComida] ?? 0 }}
                    </td>
                    <td class="num"><strong>{{ totalesFilaMenu.total }}</strong></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </aside>
      </div>

      <section
        v-if="solicitudesConfirmadas.length > 0"
        class="panel"
        aria-labelledby="titulo-resultado-api"
      >
        <h2 id="titulo-resultado-api">Condición confirmada por el servidor</h2>
        <ul class="lista-resultado">
          <li v-for="(sol, index) in solicitudesConfirmadas" :key="index">
            {{ formatearFecha(sol.fecha_vianda) }} · Persona #{{ sol.idPersonal }} ·
            Comida #{{ sol.idTipoComida }} · <strong>{{ sol.condicionCupo }}</strong>
          </li>
        </ul>
      </section>
    </main>
  </div>
</template>

<style scoped>
.vista-crear-pedido {
  --fuente: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --c-texto: #1e293b;
  --c-texto-sec: #64748b;
  --c-borde: #e2e8f0;
  --c-borde-fuerte: #cbd5e1;
  --c-fondo: #f8fafc;
  --c-superficie: #ffffff;
  --c-primario: #2563eb;
  --c-primario-hover: #1d4ed8;
  --c-primario-suave: #eff6ff;
  --c-verde-texto: #15803d;
  --c-verde-suave: #f0fdf4;
  --c-verde-borde: #bbf7d0;
  --c-ambar-texto: #b45309;
  --c-ambar-suave: #fffbeb;
  --c-ambar-borde: #fde68a;
  --c-rojo-texto: #b91c1c;
  --c-rojo-suave: #fef2f2;
  --c-rojo-borde: #fecaca;
  --c-exc-texto: #6d28d9;
  --c-exc-suave: #f5f3ff;
  --c-exc-borde: #ddd6fe;

  font-family: var(--fuente);
  color: var(--c-texto);
  -webkit-font-smoothing: antialiased;
}

.pedido-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 1rem;
}

:focus-visible {
  outline: 2px solid var(--c-primario);
  outline-offset: 2px;
}

/* ---------- Encabezado ---------- */
.pedido-header {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}

.pedido-sector {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--c-primario);
}

.pedido-header h1 {
  margin: 0.15rem 0 0;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.header-acciones {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

/* ---------- Paneles ---------- */
.panel {
  background-color: var(--c-superficie);
  border: 1px solid var(--c-borde);
  border-radius: 10px;
  padding: 1rem;
  margin-bottom: 1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  min-width: 0;
}

.panel h2 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
}

/* ---------- Barra superior de configuración ---------- */
.barra-config {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid var(--c-borde);
}

.bloque-config {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 0;
}

.etiqueta-bloque {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--c-texto-sec);
}

.grupo-botones {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.btn-opcion {
  min-height: 36px;
  padding: 0.35rem 0.8rem;
  border: 1px solid var(--c-borde-fuerte);
  border-radius: 7px;
  background-color: var(--c-superficie);
  color: var(--c-texto);
  font-family: var(--fuente);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-opcion.activo {
  background-color: var(--c-primario);
  border-color: var(--c-primario);
  color: #ffffff;
}

.pill-periodo {
  display: inline-flex;
  align-items: center;
  min-height: 36px;
  padding: 0.35rem 0.75rem;
  border: 1px solid var(--c-borde);
  border-radius: 7px;
  background-color: var(--c-fondo);
  font-size: 0.84rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.pill-corte {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 36px;
  padding: 0.35rem 0.75rem;
  border: 1px solid var(--c-ambar-borde);
  border-radius: 7px;
  background-color: var(--c-ambar-suave);
  color: var(--c-ambar-texto);
  font-size: 0.8rem;
  font-weight: 600;
}

.icono-mini {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

.campos-fechas {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.75rem;
  margin-top: 0.85rem;
}

.campos-fechas > *,
.campo-incorporar,
.grupo-inline,
.barra-busqueda {
  min-width: 0;
  max-width: 100%;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--c-texto-sec);
}

.formato-inline {
  font-weight: 500;
  color: var(--c-primario);
}

input[type='date'],
input[type='search'],
select {
  display: block;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  height: 36px;
  min-height: 36px;
  padding: 0.3rem 0.6rem;
  border: 1px solid var(--c-borde-fuerte);
  border-radius: 7px;
  background-color: var(--c-superficie);
  color: var(--c-texto);
  font-family: var(--fuente);
  font-size: 0.84rem;
  box-sizing: border-box;
}

input[aria-invalid='true'] {
  border-color: var(--c-rojo-texto);
  background-color: var(--c-rojo-suave);
}

input:disabled,
select:disabled {
  background-color: var(--c-fondo);
  color: var(--c-texto-sec);
}

/* ---------- Días del período ---------- */
.dias-periodo {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  margin-top: 0.85rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--c-borde);
}

.lista-dias {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.dia-item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-height: 32px;
  padding: 0.25rem 0.65rem;
  border: 1px solid var(--c-borde-fuerte);
  border-radius: 999px;
  background-color: var(--c-fondo);
  color: var(--c-texto);
  font-size: 0.78rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  cursor: pointer;
}

.dia-item input[type='checkbox'] {
  width: auto;
  min-height: auto;
  height: auto;
  margin: 0;
}

.dia-item.excluido {
  opacity: 0.55;
  text-decoration: line-through;
  background-color: var(--c-superficie);
}

/* ---------- Cuerpo principal (2 columnas en escritorio) ---------- */
.pedido-cuerpo {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 1rem;
  align-items: start;
}

.panel-cabecera {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.85rem;
}

.contador-badge {
  color: var(--c-texto-sec);
  font-weight: 600;
}

.controles-incorporacion {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.75rem;
  margin-bottom: 0.9rem;
  padding: 0.75rem;
  border: 1px solid var(--c-borde);
  border-radius: 8px;
  background-color: var(--c-fondo);
}

.grupo-inline {
  display: flex;
  gap: 0.45rem;
  align-items: center;
}

.grupo-inline select {
  flex: 1;
}

.barra-busqueda {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.barra-busqueda__lupa {
  position: absolute;
  left: 0.65rem;
  width: 15px;
  height: 15px;
  color: var(--c-texto-sec);
  pointer-events: none;
}

.barra-busqueda input[type='search'] {
  flex: 1;
  padding-left: 2.1rem;
  border-radius: 999px;
  background-color: var(--c-superficie);
}

/* ---------- Tablas ---------- */
.tabla-scroll {
  width: 100%;
  overflow-x: auto;
  border: 1px solid var(--c-borde);
  border-radius: 8px;
  background-color: var(--c-superficie);
}

.tabla-pedido,
.tabla-resumen {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}

.tabla-pedido th,
.tabla-pedido td,
.tabla-resumen th,
.tabla-resumen td {
  padding: 0.55rem 0.6rem;
  border-bottom: 1px solid var(--c-borde);
  text-align: left;
  vertical-align: middle;
}

.tabla-pedido thead th,
.tabla-resumen thead th,
.tabla-resumen tfoot th,
.tabla-resumen tfoot td {
  background-color: var(--c-fondo);
  color: var(--c-texto-sec);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.tabla-pedido tbody tr:hover {
  background-color: #f8fafc;
}

.tabla-pedido tbody tr:last-child td {
  border-bottom: 0;
}

.col-centrada {
  text-align: center !important;
}

.num {
  text-align: right !important;
  font-variant-numeric: tabular-nums;
}

.cabecera-comida {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.1rem;
}

.btn-link-accion {
  background: none;
  border: 0;
  padding: 0.1rem 0.25rem;
  color: var(--c-primario);
  font-family: var(--fuente);
  font-size: 0.75rem;
  font-weight: 600;
  text-decoration: underline;
  cursor: pointer;
}

.btn-comida {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 38px;
  border: 1px solid var(--c-borde-fuerte);
  border-radius: 7px;
  background-color: var(--c-superficie);
  color: var(--c-texto);
  font-family: var(--fuente);
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.15s, border-color 0.15s;
}

.btn-comida.seleccionada {
  background-color: var(--c-primario);
  border-color: var(--c-primario-hover);
  color: #ffffff;
}

.btn-comida.seleccionada.excepcion {
  background-color: var(--c-exc-suave);
  border: 1px dashed var(--c-exc-texto);
  color: var(--c-exc-texto);
  font-size: 0.72rem;
}

.nombre-persona {
  font-weight: 600;
}

.dato-secundario {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.15rem;
  font-size: 0.76rem;
  color: var(--c-texto-sec);
}

.etiqueta-menu,
.etiqueta-residente,
.etiqueta-fijo {
  display: inline-flex;
  align-items: center;
  padding: 0.12rem 0.45rem;
  border-radius: 5px;
  font-size: 0.74rem;
  font-weight: 600;
  white-space: nowrap;
}

.etiqueta-menu {
  background-color: var(--c-fondo);
  border: 1px solid var(--c-borde);
  color: var(--c-texto);
}

.etiqueta-residente {
  background-color: var(--c-primario-suave);
  color: var(--c-primario-hover);
}

.etiqueta-fijo {
  background-color: var(--c-fondo);
  border: 1px solid var(--c-borde);
  color: var(--c-texto-sec);
}

.btn-quitar {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  height: 30px;
  padding: 0 0.55rem;
  border: 1px solid var(--c-rojo-borde);
  border-radius: 6px;
  background-color: var(--c-rojo-suave);
  color: var(--c-rojo-texto);
  font-family: var(--fuente);
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
}

.btn-quitar svg {
  width: 13px;
  height: 13px;
}

.btn-quitar:hover:not(:disabled) {
  background-color: #fee2e2;
}

/* ---------- Panel lateral (Cupos y Totales) ---------- */
.panel-lateral {
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.bloque-lateral {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.titulo-lateral {
  margin: 0;
  font-size: 0.85rem !important;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--c-texto-sec);
}

.lista-cupos {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.item-cupo {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.item-cupo__cabecera {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
  font-size: 0.82rem;
}

.item-cupo__valores {
  font-variant-numeric: tabular-nums;
  color: var(--c-texto-sec);
  text-align: right;
}

.texto-exc {
  color: var(--c-exc-texto);
  font-weight: 700;
}

.barra-cupo {
  height: 6px;
  border-radius: 999px;
  background-color: var(--c-borde);
  overflow: hidden;
}

.barra-cupo span {
  display: block;
  height: 100%;
  background-color: var(--c-primario);
}

.texto-vacio {
  text-align: center !important;
  font-size: 0.8rem;
  color: var(--c-texto-sec);
}

/* ---------- Detalle por día y footer ---------- */
.previa-dias {
  margin-top: 1rem;
  padding-top: 0.85rem;
  border-top: 1px solid var(--c-borde);
}

.previa-dias h3 {
  margin: 0 0 0.5rem;
  font-size: 0.88rem;
  font-weight: 700;
}

.tarjetas-dias {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.5rem;
}

.tarjeta-dia {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0.55rem 0.7rem;
  border: 1px solid var(--c-borde);
  border-radius: 7px;
  background-color: var(--c-fondo);
  font-size: 0.78rem;
}

.tarjeta-dia span {
  color: var(--c-texto-sec);
  font-variant-numeric: tabular-nums;
}

.acciones-footer {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  margin-top: 1rem;
  padding-top: 0.85rem;
  border-top: 1px solid var(--c-borde);
}

.resumen-seleccion {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--c-texto-sec);
  font-variant-numeric: tabular-nums;
}

.btn-principal,
.btn-secundario {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 0.4rem 0.9rem;
  border-radius: 7px;
  font-family: var(--fuente);
  font-size: 0.84rem;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
}

.btn-compacto {
  height: 36px;
  min-height: 36px;
  padding: 0.3rem 0.75rem;
  font-size: 0.8rem;
  flex-shrink: 0;
}

.btn-principal {
  border: 0;
  background-color: var(--c-primario);
  color: #ffffff;
}

.btn-principal:hover:not(:disabled) {
  background-color: var(--c-primario-hover);
}

.btn-secundario {
  border: 1px solid var(--c-borde-fuerte);
  background-color: var(--c-superficie);
  color: var(--c-texto);
}

.btn-secundario:hover:not(:disabled) {
  background-color: var(--c-fondo);
}

button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.mensaje-confirmacion,
.estado-info {
  padding: 0.7rem 0.9rem;
  border-radius: 8px;
  margin-bottom: 0.9rem;
  font-size: 0.85rem;
  font-weight: 600;
  background-color: var(--c-verde-suave);
  border: 1px solid var(--c-verde-borde);
  color: var(--c-verde-texto);
}

.estado-info {
  background-color: var(--c-fondo);
  border-color: var(--c-borde);
  color: var(--c-texto-sec);
}

.aviso-conflicto {
  padding: 0.7rem 0.9rem;
  border-radius: 8px;
  margin-bottom: 0.9rem;
  background-color: var(--c-ambar-suave);
  border: 1px solid var(--c-ambar-borde);
  color: var(--c-ambar-texto);
  font-size: 0.84rem;
}

.aviso-conflicto p {
  margin: 0 0 0.35rem;
  font-weight: 600;
}

.aviso-conflicto ul,
.lista-resultado {
  margin: 0;
  padding-left: 1.15rem;
  font-size: 0.82rem;
}

.enlace-accion {
  margin-left: 0.5rem;
  color: var(--c-primario);
  font-weight: 600;
}

.field-error {
  margin: 0.15rem 0 0;
  color: var(--c-rojo-texto);
  font-size: 0.78rem;
  font-weight: 600;
}

.error-bloque {
  margin-top: 0.65rem;
}

@media (min-width: 768px) {
  .pedido-container {
    padding: 1.25rem 1.5rem;
  }

  .pedido-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }

  .barra-config {
    flex-direction: row;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
  }

  .campos-fechas {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .controles-incorporacion {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .acciones-footer {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

@media (min-width: 1025px) {
  .pedido-cuerpo {
    grid-template-columns: minmax(0, 1.85fr) minmax(270px, 1fr);
  }
}
</style>
