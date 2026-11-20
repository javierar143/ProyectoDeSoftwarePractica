<template>
  <main
    class="kiosko-claro-viewport"
    @pointerdown="segundosInactividad = SEGUNDOS_LIMITE_INACTIVIDAD"
    @keydown="segundosInactividad = SEGUNDOS_LIMITE_INACTIVIDAD"
  >
    <div class="kiosko-contenedor">
      <header class="kiosko-encabezado">
        <div>
          <span class="badge-turno-activo">
            ● TURNO EN CURSO · {{ comidaEnCursoObj.rango }}
          </span>
          <div class="titulo-y-reloj">
            <h1>{{ comidaEnCursoObj.nombre }}</h1>
            <span class="reloj-kiosko">{{ fechaActualTexto }} · {{ horaActualTexto }} hs</span>
          </div>
        </div>

        <div class="encabezado-controles">
          <div class="selector-turno-segmentado" role="group" aria-label="Cambiar turno de comida">
            <button
              v-for="comida in COMIDAS_CONFIG"
              :key="comida.id"
              type="button"
              :class="['btn-segmento', comidaEnCursoId === comida.id ? 'activo' : '']"
              @click="seleccionarComidaManual(comida.id)"
            >
              {{ comida.nombre }}
            </button>
          </div>

          <button
            type="button"
            class="btn-panel-discreto"
            @click="menuDiscretoAbierto = true"
          >
            Resumen y Turno
          </button>
        </div>
      </header>

      <div
        v-if="alerta.texto"
        :class="['alerta-kiosko', `alerta-${alerta.tipo}`]"
        role="alert"
      >
        <span>{{ alerta.texto }}</span>
        <button v-if="reintentoConsulta" type="button" :disabled="buscando" @click="reintentarConsulta">Reintentar</button>
        <button type="button" class="btn-cerrar-alerta" @click="alerta.texto = ''">Cerrar</button>
      </div>

      <div class="kiosko-layout-grid">
        <!-- COLUMNA IZQUIERDA: Búsqueda -->
        <section class="tarjeta-kiosko" aria-label="Buscador de comensales">
          <div class="buscador-header">
            <h2>Buscar comensal</h2>
            <div class="selector-modo-busqueda" role="tablist">
              <button
                v-for="m in [
                  { id: 'dni', label: 'Por DNI' },
                  { id: 'nombre', label: 'Nombre' },
                  { id: 'sector', label: 'Por Sector' },
                ]"
                :key="m.id"
                type="button"
                role="tab"
                :aria-selected="modoBusqueda === m.id"
                :class="['btn-modo-busq', modoBusqueda === m.id ? 'activo' : '']"
                @click="cambiarModoBusqueda(m.id)"
              >
                {{ m.label }}
              </button>
            </div>
          </div>

          <TecladoDniKiosko
            v-if="modoBusqueda === 'dni'"
            v-model="dniInput"
            :buscando="buscando"
            @buscar="buscarPorDni"
          />

          <div v-else-if="modoBusqueda === 'nombre'" class="bloque-alternativo">
            <label for="input-nya" class="label-estandar">Apellido o Nombre de la persona</label>
            <div class="barra-input-boton">
              <input
                id="input-nya"
                v-model="nyaInput"
                type="text"
                placeholder="Ej: Gómez o Laura"
                class="input-claro-tactil"
                @keyup.enter="buscarPorNombre"
              />
              <button
                type="button"
                class="btn-primario-tactil"
                :disabled="buscando || nyaInput.trim().length < 2"
                @click="buscarPorNombre"
              >
                Buscar
              </button>
            </div>

            <div v-if="resultadosNombre.length > 0" class="lista-resultados-clara">
              <div
                v-for="pers in resultadosNombre"
                :key="pers.idPersonal"
                class="fila-persona-resultado"
              >
                <div>
                  <strong>{{ pers.apellido }}, {{ pers.nombre }}</strong>
                  <span class="res-detalle">DNI {{ pers.dni }} · {{ pers.sector }}</span>
                </div>
                <button
                  type="button"
                  class="btn-incluir-chico"
                  :disabled="estaEnRetiro(pers.idPersonal)"
                  @click="agregarPersonaAlRetiro(pers)"
                >
                  {{ estaEnRetiro(pers.idPersonal) ? 'En bandeja' : '+ Agregar' }}
                </button>
              </div>
            </div>
            <div v-else-if="busquedaSinResultados" class="bandeja-vacia">
              No se encontraron personas con comidas autorizadas hoy para esa búsqueda.
            </div>
          </div>

          <div v-else class="bloque-alternativo">
            <label for="select-sector" class="label-estandar">
              Seleccionar Sector (comidas autorizadas pendientes hoy)
            </label>
            <div class="barra-input-boton">
              <select
                id="select-sector"
                v-model="sectorFiltroId"
                class="input-claro-tactil"
                @change="buscarPorSector"
              >
                <option value="">Elegí un sector...</option>
                <option v-for="sec in sectoresOpciones" :key="sec.id" :value="sec.id">
                  {{ sec.nombre }}
                </option>
              </select>
              <button
                v-if="resultadosSector.length > 0"
                type="button"
                class="btn-primario-tactil"
                @click="resultadosSector.forEach(agregarPersonaAlRetiro)"
              >
                + Todos ({{ resultadosSector.length }})
              </button>
            </div>

            <div v-if="resultadosSector.length > 0" class="lista-resultados-clara">
              <div
                v-for="pers in resultadosSector"
                :key="pers.idPersonal"
                class="fila-persona-resultado"
              >
                <div>
                  <strong>{{ pers.apellido }}, {{ pers.nombre }}</strong>
                  <span class="res-detalle">DNI {{ pers.dni }} · Menú {{ pers.menuPrincipal }}</span>
                </div>
                <button
                  type="button"
                  class="btn-incluir-chico"
                  :disabled="estaEnRetiro(pers.idPersonal)"
                  @click="agregarPersonaAlRetiro(pers)"
                >
                  {{ estaEnRetiro(pers.idPersonal) ? 'En bandeja' : '+ Agregar' }}
                </button>
              </div>
            </div>
            <div v-else-if="sectorFiltroId && !buscando" class="bandeja-vacia">
              No hay personas con comidas pendientes vigentes en este sector.
            </div>
          </div>
        </section>

        <!-- COLUMNA DERECHA: Bandeja de Retiro -->
        <section class="tarjeta-kiosko" aria-label="Bandeja de retiro en curso">
          <div class="bandeja-encabezado">
            <div>
              <h2>Revisar comidas y confirmar entrega</h2>
              <p class="subtitulo-bandeja">
                Personas incluidas en esta operación: <strong>{{ personasEnRetiro.length }}</strong>
              </p>
            </div>

            <div v-if="personasEnRetiro.length > 0" class="bandeja-acciones-top">
              <span class="chip-inactividad">Reinicia en {{ segundosInactividad }}s</span>
              <button type="button" class="btn-panel-discreto" @click="resetearFlujoKiosko">
                Vaciar bandeja
              </button>
            </div>
          </div>

          <div v-if="personasEnRetiro.length === 0" class="bandeja-vacia">
            <strong>No hay personas cargadas en el retiro actual</strong>
            <p>Usá el buscador de la izquierda para agregar comensales y revisar sus viandas.</p>
          </div>

          <div v-else class="lista-comensales-retiro">
            <FichaComensalRetiro
              v-for="persona in personasEnRetiro"
              :key="persona.idPersonal"
              :persona="persona"
              :comidas-config="COMIDAS_CONFIG"
              :comida-en-curso-id="comidaEnCursoId"
              :minutos-actuales="minutosActuales"
              :seleccionadas-ids="solicitudesSeleccionadasIds"
              @quitar="quitarPersona"
              @toggle-comida="toggleSeleccionComida"
            />
          </div>

          <div class="bandeja-pie-confirmacion">
            <div class="resumen-previo-pie">
              <span>Seleccionadas para entregar:</span>
              <strong>{{ solicitudesSeleccionadasIds.length }} vianda(s)</strong>
            </div>

            <button
              type="button"
              :class="[
                'btn-confirmar-entrega-kiosko',
                solicitudesSeleccionadasIds.length > 0 ? 'activo' : 'deshabilitado',
              ]"
              :disabled="solicitudesSeleccionadasIds.length === 0 || enviandoEntrega"
              @click="modalConfirmacionAbierto = true"
            >
              {{
                solicitudesSeleccionadasIds.length === 0
                  ? 'Seleccioná al menos una comida autorizada pendiente'
                  : `Revisar y Confirmar Entrega (${solicitudesSeleccionadasIds.length})`
              }}
            </button>
          </div>
        </section>
      </div>
    </div>

    <ModalConfirmarEntrega
      v-if="modalConfirmacionAbierto"
      :personas="personasEnRetiro"
      :items="itemsResumenConfirmacion"
      :enviando="enviandoEntrega"
      :resultado-incierto="entregaResultadoIncierto"
      @cerrar="modalConfirmacionAbierto = false"
      @confirmar="confirmarEntregaDefinitiva"
    />

    <ModalResumenTurno
      v-if="menuDiscretoAbierto"
      ref="resumenTurnoRef"
      :fecha-hoy-iso="fechaHoyIso"
      :fecha-texto="fechaActualTexto"
      :comida-actual="comidaEnCursoObj"
      :comidas-config="COMIDAS_CONFIG"
      :minutos-actuales="minutosActuales"
      @cerrar="menuDiscretoAbierto = false"
      @logout="ejecutarCierreSesion"
    />
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import FichaComensalRetiro from '../components/FichaComensalRetiro.vue'
import ModalConfirmarEntrega from '../components/ModalConfirmarEntrega.vue'
import ModalResumenTurno from '../components/ModalResumenTurno.vue'
import TecladoDniKiosko from '../components/TecladoDniKiosko.vue'
import { normalizeApiError } from '@/services/api/error-handler'
import {
  buscarComidasAutorizadas,
  cerrarSesionApi,
  listarSectoresActivos,
  registrarEntrega,
} from '../services/entregas'

