<script setup>
/**
 * PedidosSectorView
 * Jefe de Servicio: consulta, detalle, edición y eliminación de los pedidos de su sector.
 *
 * Reglas de negocio aplicadas en la interfaz (el backend siempre tiene la última palabra):
 *  - El sector lo determina la API según el usuario autenticado (no hay selector de sector).
 *  - Solo se modifica o elimina un pedido en estado "confirmado", de hoy o de una fecha futura,
 *    y antes del horario de corte (hora límite del día anterior a la fecha del pedido).
 *  - Lo pedido y lo autorizado se muestran siempre por separado; lo autorizado es solo lectura.
 *  - La condición Regular / Excepción definitiva la calcula el backend; en edición se estima.
 */
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

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

/* ------------------------------------------------------------------ */
/* Catálogos fijos                                                     */
/* ------------------------------------------------------------------ */
const COMIDAS = [
  { idTipoComida: 1, label: 'Desayuno', inicial: 'D' },
  { idTipoComida: 2, label: 'Almuerzo', inicial: 'A' },
  { idTipoComida: 3, label: 'Merienda', inicial: 'M' },
  { idTipoComida: 4, label: 'Cena', inicial: 'C' },
]

const MENUS = [
  { idTipoMenu: 1, label: 'General' },
  { idTipoMenu: 2, label: 'Vegetariano' },
  { idTipoMenu: 3, label: 'Celíaco' },
]

const ESTADOS_FILTRO = [
  { value: '', label: 'Todos' },
  { value: 'confirmado', label: 'Confirmado' },
  { value: 'autorizado', label: 'Autorizado' },
  { value: 'rechazado', label: 'Rechazado' },
]

const ESTADOS_INFO = {
  confirmado: { texto: 'Confirmado', icono: '◷' },
  autorizado: { texto: 'Autorizado', icono: '✓' },
  rechazado: { texto: 'Rechazado', icono: '✕' },
}

/* ------------------------------------------------------------------ */
/* Utilidades de texto y fechas (siempre dd/mm/aaaa en pantalla)       */
/* ------------------------------------------------------------------ */
const pad = (n) => String(n).padStart(2, '0')

function normalizarTexto(valor) {
  return String(valor ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}

function isoADate(iso) {
  const [a, m, d] = String(iso).slice(0, 10).split('-').map(Number)
  return new Date(a, (m || 1) - 1, d || 1)
}

function dateAIso(fecha) {
  return `${fecha.getFullYear()}-${pad(fecha.getMonth() + 1)}-${pad(fecha.getDate())}`
}

function hoyLocalIso() {
  return dateAIso(new Date())
}

function formatearFecha(iso) {
  if (!iso) return '—'
  const partes = String(iso).slice(0, 10).split('-')
  return partes.length === 3 ? `${partes[2]}/${partes[1]}/${partes[0]}` : String(iso)
}

function formatearFechaHora(fecha) {
  return `${pad(fecha.getDate())}/${pad(fecha.getMonth() + 1)}/${fecha.getFullYear()} ${pad(
    fecha.getHours(),
  )}:${pad(fecha.getMinutes())}`
}

function diaSemana(iso) {
  if (!iso) return ''
  return isoADate(iso).toLocaleDateString('es-AR', { weekday: 'long' })
}

function esIsoValido(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso ?? '').trim())
  if (!m) return false
  const [, a, mes, d] = m
  const f = new Date(Number(a), Number(mes) - 1, Number(d))
  return f.getFullYear() === Number(a) && f.getMonth() === Number(mes) - 1 && f.getDate() === Number(d)
}

/* ------------------------------------------------------------------ */
/* Estado general                                                      */
/* ------------------------------------------------------------------ */
const horarioCorte = ref(null)
const ahora = ref(new Date())
let temporizadorReloj = null

const filtros = reactive({ desde: '', hasta: '', estado: '', comida: '', menu: '', consulta: '' })
const filtrosAplicados = ref({ desde: '', hasta: '', estado: '', comida: '', menu: '', consulta: '' })
const errorDesde = ref('')
const errorHasta = ref('')

const page = ref(1)
const perPage = ref(10)
const totalItems = ref(0)

const pedidosLista = ref([])
const cargandoLista = ref(false)
const accionEnCurso = ref(false)
const apiErrorMessage = ref(null)
const retryOperation = ref(null)
const mensajeExito = ref('')

const catalogoPersonas = ref(new Map())
const personalSectorDisponibles = ref([])
const residentesDisponibles = ref([])
const cuposPorComida = ref({ 1: 0, 2: 0, 3: 0, 4: 0 })
const cuposCargados = ref(false)

const pedidoSeleccionado = ref(null)
const modoEdicion = ref(false)
const filasEdicion = ref([])
const firmaOriginal = ref('')
const personaSectorSeleccionadaId = ref('')
const busquedaResidente = ref('')
const errorEdicion = ref('')

const pedidoAEliminar = ref(null)
const dialogEliminar = ref(null)
const tituloDetalle = ref(null)

let seqUid = 1
let seqOrden = 1_000_000_000

/* ------------------------------------------------------------------ */
/* Datos derivados del usuario y de la configuración                   */
/* ------------------------------------------------------------------ */
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

function obtenerSectorIdUsuario() {
  const usuario = authStore.user ?? {}
  return usuario.idSector ?? usuario.id_sector ?? usuario.sector?.idSector ?? usuario.sector?.id ?? null
}

const textoCorte = computed(() =>
  horarioCorte.value
    ? `${horarioCorte.value} hs del día anterior a la fecha de cada pedido`
    : '18:00 hs del día anterior (por defecto)',
)

const totalPaginas = computed(() =>
  perPage.value ? Math.max(1, Math.ceil(totalItems.value / perPage.value)) : 1,
)

const rangoMostrado = computed(() => {
  if (totalItems.value === 0) return ''
  const desde = (page.value - 1) * perPage.value + 1
  const hasta = Math.min(page.value * perPage.value, totalItems.value)
  return `Mostrando ${desde}–${hasta} de ${totalItems.value}`
})

const hayFiltrosActivos = computed(() =>
  Object.values(filtrosAplicados.value).some((valor) => String(valor).trim() !== ''),
)

/* ------------------------------------------------------------------ */
/* Reglas de edición: estado, fecha y horario de corte                 */
/* ------------------------------------------------------------------ */
const fechaDePedido = (pedido) => pedido?.fecha_desde ?? pedido?.fecha ?? ''

function fechaLimiteCorte(fechaIso) {
  const m = /^(\d{1,2}):(\d{2})/.exec(horarioCorte.value ?? '18:00')
  if (!m || !fechaIso) return null
  const limite = isoADate(fechaIso)
  limite.setDate(limite.getDate() - 1)
  limite.setHours(Number(m[1]), Number(m[2]), 0, 0)
  return limite
}

function motivoBloqueo(pedido) {
  if (!pedido) return 'No hay un pedido seleccionado.'
  const estado = String(pedido.estado ?? '').toLowerCase()
  if (estado === 'autorizado') return 'Ya fue autorizado.'
  if (estado === 'rechazado') return 'Fue rechazado.'
  const fecha = fechaDePedido(pedido)
  if (fecha && fecha < hoyLocalIso()) return 'Fecha pasada.'
  const limite = fechaLimiteCorte(fecha)
  if (limite && ahora.value >= limite) return 'Horario de corte vencido.'
  return ''
}

const puedeModificar = (pedido) => motivoBloqueo(pedido) === ''

function textoLimiteEdicion(pedido) {
  const limite = fechaLimiteCorte(fechaDePedido(pedido))
  return limite ? formatearFechaHora(limite) : 'el horario de corte configurado'
}

function etiquetaPeriodicidad(pedido) {
  const informada = String(pedido?.periodicidad ?? '').trim()
  if (informada) return informada.charAt(0).toUpperCase() + informada.slice(1).toLowerCase()
  const desde = fechaDePedido(pedido)
  const hasta = pedido?.fecha_hasta
  if (desde && hasta && hasta !== desde) {
    const dias = Math.round((isoADate(hasta) - isoADate(desde)) / 86_400_000) + 1
    return dias >= 28 ? 'Mensual' : dias >= 7 ? 'Semanal' : 'Diaria'
  }
  return 'Diaria'
}

const infoEstado = (estado) =>
  ESTADOS_INFO[String(estado ?? '').toLowerCase()] ?? { texto: String(estado ?? '—'), icono: '•' }

/* ------------------------------------------------------------------ */
/* Totales por comida y tipo de menú                                    */
/* ------------------------------------------------------------------ */
function construirMatriz(aportes) {
  const celdas = {}
  const porMenu = {}
  for (const m of MENUS) {
    celdas[m.idTipoMenu] = { 1: 0, 2: 0, 3: 0, 4: 0 }
    porMenu[m.idTipoMenu] = 0
  }
  const porComida = { 1: 0, 2: 0, 3: 0, 4: 0 }
  let total = 0
  for (const { idComida, idMenu, cantidad } of aportes) {
    if (!celdas[idMenu] || porComida[idComida] === undefined) continue
    celdas[idMenu][idComida] += cantidad
    porComida[idComida] += cantidad
    porMenu[idMenu] += cantidad
    total += cantidad
  }
  return { celdas, porComida, porMenu, total }
}

function aportesDesdeMapa(mapa) {
  return Object.entries(mapa || {}).flatMap(([clave, valor]) => {
    const m = /^comida_(\d+)_menu_(\d+)$/.exec(clave)
    return m ? [{ idComida: Number(m[1]), idMenu: Number(m[2]), cantidad: Number(valor) || 0 }] : []
  })
}

function matrizDesdeFilas(filas) {
  const aportes = []
  for (const fila of filas) {
    for (const c of COMIDAS) {
      if (fila.comidas[c.idTipoComida]) {
        aportes.push({ idComida: c.idTipoComida, idMenu: fila.idTipoMenu, cantidad: 1 })
      }
    }
  }
  return construirMatriz(aportes)
}

const pedidosFiltradosCliente = computed(() => {
  const q = normalizarTexto(filtrosAplicados.value.consulta.trim())
  if (!q) return pedidosLista.value
  return pedidosLista.value.filter((p) => {
    const textoPedido = [
      `#${p.idPedido}`,
      String(p.idPedido),
      formatearFecha(fechaDePedido(p)),
      diaSemana(fechaDePedido(p)),
      etiquetaPeriodicidad(p),
      String(p.estado ?? ''),
    ].join(' ')
    return normalizarTexto(textoPedido).includes(q)
  })
})

