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
    mapa[idC] = { total, regulares, excepciones }
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
  <main class="pedido-container" aria-labelledby="titulo-nuevo-pedido">
    <header class="pedido-header">
      <div>
        <h1 id="titulo-nuevo-pedido">Nuevo pedido</h1>
        <p class="pedido-subtitulo">
          {{ nombreSector }} · Horario de corte: {{ horarioCorte }}
        </p>
      </div>
      <RouterLink class="btn-secundario" to="/inicio/jefe-servicio">
        Volver al inicio
      </RouterLink>
    </header>

    <p
      v-if="mensajeConfirmacion"
      class="mensaje-confirmacion"
      role="status"
    >
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

    <ApiErrorMessage
      :error="apiErrorMessage"
      @retry="retryOperation"
    />

    <div class="pedido-grid">
      <section class="panel" aria-labelledby="titulo-periodo">
        <h2 id="titulo-periodo">Periodicidad y fechas</h2>

        <div class="grupo-botones" role="group" aria-label="Periodicidad">
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

        <div class="campos-fechas">
          <div class="form-field">
            <label for="fecha-desde">Fecha desde</label>
            <input
              id="fecha-desde"
              v-model="fechaDesde"
              type="date"
              :min="fechaMinimaPermitida"
              :disabled="loading || loadingDatos"
              :aria-invalid="Boolean(fechaDesdeError)"
              :aria-describedby="fechaDesdeError ? 'fecha-desde-error' : undefined"
            />
            <span class="texto-formato">
              Formato: {{ formatearFecha(fechaDesde) }}
            </span>
            <p v-if="fechaDesdeError" id="fecha-desde-error" class="field-error">
              {{ fechaDesdeError }}
            </p>
          </div>

          <div v-if="periodicidad !== 'diaria'" class="form-field">
            <label for="fecha-hasta">Fecha hasta</label>
            <input
              id="fecha-hasta"
              v-model="fechaHasta"
              type="date"
              :min="fechaDesde || fechaMinimaPermitida"
              :disabled="loading || loadingDatos"
              :aria-invalid="Boolean(fechaHastaError)"
              :aria-describedby="fechaHastaError ? 'fecha-hasta-error' : undefined"
            />
            <span class="texto-formato">
              Formato: {{ formatearFecha(fechaHasta) }}
            </span>
            <p v-if="fechaHastaError" id="fecha-hasta-error" class="field-error">
              {{ fechaHastaError }}
            </p>
          </div>
        </div>

        <div v-if="fechasPeriodo.length > 1" class="dias-periodo">
          <h3>Días del período (podés desmarcar días a excluir)</h3>
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
          <p v-if="diasError" class="field-error">{{ diasError }}</p>
        </div>
      </section>

      <aside class="panel" aria-labelledby="titulo-cupos">
        <h2 id="titulo-cupos">Cupo del sector y totales</h2>

        <ul class="lista-cupos">
          <li
            v-for="comida in comidas"
            :key="comida.idTipoComida"
            class="item-cupo"
          >
            <span>{{ comida.label }}</span>
            <span>
              {{ resumenPorComida[comida.idTipoComida]?.regulares ?? 0 }}/{{
                cuposPorComida[comida.idTipoComida] ?? 0
              }}
              regulares
              <template
                v-if="(resumenPorComida[comida.idTipoComida]?.excepciones ?? 0) > 0"
              >
                · {{ resumenPorComida[comida.idTipoComida].excepciones }} exc.
              </template>
            </span>
          </li>
        </ul>

        <div class="tabla-scroll">
          <table class="tabla-resumen">
            <thead>
              <tr>
                <th scope="col">Menú</th>
                <th v-for="comida in comidas" :key="comida.idTipoComida" scope="col">
                  {{ comida.inicial }}
                </th>
                <th scope="col">Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="itemMenu in resumenPorMenu" :key="itemMenu.menu">
                <td>{{ itemMenu.menu }}</td>
                <td v-for="comida in comidas" :key="comida.idTipoComida">
                  {{ itemMenu.porComida[comida.idTipoComida] ?? 0 }}
                </td>
                <td><strong>{{ itemMenu.total }}</strong></td>
              </tr>
              <tr v-if="resumenPorMenu.length === 0">
                <td :colspan="comidas.length + 2" class="texto-vacio">
                  Sin comidas seleccionadas
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </aside>
    </div>

    <section class="panel" aria-labelledby="titulo-comensales">
      <div class="panel-cabecera">
        <h2 id="titulo-comensales">
          Personal incluido ({{ filas.length }})
        </h2>

        <div class="controles-incorporacion">
          <div class="buscar-residente">
            <label for="select-personal-sector" class="sr-only">
              Seleccionar personal fijo del sector
            </label>
            <select
              id="select-personal-sector"
              v-model="personaSectorSeleccionadaId"
              :disabled="loading || loadingDatos || personalSectorDisponibles.length === 0"
              @change="apiErrorMessage = null"
            >
              <option value="">Personal fijo del sector...</option>
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
              class="btn-secundario"
              :disabled="loading || loadingDatos || !personaSectorSeleccionadaId"
              @click="agregarPersonaDelSector"
            >
              Agregar del sector
            </button>
            <button
              type="button"
              class="btn-secundario"
              :disabled="loading || loadingDatos || personalSectorDisponibles.length === 0"
              @click="agregarTodoPersonalSector"
            >
              Incluir todo el sector
            </button>
          </div>

          <div class="buscar-residente">
            <label for="buscar-residente" class="sr-only">
              Buscar residente por nombre, apellido o DNI
            </label>
            <input
              id="buscar-residente"
              v-model="busquedaResidente"
              type="search"
              placeholder="Buscar residente por nombre, apellido o DNI"
              :disabled="loading || loadingDatos"
              @input="apiErrorMessage = null"
            />
            <button
              type="button"
              class="btn-secundario"
              :disabled="loading || loadingDatos || !busquedaResidente.trim()"
              @click="agregarResidenteFiltrado"
            >
              Agregar residente
            </button>
          </div>
        </div>
      </div>

      <p v-if="loadingDatos" class="estado-info" role="status">
        Cargando datos del sector...
      </p>

      <p v-else-if="filas.length === 0" class="estado-info" role="status">
        No hay personas incorporadas al pedido.
      </p>

      <form v-else @submit.prevent="enviarPedido" novalidate>
        <div class="tabla-scroll">
          <table class="tabla-pedido">
            <thead>
              <tr>
                <th scope="col">Persona</th>
                <th scope="col">Tipo de menú</th>
                <th
                  v-for="comida in comidas"
                  :key="comida.idTipoComida"
                  scope="col"
                  class="col-centrada"
                >
                  <div>{{ comida.label }}</div>
                  <button
                    type="button"
                    class="btn-link-accion"
                    :disabled="loading"
                    @click="alternarTodosComida(comida.idTipoComida)"
                  >
                    Todos
                  </button>
                </th>
                <th scope="col" class="col-centrada">Fila</th>
                <th scope="col">Acción</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(fila, idx) in filas" :key="fila.uid">
                <td>
                  <div class="nombre-persona">{{ fila.nombre }}</div>
                  <div class="dato-secundario">
                    DNI {{ fila.dni }}
                    <span v-if="fila.esResidente" class="etiqueta-residente">
                      Residente
                    </span>
                    <span v-else class="etiqueta-fijo">
                      Personal fijo
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
                <td>
                  <button
                    type="button"
                    class="btn-quitar"
                    :aria-label="`Quitar a ${fila.nombre}`"
                    :disabled="loading"
                    @click="quitarFila(idx)"
                  >
                    Quitar
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
            {{ diasActivos.length === 1 ? 'día' : 'días' }})
          </h3>
          <div class="tarjetas-dias">
            <article v-for="diaIso in diasActivos" :key="diaIso" class="tarjeta-dia">
              <strong>{{ formatearFecha(diaIso) }}</strong>
              <span>{{ totalSolicitudesSeleccionadas }} comidas en el día</span>
            </article>
          </div>
        </div>

        <div class="acciones-footer">
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
</template>