const router = useRouter()

const NOMBRES_MENUS = { 1: 'General', 2: 'Vegetariano', 3: 'Celíaco' }
const COMIDAS_CONFIG = ref([
  { id: 1, nombre: 'Desayuno', rango: '07:00 a 09:30', inicioMin: 420, finMin: 570 },
  { id: 2, nombre: 'Almuerzo', rango: '11:30 a 14:30', inicioMin: 690, finMin: 870 },
  { id: 3, nombre: 'Merienda', rango: '16:00 a 17:30', inicioMin: 960, finMin: 1050 },
  { id: 4, nombre: 'Cena', rango: '19:30 a 22:00', inicioMin: 1170, finMin: 1320 },
])

const SEGUNDOS_LIMITE_INACTIVIDAD = 60

function calcularComidaPorHora() {
  const ahora = new Date()
  const min = ahora.getHours() * 60 + ahora.getMinutes()
  for (const c of COMIDAS_CONFIG.value) {
    if (min >= c.inicioMin && min <= c.finMin) return c.id
  }
  if (min < 690) return 1
  if (min < 960) return 2
  if (min < 1170) return 3
  return 4
}

const hoy = new Date()
const fechaHoyIso = ref(
  `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}-${String(hoy.getDate()).padStart(2, '0')}`
)
const relojActual = ref(new Date())
const comidaEnCursoId = ref(calcularComidaPorHora())
const comidaForzadaManual = ref(false)

