<script setup>
import { computed, onMounted, ref } from 'vue'

import { normalizeApiError } from '@/services/api/error-handler'
import ApiErrorMessage from '@/modules/shared/components/ApiErrorMessage.vue'
import {
  listarCupos,
  crearCupo,
  actualizarCupo,
  eliminarCupo,
  listarSectoresCupos,
} from '../services/cupos'

const COMIDAS = [
  { idTipoComida: 1, label: 'Desayuno', inicial: 'D' },
  { idTipoComida: 2, label: 'Almuerzo', inicial: 'A' },
  { idTipoComida: 3, label: 'Merienda', inicial: 'M' },
  { idTipoComida: 4, label: 'Cena', inicial: 'C' },
]

// Filtros, búsqueda, orden y paginación
const consultaBusqueda = ref('')
const filtroSector = ref('')
const filtroComida = ref('')
const ordenSector = ref('asc')
const page = ref(1)
const perPage = ref(25)
const totalItems = ref(0)

// Datos y estados
const cuposLista = ref([])
const sectoresActivos = ref([])
const sectoresTodos = ref([])
const loadingLista = ref(false)
const guardando = ref(false)
const eliminandoId = ref(null)
const cupoConfirmarEliminarId = ref(null)

const apiErrorMessage = ref(null)
const retryOperation = ref(null)
const mensajeExito = ref('')

// Formulario crear / editar
const editandoId = ref(null)
const formSectorId = ref('')
const formComidaId = ref('')
const formCantidad = ref('')
const formError = ref('')

const totalPaginas = computed(() => {
  if (!perPage.value) return 1
  return Math.max(1, Math.ceil(totalItems.value / perPage.value))
})

const mapaSectores = computed(() => {
  const map = new Map()
  for (const s of sectoresTodos.value) {
    const id = Number(s.id ?? s.idSector)
    if (id) map.set(id, s)
  }
  for (const s of sectoresActivos.value) {
    const id = Number(s.id ?? s.idSector)
    if (id && !map.has(id)) map.set(id, s)
  }
  return map
})