const resumenesLista = computed(
  () =>
    new Map(
      pedidosFiltradosCliente.value.map((p) => [
        p.idPedido,
        {
          pedido: construirMatriz(aportesDesdeMapa(p.cantidades_pedidas)),
          autorizado: p.cantidades_autorizadas
            ? construirMatriz(aportesDesdeMapa(p.cantidades_autorizadas))
            : null,
        },
      ]),
    ),
)

/* ------------------------------------------------------------------ */
/* Personas y solicitudes                                              */
/* ------------------------------------------------------------------ */
const labelMenu = (idMenu) =>
  MENUS.find((m) => m.idTipoMenu === Number(idMenu))?.label ?? `Menú #${idMenu}`

function resolverMenu(persona) {
  const objeto = persona.tipoMenu ?? persona.tipo_menu
  const nombre = typeof objeto === 'string' ? objeto : objeto?.nombre
  const id = objeto?.idTipoMenu ?? objeto?.id ?? persona.idTipoMenu ?? persona.id_tipo_menu
  return (
    MENUS.find((m) => m.idTipoMenu === Number(id)) ??
    MENUS.find((m) => normalizarTexto(m.label) === normalizarTexto(nombre)) ??
    MENUS[0]
  )
}

function mapearPersonaBase(persona, esResidente = false) {
  const apellido = persona.apellido ?? ''
  const nombre = persona.nombre ?? ''
  const menu = resolverMenu(persona)
  return {
    idPersonal: Number(persona.idPersonal ?? persona.id),
    nombre:
      apellido && nombre
        ? `${apellido}, ${nombre}`
        : persona.nombreCompleto || nombre || `Persona #${persona.idPersonal ?? persona.id}`,
    dni: persona.dni ?? '',
    idTipoMenu: menu.idTipoMenu,
    tipoMenu: menu.label,
    esResidente,
  }
}

function datosPersonaDeSolicitud(sol) {
  const idP = Number(sol.idPersonal)
  const embebida = sol.persona ?? null
  const apellido = embebida?.apellido ?? sol.apellido
  const nombre = embebida?.nombre ?? sol.nombre
  const catalogo = catalogoPersonas.value.get(idP)
  return {
    nombre: apellido && nombre ? `${apellido}, ${nombre}` : (catalogo?.nombre ?? `Persona #${idP}`),
    dni: embebida?.dni ?? sol.dni ?? catalogo?.dni ?? '—',
    esResidente: catalogo?.esResidente ?? Boolean(sol.esResidente),
  }
}

function construirFilasDesdeSolicitudes(solicitudes = []) {
  const porPersona = new Map()
  solicitudes.forEach((sol, indice) => {
    const idP = Number(sol.idPersonal)
    if (!porPersona.has(idP)) {
      porPersona.set(idP, {
        uid: seqUid++,
        idPersonal: idP,
        ...datosPersonaDeSolicitud(sol),
        idTipoMenu: Number(sol.idTipoMenu),
        tipoMenu: labelMenu(sol.idTipoMenu),
        comidas: { 1: false, 2: false, 3: false, 4: false },
        orden: { 1: null, 2: null, 3: null, 4: null },
      })
    }
    const fila = porPersona.get(idP)
    const idC = Number(sol.idTipoComida)
    fila.comidas[idC] = true
    fila.orden[idC] = Number(sol.idSolicitud) || indice + 1
  })
  return Array.from(porPersona.values())
}

const solicitudes = computed(() => pedidoSeleccionado.value?.solicitudes ?? [])
const filasDetalle = computed(() => construirFilasDesdeSolicitudes(solicitudes.value))
const solicitudPorCelda = computed(
  () => new Map(solicitudes.value.map((s) => [`${Number(s.idPersonal)}-${Number(s.idTipoComida)}`, s])),
)

const solicitudDe = (fila, idComida) => solicitudPorCelda.value.get(`${fila.idPersonal}-${idComida}`)
const esExcepcion = (sol) => normalizarTexto(sol?.condicionCupo ?? sol?.condicion).startsWith('exc')

function estadoAutorizacion(sol) {
  const valor = normalizarTexto(sol?.estadoAutorizacion)
  if (valor.startsWith('no')) return 'no_autorizada'
  if (valor.startsWith('autoriz')) return 'autorizada'
  return 'pendiente'
}

const ETIQUETAS_AUTORIZACION = {
  autorizada: { texto: 'Autorizada', icono: '✓' },
  no_autorizada: { texto: 'No autorizada', icono: '✕' },
  pendiente: { texto: 'Sin revisar', icono: '◷' },
}

const mostrarAutorizacionPorCelda = computed(
  () => String(pedidoSeleccionado.value?.estado ?? '').toLowerCase() === 'autorizado',
)

/* ------------------------------------------------------------------ */
/* Edición: condición estimada, cupos y cambios sin guardar            */
/* ------------------------------------------------------------------ */
const condicionesEstimadas = computed(() => {
  const resultado = {}
  for (const c of COMIDAS) {
    const cupo = Number(cuposPorComida.value[c.idTipoComida] ?? 0)
    filasEdicion.value
      .filter((f) => f.comidas[c.idTipoComida])
      .sort((a, b) => a.orden[c.idTipoComida] - b.orden[c.idTipoComida])
      .forEach((fila, posicion) => {
        resultado[`${fila.uid}-${c.idTipoComida}`] =
          !cuposCargados.value || posicion < cupo ? 'regular' : 'excepcion'
      })
  }
  return resultado
})

const condicionEdicion = (fila, idComida) => condicionesEstimadas.value[`${fila.uid}-${idComida}`]

const usoDeCupo = computed(() =>
  COMIDAS.map((c) => {
    const cupo = Number(cuposPorComida.value[c.idTipoComida] ?? 0)
    const seleccionadas = filasEdicion.value.filter((f) => f.comidas[c.idTipoComida]).length
    const regulares = Math.min(seleccionadas, cupo)
    return {
      ...c,
      cupo,
      regulares,
      excepciones: Math.max(0, seleccionadas - cupo),
      porcentaje: cupo > 0 ? Math.min(100, Math.round((regulares / cupo) * 100)) : 0,
    }
  }),
)

const desgloseCondicion = computed(() => {
  if (modoEdicion.value) {
    const valores = Object.values(condicionesEstimadas.value)
    const excepciones = valores.filter((v) => v === 'excepcion').length
    return { regulares: valores.length - excepciones, excepciones }
  }
  const excepciones = solicitudes.value.filter(esExcepcion).length
  return { regulares: solicitudes.value.length - excepciones, excepciones }
})

function firmaDe(filas) {
  return filas
    .map((f) => `${f.idPersonal}:${COMIDAS.map((c) => (f.comidas[c.idTipoComida] ? 1 : 0)).join('')}`)
    .sort()
    .join('|')
}

const hayCambios = computed(
  () => modoEdicion.value && firmaDe(filasEdicion.value) !== firmaOriginal.value,
)

const filaSinComidas = (fila) => !COMIDAS.some((c) => fila.comidas[c.idTipoComida])
const totalSolicitudesEdicion = computed(() => matrizDesdeFilas(filasEdicion.value).total)

const tarjetasResumen = computed(() => {
  const pedido = pedidoSeleccionado.value
  if (!pedido) return []
  const estado = String(pedido.estado ?? '').toLowerCase()
  const tarjetas = [
    {
      id: 'pedido',
      titulo: modoEdicion.value ? 'Pedido (en edición)' : 'Cantidades pedidas',
      nota: modoEdicion.value
        ? 'Se actualiza al modificar la selección.'
        : 'Solicitado por el sector.',
      variante: 'pedido',
      matriz: modoEdicion.value
        ? matrizDesdeFilas(filasEdicion.value)
        : construirMatriz(aportesDesdeMapa(pedido.cantidades_pedidas)),
      desglose: desgloseCondicion.value,
    },
  ]
  if (pedido.cantidades_autorizadas) {
    tarjetas.push({
      id: 'autorizado',
      titulo: 'Cantidades autorizadas',
      nota: 'Solo lectura (Servicio de Alimentación).',
      variante: 'autorizado',
      matriz: construirMatriz(aportesDesdeMapa(pedido.cantidades_autorizadas)),
    })
  } else {
    tarjetas.push({
      id: 'autorizado',
      titulo: 'Cantidades autorizadas',
      nota:
        estado === 'rechazado'
          ? 'Pedido rechazado sin cantidades autorizadas.'
          : 'Pendiente de revisión.',
      variante: 'pendiente',
      matriz: null,
    })
  }
  return tarjetas
})

/* ------------------------------------------------------------------ */
/* Búsqueda de personas para agregar                                   */
/* ------------------------------------------------------------------ */
const idsEnPedido = computed(() => new Set(filasEdicion.value.map((f) => f.idPersonal)))

const personalSectorSinAgregar = computed(() =>
  personalSectorDisponibles.value.filter((p) => !idsEnPedido.value.has(p.idPersonal)),
)

const sugerenciasResidentes = computed(() => {
  const consulta = normalizarTexto(busquedaResidente.value.trim())
  if (consulta.length < 2) return []
  return residentesDisponibles.value
    .filter(
      (r) =>
        !idsEnPedido.value.has(r.idPersonal) &&
        (normalizarTexto(r.nombre).includes(consulta) || String(r.dni).includes(consulta)),
    )
    .slice(0, 6)
})

const mensajeBusquedaResidente = computed(() => {
  const consulta = busquedaResidente.value.trim()
  if (consulta.length < 2) return 'Escribí al menos 2 caracteres para buscar.'
  if (sugerenciasResidentes.value.length === 0) {
    return 'No se encontraron residentes activos que coincidan, o ya están en el pedido.'
  }
  return `${sugerenciasResidentes.value.length} resultado(s). Seleccioná uno para agregarlo.`
})