const modoBusqueda = ref('dni')
const dniInput = ref('')
const nyaInput = ref('')
const sectorFiltroId = ref('')
const buscando = ref(false)
const busquedaSinResultados = ref(false)
const resultadosNombre = ref([])
const resultadosSector = ref([])
const sectoresApi = ref([])
const sectoresCache = ref({})

const personasEnRetiro = ref([])
const solicitudesSeleccionadasIds = ref([])
const modalConfirmacionAbierto = ref(false)
const menuDiscretoAbierto = ref(false)
const enviandoEntrega = ref(false)
const entregaResultadoIncierto = ref(false)
const alerta = ref({ tipo: '', texto: '' })
const resumenTurnoRef = ref(null)
const reintentoConsulta = ref(null)
const segundosInactividad = ref(SEGUNDOS_LIMITE_INACTIVIDAD)

function esReintentableSinAfectarMantenimiento(error) {
  const status = error?.response?.status ?? error?.status
  return !error?.response || status === 500
}

let timerReloj = null
let timerPostConfirmacion = null

const minutosActuales = computed(
  () => relojActual.value.getHours() * 60 + relojActual.value.getMinutes()
)

const comidaEnCursoObj = computed(
  () => COMIDAS_CONFIG.value.find((c) => c.id === comidaEnCursoId.value) || COMIDAS_CONFIG.value[0]
)