function normalizarTexto(valor) {
  return String(valor ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}

function nombreSector(idSector) {
  const sec = mapaSectores.value.get(Number(idSector))
  return sec?.nombre ?? `Sector #${idSector}`
}

function esSectorActivo(idSector) {
  const sec = mapaSectores.value.get(Number(idSector))
  if (!sec) return true
  if (typeof sec.estado === 'string') {
    return sec.estado.toLowerCase() === 'activo'
  }
  return Boolean(sec.isActive ?? sec.activo ?? true)
}

function labelComida(idTipoComida) {
  const item = COMIDAS.find((c) => c.idTipoComida === Number(idTipoComida))
  return item ? item.label : `Comida #${idTipoComida}`
}

const cuposFiltrados = computed(() => {
  const q = normalizarTexto(consultaBusqueda.value.trim())
  if (!q) return cuposLista.value
  return cuposLista.value.filter((cupo) => {
    const texto = [
      `#${cupo.idCupo}`,
      String(cupo.idCupo),
      nombreSector(cupo.idSector),
      labelComida(cupo.idTipoComida),
      `${cupo.cantComensales} comensales`,
    ].join(' ')
    return normalizarTexto(texto).includes(q)
  })
})

async function cargarSectores() {
  try {
    const [activos, todos] = await Promise.all([
      listarSectoresCupos('activo'),
      listarSectoresCupos('todos').catch(() => []),
    ])
    sectoresActivos.value = activos
    sectoresTodos.value = todos.length > 0 ? todos : activos
  } catch {
    // Si falla el catálogo de sectores, la tabla igual muestra los IDs
  }
}

async function cargarCupos(paginaDestino = 1) {
  loadingLista.value = true
  apiErrorMessage.value = null
  retryOperation.value = null
  page.value = paginaDestino

  const params = {
    page: paginaDestino,
    orden: ordenSector.value,
  }
  if (filtroSector.value) params.sector = Number(filtroSector.value)
  if (filtroComida.value) params.tipo_comida = Number(filtroComida.value)

  try {
    const data = await listarCupos(params)
    cuposLista.value = data.items
    totalItems.value = data.total
    perPage.value = data.per_page || 25
  } catch (error) {
    const normalizado = normalizeApiError(error)
    apiErrorMessage.value = normalizado
    if (normalizado.canRetry) {
      retryOperation.value = () => cargarCupos(paginaDestino)
    }
  } finally {
    loadingLista.value = false
  }
}

onMounted(async () => {
  await Promise.all([cargarSectores(), cargarCupos(1)])
})

function aplicarFiltros() {
  mensajeExito.value = ''
  cargarCupos(1)
}

function limpiarFiltros() {
  consultaBusqueda.value = ''
  filtroSector.value = ''
  filtroComida.value = ''
  ordenSector.value = 'asc'
  mensajeExito.value = ''
  cargarCupos(1)
}

function alternarOrdenSector() {
  ordenSector.value = ordenSector.value === 'asc' ? 'desc' : 'asc'
  cargarCupos(1)
}

function resetFormulario() {
  editandoId.value = null
  formSectorId.value = ''
  formComidaId.value = ''
  formCantidad.value = ''
  formError.value = ''
}

function prepararEdicion(cupo) {
  mensajeExito.value = ''
  apiErrorMessage.value = null
  formError.value = ''
  cupoConfirmarEliminarId.value = null

  editandoId.value = cupo.idCupo
  formSectorId.value = String(cupo.idSector)
  formComidaId.value = String(cupo.idTipoComida)
  formCantidad.value = String(cupo.cantComensales)
}

function validarFormularioCupo() {
  formError.value = ''

  const idSector = Number(formSectorId.value)
  const idTipoComida = Number(formComidaId.value)
  const cantComensales = Number(formCantidad.value)

  if (!formSectorId.value || Number.isNaN(idSector) || idSector <= 0) {
    formError.value = 'Seleccioná un sector válido.'
    return null
  }

  if (!editandoId.value && !esSectorActivo(idSector)) {
    formError.value = 'No se puede crear un cupo para un sector inactivo.'
    return null
  }

  if (!formComidaId.value || Number.isNaN(idTipoComida) || idTipoComida <= 0) {
    formError.value = 'Seleccioná un tipo de comida.'
    return null
  }

  if (
    formCantidad.value === '' ||
    !Number.isInteger(cantComensales) ||
    cantComensales <= 0
  ) {
    formError.value = 'La cantidad de comensales debe ser un entero mayor a cero.'
    return null
  }

  return { idSector, idTipoComida, cantComensales }
}

async function guardarCupo() {
  if (guardando.value) return
  apiErrorMessage.value = null
  mensajeExito.value = ''

  const payload = validarFormularioCupo()
  if (!payload) return

  guardando.value = true
  try {
    if (editandoId.value !== null) {
      await actualizarCupo(editandoId.value, payload)
      mensajeExito.value = `Cupo #${editandoId.value} actualizado (aplica a pedidos posteriores).`
    } else {
      const creado = await crearCupo(payload)
      mensajeExito.value = `Cupo #${creado.idCupo ?? ''} creado correctamente.`
    }
    resetFormulario()
    await cargarCupos(page.value)
  } catch (error) {
    const status = error?.response?.status
    const detalleServidor =
      error?.response?.data?.error ||
      error?.response?.data?.message ||
      error?.response?.data?.description

    if (status === 409) {
      formError.value =
        detalleServidor ||
        'Ya existe un cupo vigente para ese sector y tipo de comida.'
    } else if (status === 400) {
      formError.value = detalleServidor || 'Datos inválidos para el cupo.'
    } else {
      apiErrorMessage.value = normalizeApiError(error)
    }
  } finally {
    guardando.value = false
  }
}

function solicitarEliminarCupo(idCupo) {
  mensajeExito.value = ''
  apiErrorMessage.value = null
  cupoConfirmarEliminarId.value = idCupo
}

async function confirmarEliminarCupo(idCupo) {
  if (eliminandoId.value !== null) return
  eliminandoId.value = idCupo
  apiErrorMessage.value = null
  mensajeExito.value = ''

  try {
    await eliminarCupo(idCupo)
    cupoConfirmarEliminarId.value = null
    if (editandoId.value === idCupo) {
      resetFormulario()
    }
    mensajeExito.value = `Cupo #${idCupo} dado de baja correctamente.`
    const nuevaPagina =
      cuposLista.value.length === 1 && page.value > 1
        ? page.value - 1
        : page.value
    await cargarCupos(nuevaPagina)
  } catch (error) {
    cupoConfirmarEliminarId.value = null
    apiErrorMessage.value = normalizeApiError(error)
  } finally {
    eliminandoId.value = null
  }
}
</script>

<template>
  <div class="vista-cupos">
    <!-- Espacio reservado para la barra de navegación del layout -->
    <slot name="navbar" />

    <main class="cupos-container" aria-labelledby="titulo-cupos">
      <header class="cupos-header">
        <div>
          <p class="cupos-rol">Servicio de Alimentación</p>
          <h1 id="titulo-cupos">Cupos por sector y comida</h1>
          <p class="cupos-subtitulo">
            Define el límite de solicitudes regulares por sector y comida (independiente del menú).
          </p>
        </div>
        <div class="header-acciones">
          <RouterLink class="btn btn--secundario" to="/inicio/servicio-alimentacion">
            Volver a autorizaciones
          </RouterLink>
        </div>
      </header>

      <p v-if="mensajeExito" class="mensaje-exito" role="status">
        <span>{{ mensajeExito }}</span>
        <button type="button" class="btn-texto" @click="mensajeExito = ''">Cerrar</button>
      </p>

      <ApiErrorMessage :error="apiErrorMessage" @retry="retryOperation" />

      <!-- Formulario crear / editar -->
      <section class="panel" aria-labelledby="titulo-form-cupo">
        <div class="panel-cabecera">
          <h2 id="titulo-form-cupo">
            {{ editandoId !== null ? `Editar cupo #${editandoId}` : 'Nuevo cupo' }}
          </h2>
          <span v-if="editandoId !== null" class="badge-edicion">Modo edición</span>
        </div>

        <form class="form-grid" @submit.prevent="guardarCupo" novalidate>
          <div class="form-field">
            <label for="form-sector">Sector *</label>
            <select
              id="form-sector"
              v-model="formSectorId"
              :disabled="guardando || sectoresActivos.length === 0"
            >
              <option value="">Seleccioná un sector activo...</option>
              <option
                v-for="sec in sectoresActivos"
                :key="sec.id ?? sec.idSector"
                :value="sec.id ?? sec.idSector"
              >
                {{ sec.nombre }}
              </option>
            </select>
          </div>

          <div class="form-field">
            <label for="form-comida">Tipo de comida *</label>
            <select
              id="form-comida"
              v-model="formComidaId"
              :disabled="guardando"
            >
              <option value="">Seleccioná comida...</option>
              <option
                v-for="c in COMIDAS"
                :key="c.idTipoComida"
                :value="c.idTipoComida"
              >
                {{ c.label }}
              </option>
            </select>
          </div>

          <div class="form-field">
            <label for="form-cantidad">Cantidad de comensales *</label>
            <input
              id="form-cantidad"
              v-model="formCantidad"
              type="number"
              min="1"
              step="1"
              placeholder="Ej: 10"
              :disabled="guardando"
            />
          </div>

          <div class="form-acciones">
            <button type="submit" class="btn btn--primario btn--compacto" :disabled="guardando">
              <svg class="icono-btn" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5l3.5 3.5 7.5-8" />
              </svg>
              <span>
                {{
                  guardando
                    ? 'Guardando...'
                    : editandoId !== null
                      ? 'Guardar cambios'
                      : 'Crear cupo'
                }}
              </span>
            </button>
            <button
              v-if="editandoId !== null || formSectorId || formComidaId || formCantidad"
              type="button"
              class="btn btn--secundario btn--compacto"
              :disabled="guardando"
              @click="resetFormulario"
            >
              Cancelar
            </button>
          </div>
        </form>

        <p v-if="formError" class="field-error" role="alert">
          {{ formError }}
        </p>
      </section>

      <!-- Filtros compactos en una fila -->
      <section class="panel" aria-labelledby="titulo-filtros-cupos">
        <div class="filtros-top">
          <h2 id="titulo-filtros-cupos">Filtros y búsqueda</h2>

          <div class="barra-busqueda">
            <label for="buscar-cupo" class="visualmente-oculto">
              Buscar cupo por sector, comida o número
            </label>
            <svg class="barra-busqueda__lupa" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <circle cx="9" cy="9" r="6" />
              <path stroke-linecap="round" d="m13.5 13.5 4 4" />
            </svg>
            <input
              id="buscar-cupo"
              v-model="consultaBusqueda"
              type="search"
              placeholder="Buscar sector, comida o #ID..."
              :disabled="loadingLista"
            />
            <button
              v-if="consultaBusqueda"
              type="button"
              class="barra-busqueda__limpiar"
              aria-label="Borrar búsqueda"
              title="Borrar búsqueda"
              @click="consultaBusqueda = ''"
            >
              ×
            </button>
          </div>
        </div>

        <form class="filtros-grid" @submit.prevent="aplicarFiltros">
          <div class="form-field">
            <label for="filtro-sector">Sector</label>
            <select
              id="filtro-sector"
              v-model="filtroSector"
              :disabled="loadingLista"
            >
              <option value="">Todos los sectores</option>
              <option
                v-for="sec in sectoresTodos"
                :key="sec.id ?? sec.idSector"
                :value="sec.id ?? sec.idSector"
              >
                {{ sec.nombre }}
              </option>
            </select>
          </div>

          <div class="form-field">
            <label for="filtro-comida">Tipo de comida</label>
            <select
              id="filtro-comida"
              v-model="filtroComida"
              :disabled="loadingLista"
            >
              <option value="">Todas las comidas</option>
              <option
                v-for="c in COMIDAS"
                :key="c.idTipoComida"
                :value="c.idTipoComida"
              >
                {{ c.label }}
              </option>
            </select>
          </div>

          <div class="filtros-botones">
            <button type="submit" class="btn btn--primario btn--compacto" :disabled="loadingLista">
              <svg class="icono-btn" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <circle cx="9" cy="9" r="5.5" />
                <path stroke-linecap="round" d="m13.2 13.2 3.8 3.8" />
              </svg>
              <span>Buscar</span>
            </button>
            <button
              type="button"
              class="btn btn--secundario btn--compacto"
              :disabled="loadingLista"
              @click="limpiarFiltros"
            >
              Limpiar
            </button>
          </div>
        </form>
      </section>

      <!-- Listado de cupos -->
      <section class="panel" aria-labelledby="titulo-listado-cupos" :aria-busy="loadingLista">
        <div class="panel-cabecera">
          <h2 id="titulo-listado-cupos">Cupos vigentes ({{ totalItems }})</h2>
          <button
            type="button"
            class="btn btn--secundario btn--compacto"
            :disabled="loadingLista"
            @click="alternarOrdenSector"
          >
            <svg class="icono-btn" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 4v12M6 16l-2.5-2.5M6 16l2.5-2.5M14 16V4M14 4l-2.5 2.5M14 4l2.5 2.5" />
            </svg>
            <span>Sector: {{ ordenSector === 'asc' ? 'A → Z' : 'Z → A' }}</span>
          </button>
        </div>

        <p v-if="loadingLista" class="estado-info" role="status">
          Cargando cupos...
        </p>

        <p v-else-if="cuposFiltrados.length === 0" class="estado-info" role="status">
          No hay cupos registrados para los filtros o búsqueda seleccionados.
        </p>

        <div v-else class="tabla-scroll">
          <table class="tabla-cupos">
            <caption class="visualmente-oculto">Listado de cupos vigentes por sector y comida</caption>
            <thead>
              <tr>
                <th scope="col">ID</th>
                <th scope="col">Sector</th>
                <th scope="col">Tipo de comida</th>
                <th scope="col" class="num">Cantidad máxima (Regular)</th>
                <th scope="col">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="cupo in cuposFiltrados"
                :key="cupo.idCupo"
                :class="{ 'fila--editando': editandoId === cupo.idCupo }"
              >
                <td data-label="ID"><strong>#{{ cupo.idCupo }}</strong></td>
                <td data-label="Sector">{{ nombreSector(cupo.idSector) }}</td>
                <td data-label="Tipo de comida">
                  <span class="chip-comida">{{ labelComida(cupo.idTipoComida) }}</span>
                </td>
                <td data-label="Cantidad máxima (Regular)" class="num">
                  <strong>{{ cupo.cantComensales }}</strong> comensales
                </td>
                <td data-label="Acciones">
                  <div class="acciones-fila">
                    <button
                      type="button"
                      class="btn-icono btn-icono--editar"
                      :aria-label="`Editar cupo #${cupo.idCupo} de ${nombreSector(cupo.idSector)} (${labelComida(cupo.idTipoComida)})`"
                      title="Editar cupo"
                      :disabled="guardando || eliminandoId !== null"
                      @click="prepararEdicion(cupo)"
                    >
                      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m13.8 3.2 3 3-9.8 9.8H4v-3l9.8-9.8Z" />
                      </svg>
                      <span>Editar</span>
                    </button>

                    <button
                      type="button"
                      class="btn-icono btn-icono--eliminar"
                      :aria-label="`Eliminar cupo #${cupo.idCupo} de ${nombreSector(cupo.idSector)} (${labelComida(cupo.idTipoComida)})`"
                      title="Eliminar cupo"
                      :disabled="guardando || eliminandoId !== null"
                      @click="solicitarEliminarCupo(cupo.idCupo)"
                    >
                      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" d="M3.5 5.5h13M8 5.5V4h4v1.5M6 5.5l.7 10.5h6.6l.7-10.5" />
                      </svg>
                      <span>Eliminar</span>
                    </button>
                  </div>

                  <div
                    v-if="cupoConfirmarEliminarId === cupo.idCupo"
                    class="confirmacion-eliminar"
                    role="alert"
                  >
                    <span>¿Dar de baja el cupo #{{ cupo.idCupo }}?</span>
                    <div class="confirmacion-eliminar__botones">
                      <button
                        type="button"
                        class="btn-eliminar-confirmar"
                        :disabled="eliminandoId === cupo.idCupo"
                        @click="confirmarEliminarCupo(cupo.idCupo)"
                      >
                        {{ eliminandoId === cupo.idCupo ? 'Eliminando...' : 'Sí, eliminar' }}
                      </button>
                      <button
                        type="button"
                        class="btn-cancelar-mini"
                        :disabled="eliminandoId === cupo.idCupo"
                        @click="cupoConfirmarEliminarId = null"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <nav
          v-if="totalPaginas > 1"
          class="paginacion"
          aria-label="Paginación de cupos"
        >
          <button
            type="button"
            class="btn btn--secundario btn--compacto"
            :disabled="loadingLista || page <= 1"
            @click="cargarCupos(page - 1)"
          >
            Anterior
          </button>
          <span>Página {{ page }} de {{ totalPaginas }}</span>
          <button
            type="button"
            class="btn btn--secundario btn--compacto"
            :disabled="loadingLista || page >= totalPaginas"
            @click="cargarCupos(page + 1)"
          >
            Siguiente
          </button>
        </nav>
      </section>
    </main>
  </div>
</template>

<style scoped>
.vista-cupos {
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
  --c-rojo-texto: #b91c1c;
  --c-rojo-suave: #fef2f2;
  --c-rojo-borde: #fecaca;

  font-family: var(--fuente);
  color: var(--c-texto);
  -webkit-font-smoothing: antialiased;
}

.cupos-container {
  max-width: 1180px;
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
.cupos-header {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 0.9rem;
}

.cupos-rol {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--c-primario);
}

.cupos-header h1 {
  margin: 0.15rem 0 0;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.cupos-subtitulo {
  margin: 0.25rem 0 0;
  color: var(--c-texto-sec);
  font-size: 0.875rem;
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

.panel-cabecera {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.8rem;
}

.badge-edicion {
  padding: 0.18rem 0.55rem;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  background-color: var(--c-primario-suave);
  color: var(--c-primario-hover);
  font-size: 0.75rem;
  font-weight: 700;
}

/* ---------- Formularios y filtros ---------- */
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
  max-width: 380px;
}

.barra-busqueda__lupa {
  position: absolute;
  left: 0.75rem;
  width: 15px;
  height: 15px;
  color: var(--c-texto-sec);
  pointer-events: none;
}

.barra-busqueda input[type='search'] {
  width: 100%;
  height: 36px;
  min-height: 36px;
  padding: 0.3rem 2rem 0.3rem 2.15rem;
  border: 1px solid var(--c-borde-fuerte);
  border-radius: 999px;
  background-color: var(--c-fondo);
  color: var(--c-texto);
  font-family: var(--fuente);
  font-size: 0.84rem;
  box-sizing: border-box;
}

.barra-busqueda input[type='search']:focus {
  outline: none;
  background-color: var(--c-superficie);
  border-color: var(--c-primario);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.barra-busqueda__limpiar {
  position: absolute;
  right: 0.5rem;
  width: 22px;
  height: 22px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--c-texto-sec);
  font-size: 0.95rem;
  line-height: 1;
  cursor: pointer;
}

.barra-busqueda__limpiar:hover {
  background-color: var(--c-borde);
  color: var(--c-texto);
}

.form-grid,
.filtros-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.75rem;
  align-items: end;
}

.form-grid > *,
.filtros-grid > *,
.form-field,
.form-acciones,
.filtros-botones {
  min-width: 0;
  max-width: 100%;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--c-texto-sec);
}