/* ------------------------------------------------------------------ */
/* Carga de datos                                                      */
/* ------------------------------------------------------------------ */
async function cargarCatalogosSector() {
  try {
    const configData = await obtenerConfiguracionPedidos().catch(() => null)
    const corte = configData?.horario_corte ?? configData?.horarioCorte
    if (corte) horarioCorte.value = String(corte).slice(0, 5)

    const { personalSector, cuposSector, residentes } = await obtenerDatosCargaPedido(
      obtenerSectorIdUsuario(),
    )

    const mapa = new Map()
    personalSectorDisponibles.value = personalSector.map((p) => {
      const item = mapearPersonaBase(p, false)
      mapa.set(item.idPersonal, item)
      return item
    })
    residentesDisponibles.value = residentes.map((r) => {
      const item = mapearPersonaBase(r, true)
      if (!mapa.has(item.idPersonal)) mapa.set(item.idPersonal, item)
      return item
    })
    catalogoPersonas.value = mapa

    const mapaCupos = { 1: 0, 2: 0, 3: 0, 4: 0 }
    for (const c of cuposSector) {
      const idC = Number(c.idTipoComida ?? c.id_tipo_comida)
      if (idC) mapaCupos[idC] = Number(c.cantComensales ?? c.cantidad ?? 0)
    }
    cuposPorComida.value = mapaCupos
    cuposCargados.value = true
  } catch {
    // Si falla la carga auxiliar, el listado principal sigue funcionando.
  }
}

async function cargarPedidos(paginaDestino = 1) {
  cargandoLista.value = true
  apiErrorMessage.value = null
  retryOperation.value = null
  page.value = paginaDestino

  const f = filtrosAplicados.value
  const params = { page: paginaDestino }
  if (f.desde) params.fecha_desde = f.desde
  if (f.hasta) params.fecha_hasta = f.hasta
  if (f.estado) params.estado = f.estado
  if (f.comida) params.id_tipo_comida = Number(f.comida)
  if (f.menu) params.id_tipo_menu = Number(f.menu)

  try {
    const data = await listarPedidosSector(params)
    pedidosLista.value = Array.isArray(data.items) ? data.items : []
    totalItems.value = Number(data.total ?? pedidosLista.value.length)
    perPage.value = Number(data.per_page ?? perPage.value)
  } catch (error) {
    const normalizado = normalizeApiError(error)
    apiErrorMessage.value = normalizado
    if (normalizado.canRetry) retryOperation.value = () => cargarPedidos(paginaDestino)
  } finally {
    cargandoLista.value = false
  }
}

onMounted(async () => {
  temporizadorReloj = setInterval(() => {
    ahora.value = new Date()
  }, 30_000)
  await Promise.all([cargarCatalogosSector(), cargarPedidos(1)])
})

onBeforeUnmount(() => clearInterval(temporizadorReloj))

/* ------------------------------------------------------------------ */
/* Filtros                                                             */
/* ------------------------------------------------------------------ */
function descartarSiHayCambios() {
  if (!hayCambios.value) return true
  return window.confirm('Tenés cambios sin guardar en este pedido. ¿Querés descartarlos?')
}

function aplicarFiltros() {
  errorDesde.value = ''
  errorHasta.value = ''

  if (filtros.desde && !esIsoValido(filtros.desde)) {
    errorDesde.value = 'Fecha desde inválida.'
  }
  if (filtros.hasta && !esIsoValido(filtros.hasta)) {
    errorHasta.value = 'Fecha hasta inválida.'
  }
  if (!errorDesde.value && !errorHasta.value && filtros.desde && filtros.hasta && filtros.desde > filtros.hasta) {
    errorHasta.value = 'Hasta no puede ser anterior a desde.'
  }
  if (errorDesde.value || errorHasta.value) return
  if (!descartarSiHayCambios()) return

  mensajeExito.value = ''
  limpiarDetalle()
  filtrosAplicados.value = { ...filtros }
  cargarPedidos(1)
}

function limpiarFiltros() {
  if (!descartarSiHayCambios()) return
  Object.assign(filtros, { desde: '', hasta: '', estado: '', comida: '', menu: '', consulta: '' })
  errorDesde.value = ''
  errorHasta.value = ''
  mensajeExito.value = ''
  limpiarDetalle()
  filtrosAplicados.value = { desde: '', hasta: '', estado: '', comida: '', menu: '', consulta: '' }
  cargarPedidos(1)
}

/* ------------------------------------------------------------------ */
/* Detalle y edición                                                   */
/* ------------------------------------------------------------------ */
function limpiarDetalle() {
  pedidoSeleccionado.value = null
  modoEdicion.value = false
  filasEdicion.value = []
  firmaOriginal.value = ''
  errorEdicion.value = ''
  personaSectorSeleccionadaId.value = ''
  busquedaResidente.value = ''
}

function alCerrarDetalle() {
  if (descartarSiHayCambios()) limpiarDetalle()
}

async function enfocarDetalle() {
  await nextTick()
  tituloDetalle.value?.focus()
  tituloDetalle.value?.scrollIntoView({ block: 'start' })
}

function entrarEnEdicion() {
  filasEdicion.value = construirFilasDesdeSolicitudes(solicitudes.value)
  firmaOriginal.value = firmaDe(filasEdicion.value)
  errorEdicion.value = ''
  modoEdicion.value = true
}

function cancelarEdicion() {
  if (!descartarSiHayCambios()) return
  modoEdicion.value = false
  filasEdicion.value = []
  errorEdicion.value = ''
  busquedaResidente.value = ''
  personaSectorSeleccionadaId.value = ''
  enfocarDetalle()
}

async function abrirPedido(pedido, editar = false) {
  if (accionEnCurso.value) return
  if (pedidoSeleccionado.value?.idPedido !== pedido.idPedido && !descartarSiHayCambios()) return

  accionEnCurso.value = true
  apiErrorMessage.value = null
  mensajeExito.value = ''
  try {
    const detalle = await obtenerPedido(pedido.idPedido)
    limpiarDetalle()
    pedidoSeleccionado.value = detalle
    if (editar && puedeModificar(detalle)) entrarEnEdicion()
    await enfocarDetalle()
  } catch (error) {
    apiErrorMessage.value = normalizeApiError(error)
  } finally {
    accionEnCurso.value = false
  }
}

async function recargarDetalle(idPedido) {
  try {
    pedidoSeleccionado.value = await obtenerPedido(idPedido)
    return pedidoSeleccionado.value
  } catch (error) {
    apiErrorMessage.value = normalizeApiError(error)
    return null
  }
}

function incorporarPersona(base) {
  if (idsEnPedido.value.has(base.idPersonal)) {
    errorEdicion.value = `${base.nombre} ya figura en este pedido.`
    return false
  }
  errorEdicion.value = ''
  filasEdicion.value.push({
    uid: seqUid++,
    idPersonal: base.idPersonal,
    nombre: base.nombre,
    dni: base.dni,
    idTipoMenu: base.idTipoMenu,
    tipoMenu: base.tipoMenu,
    esResidente: base.esResidente,
    comidas: { 1: false, 2: false, 3: false, 4: false },
    orden: { 1: null, 2: null, 3: null, 4: null },
  })
  return true
}

function agregarPersonaSector() {
  const id = Number(personaSectorSeleccionadaId.value)
  const encontrada = personalSectorDisponibles.value.find((p) => p.idPersonal === id)
  if (encontrada && incorporarPersona(encontrada)) personaSectorSeleccionadaId.value = ''
}

function agregarResidente(residente) {
  if (incorporarPersona(residente)) busquedaResidente.value = ''
}

function fijarComida(fila, idComida, activa) {
  fila.comidas[idComida] = activa
  fila.orden[idComida] = activa ? ++seqOrden : null
}

function alternarComida(fila, idComida) {
  errorEdicion.value = ''
  fijarComida(fila, idComida, !fila.comidas[idComida])
}

const columnaCompleta = (idComida) =>
  filasEdicion.value.length > 0 && filasEdicion.value.every((f) => f.comidas[idComida])

function alternarColumna(idComida) {
  errorEdicion.value = ''
  const quitar = columnaCompleta(idComida)
  for (const fila of filasEdicion.value) {
    if (quitar || !fila.comidas[idComida]) fijarComida(fila, idComida, !quitar)
  }
}

const filaCompleta = (fila) => COMIDAS.every((c) => fila.comidas[c.idTipoComida])

function alternarFila(fila) {
  errorEdicion.value = ''
  const quitar = filaCompleta(fila)
  for (const c of COMIDAS) {
    if (quitar || !fila.comidas[c.idTipoComida]) fijarComida(fila, c.idTipoComida, !quitar)
  }
}

function quitarFila(indice) {
  errorEdicion.value = ''
  filasEdicion.value.splice(indice, 1)
}

async function guardarEdicion() {
  if (!pedidoSeleccionado.value || accionEnCurso.value) return
  errorEdicion.value = ''
  apiErrorMessage.value = null
  mensajeExito.value = ''

  const comidas = {}
  for (const c of COMIDAS) {
    const ids = filasEdicion.value
      .filter((f) => f.comidas[c.idTipoComida])
      .sort((a, b) => a.orden[c.idTipoComida] - b.orden[c.idTipoComida])
      .map((f) => f.idPersonal)
    if (ids.length > 0) comidas[c.idTipoComida] = ids
  }

  if (Object.keys(comidas).length === 0) {
    errorEdicion.value =
      'Seleccioná al menos una comida para alguna persona. Si ya no necesitás el pedido, eliminalo.'
    return
  }

  accionEnCurso.value = true
  const idPedido = pedidoSeleccionado.value.idPedido

  try {
    await actualizarPedido(idPedido, { comidas })
  } catch (error) {
    await manejarErrorGuardado(error, idPedido)
    accionEnCurso.value = false
    return
  }

  mensajeExito.value = `El pedido #${idPedido} se actualizó correctamente.`
  modoEdicion.value = false
  filasEdicion.value = []
  await Promise.all([cargarPedidos(page.value), recargarDetalle(idPedido)])
  accionEnCurso.value = false
  enfocarDetalle()
}