const fechaActualTexto = computed(() => {
  const f = relojActual.value
  return `${String(f.getDate()).padStart(2, '0')}/${String(f.getMonth() + 1).padStart(2, '0')}/${f.getFullYear()}`
})

const horaActualTexto = computed(() =>
  relojActual.value.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', hour12: false })
)

const sectoresOpciones = computed(() => {
  if (sectoresApi.value.length > 0) return sectoresApi.value
  return Object.entries(sectoresCache.value)
    .map(([id, nombre]) => ({ id: Number(id), nombre }))
    .sort((a, b) => a.nombre.localeCompare(b.nombre))
})

const itemsResumenConfirmacion = computed(() => {
  const setIds = new Set(solicitudesSeleccionadasIds.value)
  const items = []
  for (const p of personasEnRetiro.value) {
    for (const c of COMIDAS_CONFIG.value) {
      const sol = p.comidas[c.id]
      if (sol && setIds.has(sol.idSolicitud)) {
        items.push({
          idSolicitud: sol.idSolicitud,
          nombre: p.nombre,
          apellido: p.apellido,
          dni: p.dni,
          sector: p.sector,
          comida: c.nombre,
          menu: sol.menu || p.menuPrincipal,
        })
      }
    }
  }
  return items
})

function esTurnoComidaVencido(idComida) {
  const cfg = COMIDAS_CONFIG.value.find((c) => c.id === Number(idComida))
  if (!cfg) return false
  return minutosActuales.value > cfg.finMin && cfg.id < comidaEnCursoId.value
}

function limpiarSeleccionadasVencidas() {
  const idsValidos = new Set()
  for (const p of personasEnRetiro.value) {
    for (const c of COMIDAS_CONFIG.value) {
      const sol = p.comidas[c.id]
      if (sol && !sol.entregada && !esTurnoComidaVencido(c.id)) {
        idsValidos.add(sol.idSolicitud)
      }
    }
  }
  solicitudesSeleccionadasIds.value = solicitudesSeleccionadasIds.value.filter((id) =>
    idsValidos.has(id)
  )
}

function seleccionarComidaManual(idComida) {
  comidaEnCursoId.value = idComida
  comidaForzadaManual.value = true
  limpiarSeleccionadasVencidas()
}

function cambiarModoBusqueda(modo) {
  modoBusqueda.value = modo
  busquedaSinResultados.value = false
  resultadosNombre.value = []
}

function consolidarPersonas(filas) {
  const mapa = new Map()
  const nuevosSectores = { ...sectoresCache.value }
  for (const fila of filas) {
    if (!fila.idPersonal) continue
    if (fila.idSector && fila.sector) nuevosSectores[Number(fila.idSector)] = fila.sector
    if (!mapa.has(fila.idPersonal)) {
      mapa.set(fila.idPersonal, {
        idPersonal: fila.idPersonal,
        dni: String(fila.dni || ''),
        nombre: fila.nombre || '',
        apellido: fila.apellido || '',
        sector: fila.sector || `Sector #${fila.idSector}`,
        menuPrincipal: fila.menu || NOMBRES_MENUS[fila.idTipoMenu] || 'General',
        comidas: { 1: null, 2: null, 3: null, 4: null },
      })
    }
    const idComida = Number(fila.idTipoComida)
    if (idComida >= 1 && idComida <= 4) {
      mapa.get(fila.idPersonal).comidas[idComida] = {
        idSolicitud: fila.idSolicitud,
        menu: fila.menu || NOMBRES_MENUS[fila.idTipoMenu] || 'General',
        entregada: Boolean(fila.entregada),
        hora_entrega: fila.hora_entrega || null,
      }
    }
  }
  sectoresCache.value = nuevosSectores
  return Array.from(mapa.values())
}