<style scoped>
.pedido-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px;
  color: #1f2937;
}

.pedido-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 18px;
}

.pedido-header h1 {
  margin: 0;
  color: #1d4ed8;
}

.pedido-subtitulo {
  margin: 4px 0 0;
  color: #4b5563;
  font-size: 14px;
}

.pedido-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  margin-bottom: 16px;
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

.controles-incorporacion {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.grupo-botones {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.btn-opcion {
  min-height: 44px;
  padding: 8px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background-color: #ffffff;
  color: #1f2937;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.btn-opcion.activo {
  background-color: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
}

.campos-fechas {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

label {
  font-weight: 600;
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

input:focus,
select:focus {
  border-color: #2563eb;
  outline: 2px solid rgba(37, 99, 235, 0.2);
}

input[aria-invalid='true'] {
  border-color: #c62828;
}

.texto-formato,
.dato-secundario,
.texto-vacio {
  font-size: 13px;
  color: #4b5563;
}

.dias-periodo {
  margin-top: 16px;
}

.dias-periodo h3,
.previa-dias h3 {
  margin: 0 0 8px;
  font-size: 15px;
}

.lista-dias {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.dia-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 38px;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 999px;
  background-color: #f9fafb;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.dia-item.excluido {
  opacity: 0.6;
  text-decoration: line-through;
}

.lista-cupos {
  list-style: none;
  padding: 0;
  margin: 0 0 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.item-cupo {
  display: flex;
  justify-content: space-between;
  padding-bottom: 6px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
}

.tabla-scroll {
  overflow-x: auto;
}

.tabla-pedido,
.tabla-resumen {
  width: 100%;
  border-collapse: collapse;
}

.tabla-pedido th,
.tabla-pedido td,
.tabla-resumen th,
.tabla-resumen td {
  padding: 10px 8px;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
  font-size: 14px;
}

.col-centrada {
  text-align: center;
}

.btn-link-accion {
  background: none;
  border: 0;
  padding: 4px 6px;
  min-height: 36px;
  color: #1d4ed8;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  text-decoration: underline;
  cursor: pointer;
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

.nombre-persona {
  font-weight: 600;
}

.etiqueta-menu,
.etiqueta-residente,
.etiqueta-fijo {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  background-color: #e5e7eb;
  color: #1f2937;
}

.etiqueta-residente {
  background-color: #dbeafe;
  color: #1e40af;
  margin-left: 6px;
}

.etiqueta-fijo {
  background-color: #f3f4f6;
  color: #374151;
  margin-left: 6px;
}

.buscar-residente {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.buscar-residente > input,
.buscar-residente > select {
  flex: 1 1 220px;
}

.previa-dias {
  margin-top: 16px;
}

.tarjetas-dias {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
}

.tarjeta-dia {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background-color: #f9fafb;
  font-size: 13px;
}

.acciones-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.btn-principal,
.btn-secundario,
.btn-quitar {
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

.btn-principal:hover {
  background-color: #1d4ed8;
}

.btn-secundario {
  border: 1px solid #d1d5db;
  background-color: #ffffff;
  color: #1f2937;
}

.btn-quitar {
  border: 1px solid #fca5a5;
  background-color: #fee2e2;
  color: #991b1b;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.mensaje-confirmacion,
.estado-info {
  padding: 12px 14px;
  border-radius: 8px;
  margin-bottom: 14px;
  font-size: 14px;
  font-weight: 600;
  background-color: #dcfce7;
  color: #166534;
}

.estado-info {
  background-color: #f3f4f6;
  color: #374151;
}

.aviso-conflicto {
  padding: 12px 14px;
  border-radius: 8px;
  margin-bottom: 14px;
  background-color: #fef3c7;
  border: 1px solid #fcd34d;
  color: #854d0e;
  font-size: 14px;
}

.aviso-conflicto p {
  margin: 0 0 6px;
  font-weight: 600;
}

.aviso-conflicto ul,
.lista-resultado {
  margin: 0;
  padding-left: 18px;
}

.enlace-accion {
  margin-left: 8px;
  color: #1d4ed8;
  font-weight: 600;
}

.field-error {
  margin: 0;
  color: #c62828;
  font-size: 14px;
}

.error-bloque {
  margin-top: 10px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

@media (min-width: 768px) {
  .pedido-container {
    padding: 24px;
  }

  .pedido-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }

  .campos-fechas {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1025px) {
  .pedido-grid {
    grid-template-columns: 1.4fr 1fr;
  }

  .controles-incorporacion {
    flex-direction: row;
    justify-content: flex-end;
    align-items: center;
    flex-wrap: wrap;
    width: auto;
  }
}
</style>