async function manejarErrorGuardado(error, idPedido) {
  const status = error?.response?.status
  const mensajeApi = error?.response?.data?.error
  const normalizado = normalizeApiError(error)

  if (status === 409) {
    const detalle = await recargarDetalle(idPedido)
    await cargarPedidos(page.value)
    const sigueEditable = detalle && puedeModificar(detalle)
    if (!sigueEditable) {
      modoEdicion.value = false
      filasEdicion.value = []
      apiErrorMessage.value = {
        ...normalizado,
        message: mensajeApi || 'El pedido ya fue autorizado o rechazado y no puede modificarse.',
        canRetry: false,
      }
    } else {
      errorEdicion.value =
        mensajeApi || 'Hay un conflicto con otro pedido. Revisá la selección y volvé a intentar.'
    }
    return
  }

  if (status === 404) {
    apiErrorMessage.value = { ...normalizado, canRetry: false }
    limpiarDetalle()
    await cargarPedidos(page.value)
    return
  }

  errorEdicion.value = mensajeApi || normalizado.message
}

/* ------------------------------------------------------------------ */
/* Eliminación                                                         */
/* ------------------------------------------------------------------ */
watch(pedidoAEliminar, async (pedido) => {
  await nextTick()
  const dialogo = dialogEliminar.value
  if (!dialogo) return
  if (pedido && !dialogo.open) dialogo.showModal()
  if (!pedido && dialogo.open) dialogo.close()
})

function pedirEliminar(pedido) {
  if (!puedeModificar(pedido)) return
  mensajeExito.value = ''
  apiErrorMessage.value = null
  pedidoAEliminar.value = pedido
}

function cancelarEliminar() {
  if (accionEnCurso.value) return
  pedidoAEliminar.value = null
}

async function confirmarEliminar() {
  const pedido = pedidoAEliminar.value
  if (!pedido || accionEnCurso.value) return
  accionEnCurso.value = true
  apiErrorMessage.value = null
  mensajeExito.value = ''
  const idPedido = pedido.idPedido

  try {
    await eliminarPedido(idPedido)
    pedidoAEliminar.value = null
    if (pedidoSeleccionado.value?.idPedido === idPedido) limpiarDetalle()
    mensajeExito.value = `El pedido #${idPedido} se eliminó correctamente.`
    const paginaDestino = pedidosLista.value.length === 1 && page.value > 1 ? page.value - 1 : page.value
    await cargarPedidos(paginaDestino)
  } catch (error) {
    const status = error?.response?.status
    const normalizado = normalizeApiError(error)
    pedidoAEliminar.value = null
    if (status === 409 || status === 400 || status === 404) {
      apiErrorMessage.value = {
        ...normalizado,
        message: error?.response?.data?.error || normalizado.message,
        canRetry: false,
      }
      if (pedidoSeleccionado.value?.idPedido === idPedido) limpiarDetalle()
      await cargarPedidos(page.value)
    } else {
      apiErrorMessage.value = normalizado
      if (normalizado.canRetry) retryOperation.value = () => pedirEliminar(pedido)
    }
  } finally {
    accionEnCurso.value = false
  }
}
</script>