function estaEnRetiro(idPersonal) {
  return personasEnRetiro.value.some((p) => Number(p.idPersonal) === Number(idPersonal))
}

function agregarPersonaAlRetiro(persona) {
  const idx = personasEnRetiro.value.findIndex(
    (p) => Number(p.idPersonal) === Number(persona.idPersonal)
  )
  if (idx >= 0) personasEnRetiro.value[idx] = persona
  else personasEnRetiro.value.push(persona)

  const solCurso = persona.comidas[comidaEnCursoId.value]
  if (
    solCurso &&
    !solCurso.entregada &&
    !esTurnoComidaVencido(comidaEnCursoId.value) &&
    !solicitudesSeleccionadasIds.value.includes(solCurso.idSolicitud)
  ) {
    solicitudesSeleccionadasIds.value.push(solCurso.idSolicitud)
  }
}

async function buscarPorDni() {
  buscando.value = true
  alerta.value = { tipo: '', texto: '' }
  const params = { fecha: fechaHoyIso.value, dni: dniInput.value }
  try {
    const data = await buscarComidasAutorizadas(params)
    const personas = consolidarPersonas(Array.isArray(data) ? data : [])
    const encontrada = personas.find((p) => p.dni === dniInput.value) || personas[0]
    if (!encontrada) {
      alerta.value = {
        tipo: 'advertencia',
        texto: `No se encontraron comidas autorizadas para hoy con el DNI ${dniInput.value}.`,
      }
      return
    }
    agregarPersonaAlRetiro(encontrada)
    dniInput.value = ''
  } catch (err) {
    const apiError = normalizeApiError(err)
    reintentoConsulta.value = esReintentableSinAfectarMantenimiento(err) ? () => repetirBusquedaDni(params) : null
    alerta.value = { tipo: 'error', texto: apiError.message }
  } finally {
    buscando.value = false
  }
}

async function buscarPorNombre() {
  buscando.value = true
  busquedaSinResultados.value = false
  const params = { fecha: fechaHoyIso.value, nya: nyaInput.value.trim() }
  try {
    const data = await buscarComidasAutorizadas(params)
    resultadosNombre.value = consolidarPersonas(Array.isArray(data) ? data : [])
    busquedaSinResultados.value = resultadosNombre.value.length === 0
  } catch (err) {
    const apiError = normalizeApiError(err)
    reintentoConsulta.value = esReintentableSinAfectarMantenimiento(err) ? () => repetirBusquedaNombre(params) : null
    alerta.value = { tipo: 'error', texto: apiError.message }
  } finally {
    buscando.value = false
  }
}

async function buscarPorSector() {
  if (!sectorFiltroId.value) {
    resultadosSector.value = []
    return
  }
  buscando.value = true
  const params = { fecha: fechaHoyIso.value, sector: sectorFiltroId.value }
  try {
    const data = await buscarComidasAutorizadas(params)
    resultadosSector.value = consolidarPersonas(Array.isArray(data) ? data : []).filter((p) =>
      Object.entries(p.comidas).some(
        ([idComida, c]) => c && !c.entregada && !esTurnoComidaVencido(Number(idComida))
      )
    )
  } catch (err) {
    const apiError = normalizeApiError(err)
    reintentoConsulta.value = esReintentableSinAfectarMantenimiento(err) ? () => repetirBusquedaSector(params) : null
    alerta.value = { tipo: 'error', texto: apiError.message }
  } finally {
    buscando.value = false
  }
}

async function reintentarConsulta() {
  if (buscando.value || typeof reintentoConsulta.value !== 'function') return
  await reintentoConsulta.value()
}

