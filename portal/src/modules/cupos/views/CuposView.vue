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
  { idTipoComida: 1, label: 'Desayuno' },
  { idTipoComida: 2, label: 'Almuerzo' },
  { idTipoComida: 3, label: 'Merienda' },
  { idTipoComida: 4, label: 'Cena' },
]

// Filtros, orden y paginación
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
  <main class="cupos-container" aria-labelledby="titulo-cupos">
    <header class="cupos-header">
      <div>
        <h1 id="titulo-cupos">Cupos por sector y comida</h1>
        <p class="cupos-subtitulo">
          Define el límite de solicitudes regulares por sector y comida (independiente del menú).
        </p>
      </div>
      <RouterLink class="btn-secundario" to="/inicio/servicio-alimentacion">
        Volver a autorizaciones
      </RouterLink>
    </header>

    <p v-if="mensajeExito" class="mensaje-exito" role="status">
      {{ mensajeExito }}
    </p>

    <ApiErrorMessage :error="apiErrorMessage" @retry="retryOperation" />

    <!-- Formulario crear / editar -->
    <section class="panel" aria-labelledby="titulo-form-cupo">
      <h2 id="titulo-form-cupo">
        {{ editandoId !== null ? `Editar cupo #${editandoId}` : 'Nuevo cupo' }}
      </h2>

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
          <button type="submit" class="btn-principal" :disabled="guardando">
            {{
              guardando
                ? 'Guardando...'
                : editandoId !== null
                  ? 'Guardar cambios'
                  : 'Crear cupo'
            }}
          </button>
          <button
            v-if="editandoId !== null || formSectorId || formComidaId || formCantidad"
            type="button"
            class="btn-secundario"
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

    <!-- Filtros -->
    <section class="panel" aria-labelledby="titulo-filtros-cupos">
      <h2 id="titulo-filtros-cupos">Filtros y búsqueda</h2>
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

    <!-- Listado de cupos -->
    <section class="panel" aria-labelledby="titulo-listado-cupos">
      <div class="panel-cabecera">
        <h2 id="titulo-listado-cupos">Cupos vigentes ({{ totalItems }})</h2>
        <button
          type="button"
          class="btn-secundario"
          :disabled="loadingLista"
          @click="alternarOrdenSector"
        >
          Ordenar por sector:
          {{ ordenSector === 'asc' ? 'A → Z' : 'Z → A' }}
        </button>
      </div>

      <p v-if="loadingLista" class="estado-info" role="status">
        Cargando cupos...
      </p>

      <p v-else-if="cuposLista.length === 0" class="estado-info" role="status">
        No hay cupos registrados para los filtros seleccionados.
      </p>

      <div v-else class="tabla-scroll">
        <table class="tabla-cupos">
          <thead>
            <tr>
              <th scope="col">ID</th>
              <th scope="col">Sector</th>
              <th scope="col">Tipo de comida</th>
              <th scope="col">Cantidad máxima (Regular)</th>
              <th scope="col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cupo in cuposLista" :key="cupo.idCupo">
              <td><strong>#{{ cupo.idCupo }}</strong></td>
              <td>{{ nombreSector(cupo.idSector) }}</td>
              <td>{{ labelComida(cupo.idTipoComida) }}</td>
              <td><strong>{{ cupo.cantComensales }}</strong> comensales</td>
              <td>
                <div class="acciones-fila">
                  <button
                    type="button"
                    class="btn-accion btn-editar"
                    :disabled="guardando || eliminandoId !== null"
                    @click="prepararEdicion(cupo)"
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    class="btn-accion btn-eliminar"
                    :disabled="guardando || eliminandoId !== null"
                    @click="solicitarEliminarCupo(cupo.idCupo)"
                  >
                    Eliminar
                  </button>
                </div>

                <div
                  v-if="cupoConfirmarEliminarId === cupo.idCupo"
                  class="confirmacion-eliminar"
                  role="alert"
                >
                  <span>¿Dar de baja el cupo #{{ cupo.idCupo }}?</span>
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
          class="btn-secundario"
          :disabled="loadingLista || page <= 1"
          @click="cargarCupos(page - 1)"
        >
          Anterior
        </button>
        <span>Página {{ page }} de {{ totalPaginas }}</span>
        <button
          type="button"
          class="btn-secundario"
          :disabled="loadingLista || page >= totalPaginas"
          @click="cargarCupos(page + 1)"
        >
          Siguiente
        </button>
      </nav>
    </section>
  </main>
</template>

<style scoped>
.cupos-container {
  max-width: 1120px;
  margin: 0 auto;
  padding: 16px;
  color: #1f2937;
}

.cupos-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 18px;
}

.cupos-header h1 {
  margin: 0;
  color: #1d4ed8;
}

.cupos-subtitulo {
  margin: 4px 0 0;
  color: #4b5563;
  font-size: 14px;
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
  gap: 10px;
  margin-bottom: 14px;
}

.panel-cabecera h2 {
  margin: 0;
}

.form-grid,
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

input[type='number'],
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

.form-acciones,
.filtros-botones {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.tabla-scroll {
  overflow-x: auto;
}

.tabla-cupos {
  width: 100%;
  border-collapse: collapse;
}

.tabla-cupos th,
.tabla-cupos td {
  padding: 10px 8px;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
  font-size: 14px;
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

.field-error {
  margin: 10px 0 0;
  color: #c62828;
  font-size: 14px;
}

@media (min-width: 768px) {
  .cupos-container {
    padding: 24px;
  }

  .cupos-header,
  .panel-cabecera {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }

  .form-grid {
    grid-template-columns: repeat(4, 1fr);
  }

  .filtros-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