<template>
  <div class="vista-pedidos">
    <!-- Espacio reservado para la barra de navegación del layout -->
    <slot name="navbar" />

    <main class="pedidos-sector" aria-labelledby="titulo-pedidos-sector">
      <header class="encabezado">
        <div>
          <p class="encabezado__sector">{{ nombreSector }}</p>
          <h1 id="titulo-pedidos-sector">Pedidos del sector</h1>
          <p class="encabezado__ayuda">
            Consultá pedidos actuales e históricos. Solo se editan o eliminan pedidos confirmados antes de su corte.
          </p>
        </div>
        <div class="encabezado__acciones">
          <RouterLink class="btn btn--primario" to="/jefe-servicio/pedidos/nuevo">
            <svg class="icono-btn" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path stroke-linecap="round" d="M10 4v12M4 10h12" />
            </svg>
            Nuevo pedido
          </RouterLink>
          <RouterLink class="btn btn--secundario" to="/inicio/jefe-servicio">
            Inicio
          </RouterLink>
        </div>
      </header>

      <aside class="aviso-corte" aria-label="Horario de corte">
        <svg class="icono-aviso" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
          <circle cx="10" cy="10" r="7.5" />
          <path stroke-linecap="round" d="M10 6v4.2l2.8 1.6" />
        </svg>
        <p>
          <strong>Horario de corte:</strong> {{ textoCorte }}.
        </p>
      </aside>

      <p v-if="mensajeExito" class="mensaje mensaje--exito" role="status">
        <span>{{ mensajeExito }}</span>
        <button type="button" class="btn-texto" @click="mensajeExito = ''">Cerrar</button>
      </p>

      <ApiErrorMessage :error="apiErrorMessage" @retry="retryOperation" />

      <!-- ============================ Filtros compactos ============================ -->
      <section class="panel panel--filtros" aria-labelledby="titulo-filtros">
        <div class="filtros-top">
          <h2 id="titulo-filtros" class="panel__titulo">Filtros</h2>

          <div class="barra-busqueda">
            <label for="filtro-consulta" class="visualmente-oculto">Buscar por número, fecha o estado</label>
            <svg class="barra-busqueda__lupa" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <circle cx="9" cy="9" r="6" />
              <path stroke-linecap="round" d="m13.5 13.5 4 4" />
            </svg>
            <input
              id="filtro-consulta"
              v-model="filtros.consulta"
              type="search"
              placeholder="Buscar pedido #, fecha o estado..."
              :disabled="cargandoLista"
            />
            <button
              v-if="filtros.consulta"
              type="button"
              class="barra-busqueda__limpiar"
              aria-label="Borrar búsqueda"
              title="Borrar búsqueda"
              @click="filtros.consulta = ''"
            >
              ×
            </button>
          </div>
        </div>

        <form class="filtros-grid" novalidate @submit.prevent="aplicarFiltros">
          <div class="campo">
            <label for="filtro-desde">
              Desde <span v-if="filtros.desde" class="campo__hint">({{ formatearFecha(filtros.desde) }})</span>
            </label>
            <input
              id="filtro-desde"
              v-model="filtros.desde"
              type="date"
              :aria-invalid="Boolean(errorDesde)"
              :aria-describedby="errorDesde ? 'error-desde' : undefined"
              :disabled="cargandoLista"
            />
            <p v-if="errorDesde" id="error-desde" class="campo__error" role="alert">{{ errorDesde }}</p>
          </div>

          <div class="campo">
            <label for="filtro-hasta">
              Hasta <span v-if="filtros.hasta" class="campo__hint">({{ formatearFecha(filtros.hasta) }})</span>
            </label>
            <input
              id="filtro-hasta"
              v-model="filtros.hasta"
              type="date"
              :aria-invalid="Boolean(errorHasta)"
              :aria-describedby="errorHasta ? 'error-hasta' : undefined"
              :disabled="cargandoLista"
            />
            <p v-if="errorHasta" id="error-hasta" class="campo__error" role="alert">{{ errorHasta }}</p>
          </div>

          <div class="campo">
            <label for="filtro-estado">Estado</label>
            <select id="filtro-estado" v-model="filtros.estado" :disabled="cargandoLista">
              <option v-for="e in ESTADOS_FILTRO" :key="e.value" :value="e.value">{{ e.label }}</option>
            </select>
          </div>

          <div class="campo">
            <label for="filtro-comida">Comida</label>
            <select id="filtro-comida" v-model="filtros.comida" :disabled="cargandoLista">
              <option value="">Todas</option>
              <option v-for="c in COMIDAS" :key="c.idTipoComida" :value="c.idTipoComida">
                {{ c.label }}
              </option>
            </select>
          </div>

          <div class="campo">
            <label for="filtro-menu">Menú</label>
            <select id="filtro-menu" v-model="filtros.menu" :disabled="cargandoLista">
              <option value="">Todos</option>
              <option v-for="m in MENUS" :key="m.idTipoMenu" :value="m.idTipoMenu">{{ m.label }}</option>
            </select>
          </div>

          <div class="filtros-acciones">
            <button type="submit" class="btn btn--primario btn--compacto" :disabled="cargandoLista">
              <svg class="icono-btn" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <circle cx="9" cy="9" r="5.5" />
                <path stroke-linecap="round" d="m13.2 13.2 3.8 3.8" />
              </svg>
              Filtrar
            </button>
            <button type="button" class="btn btn--secundario btn--compacto" :disabled="cargandoLista" @click="limpiarFiltros">
              Limpiar
            </button>
          </div>
        </form>
      </section>

      <!-- ============================ Listado ============================ -->
      <section class="panel" aria-labelledby="titulo-listado" :aria-busy="cargandoLista">
        <div class="panel__cabecera">
          <h2 id="titulo-listado" class="panel__titulo">Pedidos ({{ pedidosFiltradosCliente.length }})</h2>
          <p v-if="rangoMostrado" class="texto-sec">{{ rangoMostrado }}</p>
        </div>

        <p v-if="cargandoLista" class="estado" role="status">
          Cargando pedidos del sector...
        </p>

        <div v-else-if="pedidosFiltradosCliente.length === 0" class="estado" role="status">
          <p v-if="hayFiltrosActivos">
            No hay pedidos que coincidan con los filtros o búsqueda.
          </p>
          <p v-else>Tu sector todavía no tiene pedidos cargados.</p>
          <RouterLink v-if="!hayFiltrosActivos" class="btn btn--primario" to="/jefe-servicio/pedidos/nuevo">
            Cargar primer pedido
          </RouterLink>
        </div>

        <div v-else class="tabla-scroll">
          <table class="tabla tabla--listado">
            <caption class="visualmente-oculto">Pedidos del sector</caption>
            <thead>
              <tr>
                <th scope="col">Pedido</th>
                <th scope="col">Fecha</th>
                <th scope="col">Periodicidad</th>
                <th scope="col">Estado</th>
                <th scope="col">Por comida</th>
                <th scope="col">Por menú</th>
                <th scope="col">Autorizado</th>
                <th scope="col">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="pedido in pedidosFiltradosCliente"
                :key="pedido.idPedido"
                :class="{ 'fila--activa': pedidoSeleccionado?.idPedido === pedido.idPedido }"
              >
                <td data-label="Pedido"><strong>#{{ pedido.idPedido }}</strong></td>
                <td data-label="Fecha">
                  <div class="celda-apilada">
                    <strong>{{ formatearFecha(fechaDePedido(pedido)) }}</strong>
                    <span class="texto-sec texto-cap">{{ diaSemana(fechaDePedido(pedido)) }}</span>
                  </div>
                </td>
                <td data-label="Periodicidad">{{ etiquetaPeriodicidad(pedido) }}</td>
                <td data-label="Estado">
                  <span :class="['badge', `badge--${String(pedido.estado).toLowerCase()}`]">
                    <span aria-hidden="true">{{ infoEstado(pedido.estado).icono }}</span>
                    {{ infoEstado(pedido.estado).texto }}
                  </span>
                </td>
                <td data-label="Por comida">
                  <ul class="chips" aria-label="Cantidad pedida por comida">
                    <li
                      v-for="c in COMIDAS"
                      :key="c.idTipoComida"
                      :class="['chip', { 'chip--cero': !resumenesLista.get(pedido.idPedido)?.pedido.porComida[c.idTipoComida] }]"
                    >
                      <span class="visualmente-oculto">{{ c.label }}:</span>
                      <span aria-hidden="true">{{ c.inicial }}</span>
                      {{ resumenesLista.get(pedido.idPedido)?.pedido.porComida[c.idTipoComida] ?? 0 }}
                    </li>
                  </ul>
                </td>
                <td data-label="Por menú">
                  <ul class="chips" aria-label="Cantidad pedida por tipo de menú">
                    <li
                      v-for="m in MENUS"
                      :key="m.idTipoMenu"
                      :class="['chip', { 'chip--cero': !resumenesLista.get(pedido.idPedido)?.pedido.porMenu[m.idTipoMenu] }]"
                    >
                      {{ m.label }}: {{ resumenesLista.get(pedido.idPedido)?.pedido.porMenu[m.idTipoMenu] ?? 0 }}
                    </li>
                  </ul>
                </td>
                <td data-label="Autorizado">
                  <template v-if="resumenesLista.get(pedido.idPedido)?.autorizado">
                    <strong>{{ resumenesLista.get(pedido.idPedido).autorizado.total }}</strong>
                    de {{ resumenesLista.get(pedido.idPedido).pedido.total }}
                  </template>
                  <span v-else-if="String(pedido.estado).toLowerCase() === 'rechazado'" class="texto-sec">
                    Rechazado
                  </span>
                  <span v-else class="texto-sec">Pendiente</span>
                </td>
                <td data-label="Acciones">
                  <div class="celda-acciones">
                    <div class="acciones-fila">
                      <button
                        type="button"
                        class="btn-icono btn-icono--ver"
                        :aria-label="`Ver detalle del pedido #${pedido.idPedido}`"
                        title="Ver detalle"
                        :disabled="accionEnCurso"
                        @click="abrirPedido(pedido, false)"
                      >
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                          <path d="M1.8 10s3-5.5 8.2-5.5S18.2 10 18.2 10s-3 5.5-8.2 5.5S1.8 10 1.8 10Z" />
                          <circle cx="10" cy="10" r="2.3" />
                        </svg>
                        <span>Ver</span>
                      </button>

                      <template v-if="puedeModificar(pedido)">
                        <button
                          type="button"
                          class="btn-icono btn-icono--editar"
                          :aria-label="`Editar pedido #${pedido.idPedido}`"
                          title="Editar pedido"
                          :disabled="accionEnCurso"
                          @click="abrirPedido(pedido, true)"
                        >
                          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" d="m13.8 3.2 3 3-9.8 9.8H4v-3l9.8-9.8Z" />
                          </svg>
                          <span>Editar</span>
                        </button>

                        <button
                          type="button"
                          class="btn-icono btn-icono--eliminar"
                          :aria-label="`Eliminar pedido #${pedido.idPedido}`"
                          title="Eliminar pedido"
                          :disabled="accionEnCurso"
                          @click="pedirEliminar(pedido)"
                        >
                          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                            <path stroke-linecap="round" d="M3.5 5.5h13M8 5.5V4h4v1.5M6 5.5l.7 10.5h6.6l.7-10.5" />
                          </svg>
                          <span>Eliminar</span>
                        </button>
                      </template>
                    </div>

                    <p v-if="puedeModificar(pedido)" class="texto-sec nota-fila">
                      Hasta {{ textoLimiteEdicion(pedido) }}
                    </p>
                    <p v-else class="texto-sec nota-fila">
                      Solo consulta: {{ motivoBloqueo(pedido).toLowerCase() }}
                    </p>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <nav v-if="totalPaginas > 1" class="paginacion" aria-label="Paginación de pedidos">
          <button
            type="button"
            class="btn btn--secundario btn--compacto"
            :disabled="cargandoLista || page <= 1"
            @click="cargarPedidos(page - 1)"
          >
            Anterior
          </button>
          <span>Página {{ page }} de {{ totalPaginas }}</span>
          <button
            type="button"
            class="btn btn--secundario btn--compacto"
            :disabled="cargandoLista || page >= totalPaginas"
            @click="cargarPedidos(page + 1)"
          >
            Siguiente
          </button>
        </nav>
      </section>

      <!-- ====================== Detalle / edición ====================== -->
      <section
        v-if="pedidoSeleccionado"
        class="panel panel--detalle"
        aria-labelledby="titulo-detalle"
      >
        <header class="detalle__cabecera">
          <div>
            <h2 id="titulo-detalle" ref="tituloDetalle" class="panel__titulo" tabindex="-1">
              {{ modoEdicion ? 'Editando pedido' : 'Detalle del pedido' }} #{{ pedidoSeleccionado.idPedido }}
            </h2>
            <p class="detalle__meta">
              <span>
                <strong>{{ formatearFecha(fechaDePedido(pedidoSeleccionado)) }}</strong>
                <span class="texto-cap"> ({{ diaSemana(fechaDePedido(pedidoSeleccionado)) }})</span>
              </span>
              <span>{{ etiquetaPeriodicidad(pedidoSeleccionado) }}</span>
              <span :class="['badge', `badge--${String(pedidoSeleccionado.estado).toLowerCase()}`]">
                <span aria-hidden="true">{{ infoEstado(pedidoSeleccionado.estado).icono }}</span>
                {{ infoEstado(pedidoSeleccionado.estado).texto }}
              </span>
            </p>
          </div>

          <div v-if="!modoEdicion" class="acciones-fila">
            <button
              v-if="puedeModificar(pedidoSeleccionado)"
              type="button"
              class="btn-icono btn-icono--editar"
              :disabled="accionEnCurso"
              @click="entrarEnEdicion"
            >
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="m13.8 3.2 3 3-9.8 9.8H4v-3l9.8-9.8Z" />
              </svg>
              <span>Editar</span>
            </button>
            <button
              v-if="puedeModificar(pedidoSeleccionado)"
              type="button"
              class="btn-icono btn-icono--eliminar"
              :disabled="accionEnCurso"
              @click="pedirEliminar(pedidoSeleccionado)"
            >
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path stroke-linecap="round" d="M3.5 5.5h13M8 5.5V4h4v1.5M6 5.5l.7 10.5h6.6l.7-10.5" />
              </svg>
              <span>Eliminar</span>
            </button>
            <button type="button" class="btn btn--secundario btn--compacto" :disabled="accionEnCurso" @click="alCerrarDetalle">
              Cerrar
            </button>
          </div>
        </header>

        <p
          v-if="pedidoSeleccionado.motivo_rechazo || pedidoSeleccionado.motivoRechazo"
          class="aviso aviso--peligro"
          role="status"
        >
          <strong>Motivo del rechazo:</strong>
          {{ pedidoSeleccionado.motivo_rechazo || pedidoSeleccionado.motivoRechazo }}
        </p>

        <p v-if="puedeModificar(pedidoSeleccionado)" class="aviso aviso--info">
          Editable hasta el <strong>{{ textoLimiteEdicion(pedidoSeleccionado) }}</strong>.
        </p>
        <p v-else class="aviso aviso--bloqueo">
          Solo consulta: {{ motivoBloqueo(pedidoSeleccionado) }}
        </p>

        <!-- Totales: pedido y autorizado por separado -->
        <div class="tarjetas">
          <article
            v-for="t in tarjetasResumen"
            :key="t.id"
            :class="['tarjeta', `tarjeta--${t.variante}`]"
            :aria-labelledby="`tarjeta-${t.id}`"
          >
            <h3 :id="`tarjeta-${t.id}`" class="tarjeta__titulo">{{ t.titulo }}</h3>
            <p class="texto-sec">{{ t.nota }}</p>

            <template v-if="t.matriz">
              <div class="tabla-scroll">
                <table class="tabla tabla--totales">
                  <caption class="visualmente-oculto">{{ t.titulo }} por tipo de menú y comida</caption>
                  <thead>
                    <tr>
                      <th scope="col">Menú</th>
                      <th v-for="c in COMIDAS" :key="c.idTipoComida" scope="col" class="num">
                        <abbr :title="c.label">{{ c.inicial }}</abbr>
                      </th>
                      <th scope="col" class="num">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="m in MENUS" :key="m.idTipoMenu">
                      <th scope="row">{{ m.label }}</th>
                      <td v-for="c in COMIDAS" :key="c.idTipoComida" class="num">
                        {{ t.matriz.celdas[m.idTipoMenu][c.idTipoComida] }}
                      </td>
                      <td class="num"><strong>{{ t.matriz.porMenu[m.idTipoMenu] }}</strong></td>
                    </tr>
                  </tbody>
                  <tfoot>
                    <tr>
                      <th scope="row">Total</th>
                      <td v-for="c in COMIDAS" :key="c.idTipoComida" class="num">
                        {{ t.matriz.porComida[c.idTipoComida] }}
                      </td>
                      <td class="num">{{ t.matriz.total }}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
              <p v-if="t.desglose" class="tarjeta__desglose">
                <span class="chip-condicion chip-condicion--regular">
                  <span aria-hidden="true">✓</span> Regulares: {{ t.desglose.regulares }}
                </span>
                <span class="chip-condicion chip-condicion--excepcion">
                  <span aria-hidden="true">!</span> Excepciones: {{ t.desglose.excepciones }}
                </span>
              </p>
            </template>
          </article>

          <article v-if="modoEdicion" class="tarjeta tarjeta--cupo" aria-labelledby="tarjeta-cupo">
            <h3 id="tarjeta-cupo" class="tarjeta__titulo">Cupo del sector por comida</h3>
            <p v-if="!cuposCargados" class="texto-sec">
              La condición Regular o Excepción la calcula el sistema al guardar.
            </p>
            <template v-else>
              <p class="texto-sec">Al superar el cupo, las siguientes solicitudes pasan a Excepción.</p>
              <ul class="cupos">
                <li v-for="u in usoDeCupo" :key="u.idTipoComida" class="cupo">
                  <div class="cupo__fila">
                    <strong>{{ u.label }}</strong>
                    <span>
                      {{ u.regulares }}/{{ u.cupo }} reg.<template v-if="u.excepciones">
                        · {{ u.excepciones }} exc.</template>
                    </span>
                  </div>
                  <div class="cupo__barra" role="img" :aria-label="`${u.label}: ${u.regulares} de ${u.cupo} cupos regulares usados`">
                    <span :style="{ width: `${u.porcentaje}%` }"></span>
                  </div>
                </li>
              </ul>
            </template>
          </article>
        </div>

        <!-- ---------------------- Solo lectura ---------------------- -->
        <template v-if="!modoEdicion">
          <h3 class="subtitulo">Personas y comidas solicitadas</h3>
          <ul class="leyenda" aria-label="Referencias de la tabla">
            <li><span class="chip-condicion chip-condicion--regular"><span aria-hidden="true">✓</span> Regular</span> dentro del cupo</li>
            <li><span class="chip-condicion chip-condicion--excepcion"><span aria-hidden="true">!</span> Excepción</span> superó el cupo</li>
          </ul>

          <div class="tabla-scroll">
            <table class="tabla tabla--matriz">
              <caption class="visualmente-oculto">Personas y comidas solicitadas en el pedido</caption>
              <thead>
                <tr>
                  <th scope="col">Persona</th>
                  <th scope="col">Menú</th>
                  <th v-for="c in COMIDAS" :key="c.idTipoComida" scope="col" class="centrado">{{ c.label }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="fila in filasDetalle" :key="fila.idPersonal">
                  <th scope="row" class="celda-persona">
                    <strong>{{ fila.nombre }}</strong>
                    <span class="texto-sec">DNI {{ fila.dni }}<template v-if="fila.esResidente"> (residente)</template></span>
                  </th>
                  <td>{{ fila.tipoMenu }}</td>
                  <td v-for="c in COMIDAS" :key="c.idTipoComida" class="centrado">
                    <template v-if="solicitudDe(fila, c.idTipoComida)">
                      <div class="celda-solicitud">
                        <span
                          :class="[
                            'chip-condicion',
                            esExcepcion(solicitudDe(fila, c.idTipoComida)) ? 'chip-condicion--excepcion' : 'chip-condicion--regular',
                          ]"
                        >
                          <span aria-hidden="true">{{ esExcepcion(solicitudDe(fila, c.idTipoComida)) ? '!' : '✓' }}</span>
                          {{ esExcepcion(solicitudDe(fila, c.idTipoComida)) ? 'Excepción' : 'Regular' }}
                        </span>
                        <span
                          v-if="mostrarAutorizacionPorCelda"
                          :class="['chip-aut', `chip-aut--${estadoAutorizacion(solicitudDe(fila, c.idTipoComida))}`]"
                        >
                          <span aria-hidden="true">{{ ETIQUETAS_AUTORIZACION[estadoAutorizacion(solicitudDe(fila, c.idTipoComida))].icono }}</span>
                          {{ ETIQUETAS_AUTORIZACION[estadoAutorizacion(solicitudDe(fila, c.idTipoComida))].texto }}
                        </span>
                      </div>
                    </template>
                    <span v-else class="sin-solicitud">
                      <span aria-hidden="true">—</span>
                      <span class="visualmente-oculto">No solicitada</span>
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <!-- ---------------------- Edición ---------------------- -->
        <form v-else class="edicion" novalidate @submit.prevent="guardarEdicion">
          <h3 class="subtitulo">Personas y comidas</h3>

          <div class="agregar">
            <div class="campo">
              <label for="agregar-sector">Agregar personal del sector</label>
              <div class="campo__grupo">
                <select
                  id="agregar-sector"
                  v-model="personaSectorSeleccionadaId"
                  :disabled="accionEnCurso || personalSectorSinAgregar.length === 0"
                >
                  <option value="">
                    {{ personalSectorSinAgregar.length ? 'Elegí una persona' : 'No queda personal por agregar' }}
                  </option>
                  <option v-for="p in personalSectorSinAgregar" :key="p.idPersonal" :value="p.idPersonal">
                    {{ p.nombre }} (DNI {{ p.dni }})
                  </option>
                </select>
                <button
                  type="button"
                  class="btn btn--secundario btn--compacto"
                  :disabled="accionEnCurso || !personaSectorSeleccionadaId"
                  @click="agregarPersonaSector"
                >
                  Agregar
                </button>
              </div>
            </div>

            <div class="campo">
              <label for="buscar-residente">Agregar residente</label>
              <div class="barra-busqueda barra-busqueda--inline">
                <svg class="barra-busqueda__lupa" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <circle cx="9" cy="9" r="6" />
                  <path stroke-linecap="round" d="m13.5 13.5 4 4" />
                </svg>
                <input
                  id="buscar-residente"
                  v-model="busquedaResidente"
                  type="search"
                  autocomplete="off"
                  placeholder="Buscar residente por nombre, apellido o DNI..."
                  aria-describedby="ayuda-residente"
                  :disabled="accionEnCurso"
                />
              </div>
              <p id="ayuda-residente" class="campo__ayuda" aria-live="polite">{{ mensajeBusquedaResidente }}</p>
              <ul v-if="sugerenciasResidentes.length" class="sugerencias">
                <li v-for="r in sugerenciasResidentes" :key="r.idPersonal">
                  <button type="button" class="sugerencia" :disabled="accionEnCurso" @click="agregarResidente(r)">
                    <strong>{{ r.nombre }}</strong>
                    <span class="texto-sec">DNI {{ r.dni }} · Menú {{ r.tipoMenu }}</span>
                  </button>
                </li>
              </ul>
            </div>
          </div>

          <ul class="leyenda" aria-label="Referencias de la tabla">
            <li><span class="marca marca--regular" aria-hidden="true">✓</span> Regular</li>
            <li><span class="marca marca--excepcion" aria-hidden="true">EXC</span> Excepción (estimada)</li>
            <li><span class="marca marca--vacia" aria-hidden="true"></span> No solicitada</li>
          </ul>

          <p v-if="filasEdicion.length === 0" class="estado">
            El pedido no tiene personas. Agregá personal del sector o un residente.
          </p>

          <div v-else class="tabla-scroll">
            <table class="tabla tabla--matriz tabla--edicion">
              <caption class="visualmente-oculto">Selección de comidas por persona</caption>
              <thead>
                <tr>
                  <th scope="col">Persona</th>
                  <th scope="col">Menú</th>
                  <th v-for="c in COMIDAS" :key="c.idTipoComida" scope="col" class="centrado">
                    <div class="cabecera-comida">
                      <span>{{ c.label }}</span>
                      <button
                        type="button"
                        class="btn-enlace"
                        :aria-label="`${columnaCompleta(c.idTipoComida) ? 'Quitar' : 'Seleccionar'} ${c.label.toLowerCase()} para todas las personas`"
                        :disabled="accionEnCurso"
                        @click="alternarColumna(c.idTipoComida)"
                      >
                        {{ columnaCompleta(c.idTipoComida) ? 'Ninguno' : 'Todos' }}
                      </button>
                    </div>
                  </th>
                  <th scope="col" class="centrado">Fila</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(fila, indice) in filasEdicion" :key="fila.uid">
                  <th scope="row" class="celda-persona">
                    <strong>{{ fila.nombre }}</strong>
                    <span class="texto-sec">DNI {{ fila.dni }}<template v-if="fila.esResidente"> (residente)</template></span>
                    <span v-if="filaSinComidas(fila)" class="texto-aviso">Sin comidas: no se incluirá.</span>
                  </th>
                  <td>{{ fila.tipoMenu }}</td>
                  <td v-for="c in COMIDAS" :key="c.idTipoComida" class="centrado">
                    <button
                      type="button"
                      :class="[
                        'celda-comida',
                        {
                          'celda-comida--regular': fila.comidas[c.idTipoComida] && condicionEdicion(fila, c.idTipoComida) === 'regular',
                          'celda-comida--excepcion': fila.comidas[c.idTipoComida] && condicionEdicion(fila, c.idTipoComida) === 'excepcion',
                        },
                      ]"
                      :aria-pressed="Boolean(fila.comidas[c.idTipoComida])"
                      :aria-label="`${fila.nombre}, ${c.label.toLowerCase()}: ${
                        fila.comidas[c.idTipoComida]
                          ? (condicionEdicion(fila, c.idTipoComida) === 'excepcion' ? 'solicitada como excepción' : 'solicitada')
                          : 'no solicitada'
                      }`"
                      :disabled="accionEnCurso"
                      @click="alternarComida(fila, c.idTipoComida)"
                    >
                      <template v-if="fila.comidas[c.idTipoComida]">
                        <span aria-hidden="true">{{ condicionEdicion(fila, c.idTipoComida) === 'excepcion' ? 'EXC' : '✓' }}</span>
                      </template>
                    </button>
                  </td>
                  <td class="centrado">
                    <div class="acciones-fila acciones-fila--centro">
                      <button
                        type="button"
                        class="btn-enlace"
                        :aria-label="`${filaCompleta(fila) ? 'Quitar todas las comidas de' : 'Seleccionar todas las comidas para'} ${fila.nombre}`"
                        :disabled="accionEnCurso"
                        @click="alternarFila(fila)"
                      >
                        {{ filaCompleta(fila) ? 'Ninguna' : 'Todas' }}
                      </button>
                      <button
                        type="button"
                        class="btn-icono btn-icono--eliminar btn-icono--chico"
                        :aria-label="`Quitar a ${fila.nombre} del pedido`"
                        title="Quitar persona"
                        :disabled="accionEnCurso"
                        @click="quitarFila(indice)"
                      >
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                          <path stroke-linecap="round" d="M5 5l10 10M15 5 5 15" />
                        </svg>
                        <span>Quitar</span>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p class="texto-sec nota-edicion">
            Regular/Excepción en edición es estimada según orden de incorporación; la definitiva la calcula el backend al guardar.
          </p>

          <div class="barra-acciones">
            <p v-if="errorEdicion" class="campo__error barra-acciones__error" role="alert">{{ errorEdicion }}</p>
            <div class="barra-acciones__pie">
              <p class="barra-acciones__estado" aria-live="polite">
                {{ totalSolicitudesEdicion }} solicitud(es)
                <template v-if="hayCambios">· Cambios sin guardar</template>
              </p>
              <div class="barra-acciones__botones">
                <button type="button" class="btn btn--secundario btn--compacto" :disabled="accionEnCurso" @click="cancelarEdicion">
                  Cancelar
                </button>
                <button type="submit" class="btn btn--primario btn--compacto" :disabled="accionEnCurso || filasEdicion.length === 0">
                  {{ accionEnCurso ? 'Guardando...' : 'Guardar cambios' }}
                </button>
              </div>
            </div>
          </div>
        </form>
      </section>
    </main>

    <!-- ===================== Confirmación de eliminación ===================== -->
    <dialog
      ref="dialogEliminar"
      class="dialogo"
      aria-labelledby="titulo-eliminar"
      aria-describedby="descripcion-eliminar"
      @cancel.prevent="cancelarEliminar"
    >
      <div v-if="pedidoAEliminar" class="dialogo__contenido">
        <h2 id="titulo-eliminar">¿Eliminar pedido #{{ pedidoAEliminar.idPedido }}?</h2>
        <p id="descripcion-eliminar">
          Se eliminará el pedido del {{ formatearFecha(fechaDePedido(pedidoAEliminar)) }} con sus solicitudes.
        </p>
        <div class="dialogo__acciones">
          <button type="button" class="btn btn--secundario btn--compacto" :disabled="accionEnCurso" @click="cancelarEliminar">
            Cancelar
          </button>
          <button type="button" class="btn btn--peligro-solido btn--compacto" :disabled="accionEnCurso" @click="confirmarEliminar">
            {{ accionEnCurso ? 'Eliminando...' : 'Eliminar' }}
          </button>
        </div>
      </div>
    </dialog>
  </div>
</template>

<style scoped>
.vista-pedidos {
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

.pedidos-sector {
  max-width: 1280px;
  margin: 0 auto;
  padding: 1rem;
}

.visualmente-oculto {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

:focus-visible {
  outline: 2px solid var(--c-primario);
  outline-offset: 2px;
}

/* ---------- Encabezado ---------- */
.encabezado {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}

.encabezado__sector {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--c-primario);
}

.encabezado h1 {
  margin: 0.15rem 0 0;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.encabezado__ayuda {
  margin: 0.25rem 0 0;
  font-size: 0.875rem;
  color: var(--c-texto-sec);
}

.encabezado__acciones {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.aviso-corte {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  margin-bottom: 0.9rem;
  padding: 0.6rem 0.85rem;
  border: 1px solid var(--c-ambar-borde);
  border-radius: 8px;
  background: var(--c-ambar-suave);
  color: var(--c-ambar-texto);
  font-size: 0.84rem;
}

.aviso-corte p {
  margin: 0;
}

.icono-aviso {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

/* ---------- Paneles ---------- */
.panel {
  margin-bottom: 1rem;
  padding: 1rem;
  border: 1px solid var(--c-borde);
  border-radius: 10px;
  background: var(--c-superficie);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.panel--detalle {
  border-top: 3px solid var(--c-primario);
}

.panel__titulo {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
}

.panel__titulo:focus {
  outline: none;
}

.panel__cabecera {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.subtitulo {
  margin: 1.15rem 0 0.55rem;
  font-size: 0.95rem;
  font-weight: 700;
}

/* ---------- Barra de búsqueda tipo lupa + Filtros compactos ---------- */
.filtros-top {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  margin-bottom: 0.75rem;
}

.barra-busqueda {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
  max-width: 420px;
}

.barra-busqueda--inline {
  max-width: 100%;
}

.barra-busqueda__lupa {
  position: absolute;
  left: 0.75rem;
  width: 16px;
  height: 16px;
  color: var(--c-texto-sec);
  pointer-events: none;
}

.barra-busqueda input[type='search'] {
  width: 100%;
  height: 38px;
  min-height: 38px;
  padding: 0.35rem 2rem 0.35rem 2.25rem;
  border: 1px solid var(--c-borde-fuerte);
  border-radius: 999px;
  background: var(--c-fondo);
  color: var(--c-texto);
  font-family: var(--fuente);
  font-size: 0.85rem;
  box-sizing: border-box;
  transition: border-color 0.15s, background-color 0.15s, box-shadow 0.15s;
}

.barra-busqueda input[type='search']:focus {
  outline: none;
  background: var(--c-superficie);
  border-color: var(--c-primario);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.barra-busqueda__limpiar {
  position: absolute;
  right: 0.5rem;
  width: 24px;
  height: 24px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--c-texto-sec);
  font-size: 1rem;
  line-height: 1;
  cursor: pointer;
}

.barra-busqueda__limpiar:hover {
  background: var(--c-borde);
  color: var(--c-texto);
}

.filtros-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.75rem;
  align-items: end;
}

.filtros-grid > *,
.campo,
.filtros-acciones {
  min-width: 0;
  max-width: 100%;
}

.campo {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.campo label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--c-texto-sec);
}

.campo__hint {
  font-weight: 500;
  color: var(--c-primario);
}

.campo__grupo {
  display: flex;
  gap: 0.45rem;
  align-items: center;
}

.campo__grupo select {
  flex: 1;
  min-width: 0;
}

.campo__ayuda {
  margin: 0.15rem 0 0;
  font-size: 0.78rem;
  color: var(--c-texto-sec);
}

.campo__error {
  margin: 0.15rem 0 0;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--c-rojo-texto);
}

input[type='date'],
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
  background: var(--c-superficie);
  color: var(--c-texto);
  font-family: var(--fuente);
  font-size: 0.84rem;
  box-sizing: border-box;
}

input[aria-invalid='true'] {
  border-color: var(--c-rojo-texto);
  background: var(--c-rojo-suave);
}

input:disabled,
select:disabled {
  background: var(--c-fondo);
  color: var(--c-texto-sec);
}

.filtros-acciones {
  display: flex;
  flex-wrap: nowrap;
  gap: 0.5rem;
  align-items: center;
}

.filtros-acciones .btn--compacto {
  flex: 1 1 0;
  min-width: 0;
}

/* ---------- Botones y botones con ícono ---------- */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  min-height: 38px;
  padding: 0.4rem 0.85rem;
  border: 1px solid var(--c-borde-fuerte);
  border-radius: 7px;
  background: var(--c-superficie);
  color: var(--c-texto);
  font-family: var(--fuente);
  font-size: 0.84rem;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
}

.btn--compacto {
  height: 36px;
  min-height: 36px;
  padding: 0.3rem 0.75rem;
  font-size: 0.82rem;
}

.btn:hover:not(:disabled) {
  background: var(--c-fondo);
}

.btn--primario {
  border-color: var(--c-primario);
  background: var(--c-primario);
  color: #ffffff;
}

.btn--primario:hover:not(:disabled) {
  background: var(--c-primario-hover);
}

.btn--peligro-solido {
  border-color: var(--c-rojo-texto);
  background: var(--c-rojo-texto);
  color: #ffffff;
}

.btn--peligro-solido:hover:not(:disabled) {
  background: #991b1b;
}

.icono-btn {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

.btn-icono {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  height: 32px;
  padding: 0 0.6rem;
  border: 1px solid var(--c-borde-fuerte);
  border-radius: 6px;
  background: var(--c-superficie);
  color: var(--c-texto);
  font-family: var(--fuente);
  font-size: 0.78rem;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color 0.15s, border-color 0.15s;
}

.btn-icono svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.btn-icono--ver:hover:not(:disabled) {
  border-color: var(--c-primario);
  background: var(--c-primario-suave);
  color: var(--c-primario-hover);
}

.btn-icono--editar {
  border-color: #bfdbfe;
  background: var(--c-primario-suave);
  color: var(--c-primario-hover);
}

.btn-icono--editar:hover:not(:disabled) {
  border-color: var(--c-primario);
  background: #dbeafe;
}

.btn-icono--eliminar {
  border-color: var(--c-rojo-borde);
  background: var(--c-rojo-suave);
  color: var(--c-rojo-texto);
}

.btn-icono--eliminar:hover:not(:disabled) {
  border-color: #f87171;
  background: #fee2e2;
}

.btn-icono--chico {
  height: 28px;
  padding: 0 0.5rem;
  font-size: 0.75rem;
}

.btn:disabled,
.btn-icono:disabled,
.btn-enlace:disabled,
.celda-comida:disabled,
.sugerencia:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-enlace,
.btn-texto {
  padding: 0.1rem 0.25rem;
  border: 0;
  background: transparent;
  color: var(--c-primario);
  font-family: var(--fuente);
  font-size: 0.78rem;
  font-weight: 600;
  text-decoration: underline;
  white-space: nowrap;
  cursor: pointer;
}

/* ---------- Mensajes y estados ---------- */
.mensaje {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin: 0 0 0.9rem;
  padding: 0.65rem 0.9rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
}

.mensaje--exito {
  border: 1px solid var(--c-verde-borde);
  background: var(--c-verde-suave);
  color: var(--c-verde-texto);
}

.aviso {
  margin: 0.75rem 0 0;
  padding: 0.6rem 0.85rem;
  border-radius: 8px;
  font-size: 0.84rem;
}

.aviso--info {
  border: 1px solid var(--c-primario-suave);
  background: var(--c-primario-suave);
  color: var(--c-primario-hover);
}

.aviso--bloqueo {
  border: 1px solid var(--c-borde);
  background: var(--c-fondo);
  color: var(--c-texto-sec);
}

.aviso--peligro {
  border: 1px solid var(--c-rojo-borde);
  background: var(--c-rojo-suave);
  color: var(--c-rojo-texto);
}

.estado {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.65rem;
  padding: 1.75rem 1rem;
  border: 1px dashed var(--c-borde-fuerte);
  border-radius: 8px;
  background: var(--c-fondo);
  color: var(--c-texto-sec);
  font-size: 0.875rem;
  text-align: center;
}

.estado p {
  margin: 0;
}

.texto-sec {
  font-size: 0.78rem;
  color: var(--c-texto-sec);
}

.texto-cap {
  text-transform: capitalize;
}

.texto-aviso {
  display: block;
  margin-top: 0.2rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--c-ambar-texto);
}

/* ---------- Tablas ---------- */
.tabla-scroll {
  width: 100%;
  overflow-x: auto;
  border: 1px solid var(--c-borde);
  border-radius: 8px;
  background: var(--c-superficie);
}

.tabla {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}

.tabla th,
.tabla td {
  padding: 0.55rem 0.65rem;
  border-bottom: 1px solid var(--c-borde);
  text-align: left;
  vertical-align: middle;
}

.tabla thead th,
.tabla tfoot th,
.tabla tfoot td {
  background: var(--c-fondo);
  color: var(--c-texto-sec);
  font-size: 0.76rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.tabla tbody tr:hover {
  background: #f8fafc;
}

.tabla tbody tr:last-child th,
.tabla tbody tr:last-child td {
  border-bottom: 0;
}

.tabla tbody th {
  font-weight: 400;
}

.centrado {
  text-align: center !important;
}

.num {
  text-align: right !important;
  font-variant-numeric: tabular-nums;
}

.fila--activa {
  background: var(--c-primario-suave) !important;
  box-shadow: inset 3px 0 0 var(--c-primario);
}

.celda-apilada {
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}

.celda-acciones {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nota-fila {
  margin: 0;
  font-size: 0.74rem;
}

.acciones-fila {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
}

.acciones-fila--centro {
  justify-content: center;
  flex-direction: column;
  gap: 0.25rem;
}

.celda-persona {
  min-width: 11rem;
}

.celda-persona strong,
.celda-persona .texto-sec {
  display: block;
}

.cabecera-comida {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
}

.celda-solicitud {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
}

.sin-solicitud {
  color: var(--c-texto-sec);
}

/* ---------- Chips y badges ---------- */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.18rem 0.55rem;
  border: 1px solid var(--c-borde-fuerte);
  border-radius: 999px;
  background: var(--c-fondo);
  color: var(--c-texto);
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.badge--confirmado {
  border-color: var(--c-ambar-borde);
  background: var(--c-ambar-suave);
  color: var(--c-ambar-texto);
}

.badge--autorizado {
  border-color: var(--c-verde-borde);
  background: var(--c-verde-suave);
  color: var(--c-verde-texto);
}

.badge--rechazado {
  border-color: var(--c-rojo-borde);
  background: var(--c-rojo-suave);
  color: var(--c-rojo-texto);
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.chip {
  padding: 0.14rem 0.45rem;
  border: 1px solid var(--c-borde);
  border-radius: 5px;
  background: var(--c-fondo);
  color: var(--c-texto);
  font-size: 0.75rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.chip--cero {
  background: transparent;
  color: var(--c-texto-sec);
  font-weight: 400;
}

.chip-condicion {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.14rem 0.5rem;
  border-radius: 5px;
  font-size: 0.74rem;
  font-weight: 600;
  white-space: nowrap;
}

.chip-condicion--regular {
  border: 1px solid var(--c-verde-borde);
  background: var(--c-verde-suave);
  color: var(--c-verde-texto);
}

.chip-condicion--excepcion {
  border: 1px solid var(--c-exc-borde);
  background: var(--c-exc-suave);
  color: var(--c-exc-texto);
}

.chip-aut {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.74rem;
  font-weight: 600;
  white-space: nowrap;
}

.chip-aut--autorizada {
  color: var(--c-verde-texto);
}

.chip-aut--no_autorizada {
  color: var(--c-rojo-texto);
}

.chip-aut--pendiente {
  color: var(--c-ambar-texto);
}

/* ---------- Detalle ---------- */
.detalle__cabecera {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.detalle__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem 0.85rem;
  margin: 0.35rem 0 0;
  font-size: 0.85rem;
}

.tarjetas {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.8rem;
  margin-top: 0.9rem;
}

.tarjeta {
  min-width: 0;
  padding: 0.85rem;
  border: 1px solid var(--c-borde);
  border-radius: 8px;
  background: var(--c-fondo);
}

.tarjeta--autorizado {
  border-color: var(--c-verde-borde);
  background: var(--c-verde-suave);
}

.tarjeta--pendiente {
  border-style: dashed;
}

.tarjeta--cupo {
  background: var(--c-superficie);
}

.tarjeta__titulo {
  margin: 0 0 0.2rem;
  font-size: 0.92rem;
  font-weight: 700;
}

.tarjeta .texto-sec {
  margin: 0 0 0.55rem;
}

.tarjeta .tabla-scroll {
  background: var(--c-superficie);
}

.tarjeta__desglose {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin: 0.65rem 0 0;
}

.leyenda {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 1rem;
  margin: 0 0 0.65rem;
  padding: 0;
  list-style: none;
  font-size: 0.78rem;
  color: var(--c-texto-sec);
}

.leyenda li {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

/* ---------- Cupos ---------- */
.cupos {
  display: grid;
  gap: 0.6rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.cupo__fila {
  display: flex;
  justify-content: space-between;
  gap: 0.35rem;
  font-size: 0.8rem;
}

.cupo__barra {
  height: 6px;
  margin-top: 0.25rem;
  border-radius: 999px;
  background: var(--c-borde);
  overflow: hidden;
}

.cupo__barra span {
  display: block;
  height: 100%;
  background: var(--c-primario);
}

/* ---------- Edición ---------- */
.agregar {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.85rem;
  margin-bottom: 0.9rem;
}

.sugerencias {
  display: grid;
  gap: 0.3rem;
  margin: 0.3rem 0 0;
  padding: 0;
  list-style: none;
}

.sugerencia {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.1rem;
  width: 100%;
  padding: 0.45rem 0.7rem;
  border: 1px solid var(--c-borde-fuerte);
  border-radius: 7px;
  background: var(--c-superficie);
  color: var(--c-texto);
  font-family: var(--fuente);
  font-size: 0.82rem;
  text-align: left;
  cursor: pointer;
}

.sugerencia:hover:not(:disabled) {
  border-color: var(--c-primario);
  background: var(--c-primario-suave);
}

.celda-comida {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 38px;
  border: 1px solid var(--c-borde-fuerte);
  border-radius: 7px;
  background: var(--c-superficie);
  color: var(--c-texto);
  font-family: var(--fuente);
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
}

.celda-comida--regular {
  border-color: var(--c-primario);
  background: var(--c-primario);
  color: #ffffff;
}

.celda-comida--excepcion {
  border: 1px dashed var(--c-exc-borde);
  background: var(--c-exc-suave);
  color: var(--c-exc-texto);
  font-size: 0.72rem;
}

.marca {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 20px;
  padding: 0 0.3rem;
  border-radius: 5px;
  font-size: 0.68rem;
  font-weight: 700;
}

.marca--regular {
  background: var(--c-primario);
  color: #ffffff;
}

.marca--excepcion {
  border: 1px dashed var(--c-exc-borde);
  background: var(--c-exc-suave);
  color: var(--c-exc-texto);
}

.marca--vacia {
  border: 1px solid var(--c-borde-fuerte);
  background: var(--c-superficie);
}

.nota-edicion {
  margin: 0.65rem 0 0;
  font-size: 0.78rem;
}

.barra-acciones {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  margin-top: 1rem;
  padding-top: 0.85rem;
  border-top: 1px solid var(--c-borde);
}

.barra-acciones__error {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--c-rojo-borde);
  border-radius: 7px;
  background: var(--c-rojo-suave);
}

.barra-acciones__pie {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.barra-acciones__estado {
  margin: 0;
  font-size: 0.82rem;
  color: var(--c-texto-sec);
}

.barra-acciones__botones {
  display: flex;
  flex-direction: column-reverse;
  gap: 0.45rem;
}

/* ---------- Paginación ---------- */
.paginacion {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-top: 0.9rem;
  font-size: 0.84rem;
  font-weight: 600;
}

/* ---------- Diálogo ---------- */
.dialogo {
  width: min(92vw, 26rem);
  padding: 0;
  border: 1px solid var(--c-borde-fuerte);
  border-radius: 10px;
  color: var(--c-texto);
  font-family: var(--fuente);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.18);
}

.dialogo::backdrop {
  background: rgba(15, 23, 42, 0.45);
}

.dialogo__contenido {
  padding: 1.15rem;
}

.dialogo h2 {
  margin: 0 0 0.45rem;
  font-size: 1.05rem;
}

.dialogo p {
  margin: 0 0 1rem;
  font-size: 0.86rem;
  color: var(--c-texto-sec);
}

.dialogo__acciones {
  display: flex;
  flex-direction: column-reverse;
  gap: 0.45rem;
}

/* ---------- Móviles (< 767px) ---------- */
@media (max-width: 767px) {
  .tabla--listado thead {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
  }

  .tabla--listado,
  .tabla--listado tbody {
    display: block;
  }

  .tabla-scroll:has(.tabla--listado) {
    border: 0;
    background: transparent;
    overflow: visible;
  }

  .tabla--listado tr {
    display: block;
    margin-bottom: 0.7rem;
    border: 1px solid var(--c-borde-fuerte);
    border-radius: 8px;
    background: var(--c-superficie);
  }

  .tabla--listado td {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding: 0.55rem 0.75rem;
    border-bottom: 1px solid var(--c-borde);
  }

  .tabla--listado td::before {
    content: attr(data-label);
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--c-texto-sec);
  }

  .tabla--listado td:last-child {
    border-bottom: 0;
  }
}

/* ---------- Tablets (768px - 1024px) ---------- */
@media (min-width: 768px) {
  .pedidos-sector {
    padding: 1.25rem 1.5rem;
  }

  .encabezado {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .filtros-top {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .filtros-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .tarjetas {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .detalle__cabecera {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .agregar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .barra-acciones__pie {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .barra-acciones__botones,
  .dialogo__acciones {
    flex-direction: row;
    justify-content: flex-end;
  }
}

/* ---------- Escritorio (> 1025px) ---------- */
@media (min-width: 1025px) {
  .filtros-grid {
    grid-template-columns: repeat(5, minmax(0, 1fr)) auto;
  }

  .filtros-acciones .btn--compacto {
    flex: 0 0 auto;
  }
}
</style>