async function repetirBusquedaDni(params) {
  buscando.value = true
  try {
    const data = await buscarComidasAutorizadas(params)
    const personas = consolidarPersonas(Array.isArray(data) ? data : [])
    const encontrada = personas.find((p) => p.dni === params.dni) || personas[0]
    if (encontrada) agregarPersonaAlRetiro(encontrada)
    reintentoConsulta.value = null
    alerta.value = { tipo: encontrada ? '' : 'advertencia', texto: encontrada ? '' : `No se encontraron comidas autorizadas para hoy con el DNI ${params.dni}.` }
  } catch (err) {
    const apiError = normalizeApiError(err)
    alerta.value = { tipo: 'error', texto: apiError.message }
    reintentoConsulta.value = esReintentableSinAfectarMantenimiento(err) ? () => repetirBusquedaDni(params) : null
  } finally { buscando.value = false }
}

async function repetirBusquedaNombre(params) {
  buscando.value = true
  try {
    const data = await buscarComidasAutorizadas(params)
    resultadosNombre.value = consolidarPersonas(Array.isArray(data) ? data : [])
    busquedaSinResultados.value = resultadosNombre.value.length === 0
    reintentoConsulta.value = null
    alerta.value = { tipo: '', texto: '' }
  } catch (err) {
    const apiError = normalizeApiError(err)
    alerta.value = { tipo: 'error', texto: apiError.message }
    reintentoConsulta.value = esReintentableSinAfectarMantenimiento(err) ? () => repetirBusquedaNombre(params) : null
  } finally { buscando.value = false }
}

async function repetirBusquedaSector(params) {
  buscando.value = true
  try {
    const data = await buscarComidasAutorizadas(params)
    resultadosSector.value = consolidarPersonas(Array.isArray(data) ? data : []).filter((p) =>
      Object.entries(p.comidas).some(([idComida, c]) => c && !c.entregada && !esTurnoComidaVencido(Number(idComida)))
    )
    reintentoConsulta.value = null
    alerta.value = { tipo: '', texto: '' }
  } catch (err) {
    const apiError = normalizeApiError(err)
    alerta.value = { tipo: 'error', texto: apiError.message }
    reintentoConsulta.value = esReintentableSinAfectarMantenimiento(err) ? () => repetirBusquedaSector(params) : null
  } finally { buscando.value = false }
}

function quitarPersona(idPersonal) {
  const p = personasEnRetiro.value.find((x) => Number(x.idPersonal) === Number(idPersonal))
  if (p) {
    const ids = Object.values(p.comidas).filter(Boolean).map((c) => c.idSolicitud)
    solicitudesSeleccionadasIds.value = solicitudesSeleccionadasIds.value.filter((id) => !ids.includes(id))
  }
  personasEnRetiro.value = personasEnRetiro.value.filter((x) => Number(x.idPersonal) !== Number(idPersonal))
}

function toggleSeleccionComida(persona, idComida) {
  const c = persona.comidas[idComida]
  if (!c || c.entregada || esTurnoComidaVencido(idComida)) return
  const pos = solicitudesSeleccionadasIds.value.indexOf(c.idSolicitud)
  if (pos >= 0) solicitudesSeleccionadasIds.value.splice(pos, 1)
  else solicitudesSeleccionadasIds.value.push(c.idSolicitud)
}