input[type='number'],
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

input:disabled,
select:disabled {
  background-color: var(--c-fondo);
  color: var(--c-texto-sec);
}

.form-acciones,
.filtros-botones {
  display: flex;
  flex-wrap: nowrap;
  gap: 0.45rem;
  align-items: center;
}

.form-acciones .btn--compacto,
.filtros-botones .btn--compacto {
  flex: 1 1 0;
  min-width: 0;
}

/* ---------- Botones ---------- */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  min-height: 38px;
  padding: 0.4rem 0.85rem;
  border: 1px solid var(--c-borde-fuerte);
  border-radius: 7px;
  background-color: var(--c-superficie);
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
  background-color: var(--c-fondo);
}

.btn--primario {
  border-color: var(--c-primario);
  background-color: var(--c-primario);
  color: #ffffff;
}

.btn--primario:hover:not(:disabled) {
  background-color: var(--c-primario-hover);
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
  background-color: var(--c-superficie);
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

.btn-icono--editar {
  border-color: #bfdbfe;
  background-color: var(--c-primario-suave);
  color: var(--c-primario-hover);
}

.btn-icono--editar:hover:not(:disabled) {
  border-color: var(--c-primario);
  background-color: #dbeafe;
}

.btn-icono--eliminar {
  border-color: var(--c-rojo-borde);
  background-color: var(--c-rojo-suave);
  color: var(--c-rojo-texto);
}

.btn-icono--eliminar:hover:not(:disabled) {
  border-color: #f87171;
  background-color: #fee2e2;
}

.btn-texto {
  padding: 0.1rem 0.25rem;
  border: 0;
  background: transparent;
  color: var(--c-verde-texto);
  font-family: var(--fuente);
  font-size: 0.78rem;
  font-weight: 700;
  text-decoration: underline;
  cursor: pointer;
}

/* ---------- Tabla y chips ---------- */
.tabla-scroll {
  width: 100%;
  overflow-x: auto;
  border: 1px solid var(--c-borde);
  border-radius: 8px;
  background-color: var(--c-superficie);
}

.tabla-cupos {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}

.tabla-cupos th,
.tabla-cupos td {
  padding: 0.55rem 0.65rem;
  border-bottom: 1px solid var(--c-borde);
  text-align: left;
  vertical-align: middle;
}

.tabla-cupos thead th {
  background-color: var(--c-fondo);
  color: var(--c-texto-sec);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.tabla-cupos tbody tr:hover {
  background-color: #f8fafc;
}

.tabla-cupos tbody tr:last-child td {
  border-bottom: 0;
}

.fila--editando {
  background-color: var(--c-primario-suave) !important;
  box-shadow: inset 3px 0 0 var(--c-primario);
}

.num {
  text-align: right !important;
  font-variant-numeric: tabular-nums;
}

.chip-comida {
  display: inline-flex;
  align-items: center;
  padding: 0.16rem 0.5rem;
  border: 1px solid var(--c-borde);
  border-radius: 6px;
  background-color: var(--c-fondo);
  font-size: 0.78rem;
  font-weight: 600;
}

.acciones-fila {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
}

.confirmacion-eliminar {
  margin-top: 0.45rem;
  padding: 0.5rem 0.65rem;
  border-radius: 7px;
  background-color: var(--c-rojo-suave);
  border: 1px solid var(--c-rojo-borde);
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--c-rojo-texto);
}

.confirmacion-eliminar__botones {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.btn-eliminar-confirmar {
  height: 28px;
  padding: 0 0.6rem;
  border: 0;
  border-radius: 6px;
  background-color: var(--c-rojo-texto);
  color: #ffffff;
  font-family: var(--fuente);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-cancelar-mini {
  height: 28px;
  padding: 0 0.6rem;
  border: 1px solid var(--c-borde-fuerte);
  border-radius: 6px;
  background-color: var(--c-superficie);
  color: var(--c-texto);
  font-family: var(--fuente);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
}

.paginacion {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.9rem;
  font-size: 0.84rem;
  font-weight: 600;
}

button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.mensaje-exito {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.65rem 0.9rem;
  border-radius: 8px;
  margin-bottom: 0.9rem;
  font-size: 0.85rem;
  font-weight: 600;
  background-color: var(--c-verde-suave);
  border: 1px solid var(--c-verde-borde);
  color: var(--c-verde-texto);
}

.estado-info {
  padding: 1.25rem 1rem;
  border: 1px dashed var(--c-borde-fuerte);
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  background-color: var(--c-fondo);
  color: var(--c-texto-sec);
  text-align: center;
  margin: 0;
}

.field-error {
  margin: 0.5rem 0 0;
  color: var(--c-rojo-texto);
  font-size: 0.78rem;
  font-weight: 600;
}

/* ---------- Móviles (< 767px) ---------- */
@media (max-width: 767px) {
  .tabla-cupos thead {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
  }

  .tabla-cupos,
  .tabla-cupos tbody {
    display: block;
  }

  .tabla-scroll:has(.tabla-cupos) {
    border: 0;
    background: transparent;
    overflow: visible;
  }

  .tabla-cupos tr {
    display: block;
    margin-bottom: 0.7rem;
    border: 1px solid var(--c-borde-fuerte);
    border-radius: 8px;
    background-color: var(--c-superficie);
  }

  .tabla-cupos td {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding: 0.55rem 0.75rem;
    border-bottom: 1px solid var(--c-borde);
    text-align: left !important;
  }

  .tabla-cupos td::before {
    content: attr(data-label);
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--c-texto-sec);
  }

  .tabla-cupos td:last-child {
    border-bottom: 0;
  }
}

/* ---------- Tablets (768px - 1024px) ---------- */
@media (min-width: 768px) {
  .cupos-container {
    padding: 1.25rem 1.5rem;
  }

  .cupos-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }

  .filtros-top {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .form-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .filtros-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr)) auto;
  }
}

/* ---------- Escritorio (> 1025px) ---------- */
@media (min-width: 1025px) {
  .form-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
  }

  .filtros-grid {
    grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr) auto;
  }

  .form-acciones .btn--compacto,
  .filtros-botones .btn--compacto {
    flex: 0 0 auto;
  }
}
</style>