async function confirmarEntregaDefinitiva(datosResponsable) {
  if (enviandoEntrega.value || entregaResultadoIncierto.value) return
  enviandoEntrega.value = true
  alerta.value = { tipo: '', texto: '' }
  const payload = {
    ids_solicitudes: [...solicitudesSeleccionadasIds.value],
    ...datosResponsable,
  }
  try {
    await registrarEntrega(payload)
    modalConfirmacionAbierto.value = false
    alerta.value = {
      tipo: 'exito',
      texto: `✓ Entrega registrada con éxito (${payload.ids_solicitudes.length} vianda/s). Reiniciando pantalla...`,
    }
    if (timerPostConfirmacion) clearTimeout(timerPostConfirmacion)
    timerPostConfirmacion = setTimeout(() => {
      resetearFlujoKiosko()
      alerta.value = { tipo: '', texto: '' }
    }, 3000)
  } catch (err) {
    const apiError = normalizeApiError(err)
    const esConflicto = apiError.isConflict
    alerta.value = { tipo: esConflicto ? 'advertencia' : 'error', texto: apiError.message }
    if (!esConflicto && (!err?.response || (err?.response?.status ?? err?.status) === 500)) {
      entregaResultadoIncierto.value = true
      alerta.value.texto += ' No vuelvas a enviar hasta comprobar el estado de estas solicitudes.'
    }
    if (esConflicto) {
      try {
        const actualizadas = await buscarComidasAutorizadas({ fecha: fechaHoyIso.value })
        const porPersona = new Map(consolidarPersonas(Array.isArray(actualizadas) ? actualizadas : []).map((p) => [Number(p.idPersonal), p]))
        personasEnRetiro.value = personasEnRetiro.value.map((p) => porPersona.get(Number(p.idPersonal)) || p)
        if (menuDiscretoAbierto.value) await resumenTurnoRef.value?.recargarDatosAfectados()
      } catch (refreshError) {
        const refreshApiError = normalizeApiError(refreshError)
        alerta.value.texto = `${apiError.message} Además, no se pudieron actualizar los datos: ${refreshApiError.message}`
      }
      // POST /deliveries no ofrece reintento automático/manual hasta contar con idempotencia backend.
    }
  } finally {
    enviandoEntrega.value = false
  }
}

function resetearFlujoKiosko() {
  personasEnRetiro.value = []
  solicitudesSeleccionadasIds.value = []
  dniInput.value = ''
  nyaInput.value = ''
  resultadosNombre.value = []
  resultadosSector.value = []
  sectorFiltroId.value = ''
  modalConfirmacionAbierto.value = false
  menuDiscretoAbierto.value = false
  modoBusqueda.value = 'dni'
  segundosInactividad.value = SEGUNDOS_LIMITE_INACTIVIDAD
}

async function ejecutarCierreSesion() {
  await cerrarSesionApi()
  localStorage.clear()
  sessionStorage.clear()
  router.push('/login')
}

onMounted(async () => {
  try {
    const sec = await listarSectoresActivos()
    if (Array.isArray(sec)) sectoresApi.value = sec
  } catch {
    sectoresApi.value = []
  }
  try {
    const comidasHoy = await buscarComidasAutorizadas({ fecha: fechaHoyIso.value })
    if (Array.isArray(comidasHoy)) consolidarPersonas(comidasHoy)
  } catch {
    // Sin comidas hoy
  }

  timerReloj = setInterval(() => {
    relojActual.value = new Date()
    if (!comidaForzadaManual.value) comidaEnCursoId.value = calcularComidaPorHora()
    limpiarSeleccionadasVencidas()
    const hayActividadEnPantalla =
      personasEnRetiro.value.length > 0 ||
      modalConfirmacionAbierto.value ||
      menuDiscretoAbierto.value

    if (hayActividadEnPantalla && !enviandoEntrega.value) {
      segundosInactividad.value -= 1
      if (segundosInactividad.value <= 0) {
        resetearFlujoKiosko()
        alerta.value = { tipo: 'advertencia', texto: 'Operación reiniciada por inactividad (60 s).' }
      }
    }
  }, 1000)

})

onBeforeUnmount(() => {
  if (timerReloj) clearInterval(timerReloj)
  if (timerPostConfirmacion) clearTimeout(timerPostConfirmacion)
})
</script>

<style scoped>
.kiosko-claro-viewport {
  min-height: calc(100vh - 64px);
  background: #f8fafc;
  color: #0f172a;
  padding: 1.15rem 1.5rem;
  box-sizing: border-box;
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  user-select: none;
}

.kiosko-contenedor {
  max-width: 1380px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: calc(100vh - 96px);
}

.kiosko-encabezado,
.tarjeta-kiosko {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 1rem 1.25rem;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}

.kiosko-encabezado {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.badge-turno-activo {
  font-size: 0.76rem;
  font-weight: 700;
  color: #0f766e;
  letter-spacing: 0.05em;
}

.titulo-y-reloj {
  display: flex;
  align-items: baseline;
  gap: 0.85rem;
}

.titulo-y-reloj h1 {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 800;
}

.reloj-kiosko {
  font-size: 0.95rem;
  font-weight: 600;
  color: #64748b;
}

.encabezado-controles {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.selector-turno-segmentado,
.selector-modo-busqueda {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.3rem;
  background: #f1f5f9;
  padding: 0.3rem;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
}

.selector-turno-segmentado {
  display: inline-flex;
}

.btn-segmento,
.btn-modo-busq {
  min-height: 48px;
  padding: 0.4rem 0.9rem;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #334155;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-segmento.activo,
.btn-modo-busq.activo {
  background: #0f766e;
  color: #ffffff;
}

.btn-panel-discreto,
.btn-cerrar-alerta {
  min-height: 48px;
  padding: 0.45rem 0.95rem;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #0f172a;
  font-weight: 700;
  cursor: pointer;
}

.alerta-kiosko {
  padding: 0.85rem 1.15rem;
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 700;
}

.alerta-exito { background: #dcfce7; border: 1px solid #86efac; color: #166534; }
.alerta-advertencia { background: #fef3c7; border: 1px solid #fcd34d; color: #92400e; }
.alerta-error { background: #fee2e2; border: 1px solid #fca5a5; color: #991b1b; }

.kiosko-layout-grid {
  display: grid;
  grid-template-columns: minmax(350px, 430px) 1fr;
  gap: 1.25rem;
  flex: 1;
}

.tarjeta-kiosko {
  display: flex;
  flex-direction: column;
  gap: 0.95rem;
}

.buscador-header,
.bloque-alternativo,
.lista-comensales-retiro {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.buscador-header h2,
.bandeja-encabezado h2 {
  margin: 0;
  font-size: 1.12rem;
}

.label-estandar {
  font-size: 0.82rem;
  font-weight: 700;
  color: #334155;
}

.barra-input-boton {
  display: flex;
  gap: 0.5rem;
}

.input-claro-tactil {
  flex: 1;
  min-height: 48px;
  padding: 0.45rem 0.8rem;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  font-size: 0.95rem;
}

.btn-primario-tactil,
.btn-incluir-chico {
  min-height: 48px;
  padding: 0.45rem 1rem;
  border-radius: 10px;
  border: 1px solid #0f766e;
  background: #0f766e;
  color: #ffffff;
  font-weight: 700;
  cursor: pointer;
}

.lista-resultados-clara {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 360px;
  overflow-y: auto;
}

.fila-persona-resultado {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.7rem 0.9rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.res-detalle {
  display: block;
  font-size: 0.82rem;
  color: #64748b;
}

.bandeja-encabezado {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid #f1f5f9;
}

.subtitulo-bandeja {
  margin: 0.2rem 0 0;
  font-size: 0.88rem;
  color: #475569;
}

.bandeja-acciones-top {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.chip-inactividad {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
}

.bandeja-vacia {
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  padding: 2.5rem 1.5rem;
  text-align: center;
  color: #475569;
}

.bandeja-pie-confirmacion {
  margin-top: auto;
  padding-top: 0.85rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.85rem;
}

.resumen-previo-pie strong {
  display: block;
  font-size: 1.15rem;
  color: #0f766e;
}

.btn-confirmar-entrega-kiosko {
  flex: 1;
  min-height: 58px;
  border-radius: 12px;
  font-size: 1.05rem;
  font-weight: 800;
  border: 1px solid #cbd5e1;
  cursor: pointer;
}

.btn-confirmar-entrega-kiosko.activo {
  background: #0f766e;
  border-color: #0f766e;
  color: #ffffff;
}

.btn-confirmar-entrega-kiosko.deshabilitado {
  background: #f1f5f9;
  color: #64748b;
  cursor: not-allowed;
}

@media (max-width: 1024px) {
  .kiosko-layout-grid {
    grid-template-columns: 1fr;
  }
}
</style>
