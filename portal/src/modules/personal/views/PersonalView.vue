<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import ApiErrorMessage from '@/modules/shared/components/ApiErrorMessage.vue'
import { normalizeApiError } from '@/services/api/error-handler'
import {
  eliminarPersona,
  listarPersonal,
  listarTiposMenu,
  listarTiposPersonal,
} from '../services/personal'
import ModalFormularioPersonal from '../components/ModalFormularioPersonal.vue'
import BuscadorResidentes from '../components/BuscadorResidentes.vue'

const authStore = useAuthStore()

const tiposMenu = ref([])
const tiposPersonal = ref([])
const personal = ref([])

const cargandoCatalogos = ref(false)
const cargandoLista = ref(false)
const eliminando = ref(false)

const apiError = ref(null)
const mensajeExito = ref('')
const errorFiltroDni = ref('')

const filtros = reactive({
  q: '',
  dni: '',
  estado: 'activos',
})

const paginacion = reactive({
  page: 1,
  per_page: 10,
  total: 0,
  pages: 1,
})

const modalFormAbierto = ref(false)
const personaSeleccionada = ref(null)
const personaConfirmarBaja = ref(null)

const tiposMenuMap = computed(() =>
  Object.fromEntries(tiposMenu.value.map((m) => [m.id, m.nombre]))
)

const idTipoPersonalFijo = computed(() => {
  const encontrado = tiposPersonal.value.find((t) =>
    t.nombre.toLowerCase().includes('fijo')
  )
  return encontrado?.id ?? 1
})

const idTipoResidente = computed(() => {
  const encontrado = tiposPersonal.value.find((t) =>
    t.nombre.toLowerCase().includes('residente')
  )
  return encontrado?.id ?? 2
})

const nombreSectorActual = computed(() => {
  const primeraConSector = personal.value.find((p) => p.sector?.nombre)
  if (primeraConSector) {
    return primeraConSector.sector.nombre
  }
  return authStore.user?.sector?.nombre ?? ''
})

function validarFiltroDni() {
  const valor = filtros.dni.trim()
  if (valor && !/^\d+$/.test(valor)) {
    errorFiltroDni.value = 'El DNI de búsqueda debe contener solo números.'
    return false
  }
  errorFiltroDni.value = ''
  return true
}

async function cargarCatalogos() {
  cargandoCatalogos.value = true
  try {
    const [menus, tipos] = await Promise.all([
      listarTiposMenu(),
      listarTiposPersonal(),
    ])
    tiposMenu.value = menus ?? []
    tiposPersonal.value = tipos ?? []
  } catch (error) {
    apiError.value = normalizeApiError(error)
  } finally {
    cargandoCatalogos.value = false
  }
}

async function cargarPersonalSector(pagina = 1) {
  if (!validarFiltroDni()) {
    return
  }

  cargandoLista.value = true
  apiError.value = null

  try {
    const data = await listarPersonal({
      q: filtros.q.trim(),
      dni: filtros.dni.trim(),
      estado: filtros.estado,
      id_tipo_personal: idTipoPersonalFijo.value,
      page: pagina,
      per_page: paginacion.per_page,
    })

    personal.value = data.items ?? []
    paginacion.page = data.page ?? 1
    paginacion.total = data.total ?? 0
    paginacion.pages = data.pages ?? 1
  } catch (error) {
    apiError.value = normalizeApiError(error)
  } finally {
    cargandoLista.value = false
  }
}

function limpiarFiltros() {
  filtros.q = ''
  filtros.dni = ''
  filtros.estado = 'activos'
  errorFiltroDni.value = ''
  cargarPersonalSector(1)
}

function abrirModalAlta() {
  mensajeExito.value = ''
  personaSeleccionada.value = null
  modalFormAbierto.value = true
}

function abrirModalEdicion(persona) {
  mensajeExito.value = ''
  personaSeleccionada.value = persona
  modalFormAbierto.value = true
}

function alGuardarPersona() {
  const eraEdicion = Boolean(personaSeleccionada.value)
  modalFormAbierto.value = false
  personaSeleccionada.value = null
  mensajeExito.value = eraEdicion
    ? 'Los datos de la persona se actualizaron correctamente.'
    : 'La persona fue agregada al sector correctamente.'
  cargarPersonalSector(paginacion.page)
}

function solicitarConfirmacionBaja(persona) {
  mensajeExito.value = ''
  personaConfirmarBaja.value = persona
}

async function confirmarBajaPersona() {
  if (!personaConfirmarBaja.value) return

  eliminando.value = true
  apiError.value = null

  try {
    const respuesta = await eliminarPersona(personaConfirmarBaja.value.id)
    mensajeExito.value =
      respuesta.message || 'La operación se realizó correctamente.'
    personaConfirmarBaja.value = null
    await cargarPersonalSector(1)
  } catch (error) {
    apiError.value = normalizeApiError(error)
    personaConfirmarBaja.value = null
  } finally {
    eliminando.value = false
  }
}

onMounted(async () => {
  await cargarCatalogos()
  await cargarPersonalSector(1)
})
</script>

<template>
  <main class="contenedor-personal">
    <header class="encabezado-vista">
      <div>
        <h1>Gestión de Personal del Sector</h1>
        <p class="subtitulo">
          Administrá las fichas de Personal Fijo de tu sector
          <strong v-if="nombreSectorActual">({{ nombreSectorActual }})</strong>
          y consultá el padrón de Residentes.
        </p>
      </div>

      <div class="acciones-encabezado">
        <RouterLink to="/inicio/jefe-servicio" class="btn-secundario">
          Volver al inicio
        </RouterLink>
        <button
          type="button"
          class="btn-primario"
          :disabled="cargandoCatalogos || cargandoLista"
          @click="abrirModalAlta"
        >
          + Agregar Personal Fijo
        </button>
      </div>
    </header>

    <section
      v-if="mensajeExito"
      class="alerta-exito"
      role="status"
      aria-live="polite"
    >
      <p>{{ mensajeExito }}</p>
      <button
        type="button"
        class="btn-cerrar-alerta"
        aria-label="Cerrar notificación"
        @click="mensajeExito = ''"
      >
        ✕
      </button>
    </section>

    <ApiErrorMessage
      :error="apiError"
      @retry="cargarPersonalSector(paginacion.page)"
      @refresh="cargarPersonalSector(1)"
    />

    <section class="panel-sector" aria-labelledby="titulo-personal-fijo">
      <h2 id="titulo-personal-fijo">Personal Fijo del Sector</h2>

      <form
        class="barra-filtros"
        novalidate
        @submit.prevent="cargarPersonalSector(1)"
      >
        <div class="campo-filtro">
          <label for="filtro-q">Nombre o Apellido</label>
          <input
            id="filtro-q"
            v-model="filtros.q"
            type="text"
            placeholder="Buscar por nombre o apellido..."
            :disabled="cargandoLista"
          />
        </div>

        <div class="campo-filtro">
          <label for="filtro-dni">DNI</label>
          <input
            id="filtro-dni"
            v-model="filtros.dni"
            type="text"
            inputmode="numeric"
            maxlength="10"
            placeholder="Buscar por DNI..."
            :disabled="cargandoLista"
            @input="validarFiltroDni"
          />
          <small v-if="errorFiltroDni" class="error-texto">
            {{ errorFiltroDni }}
          </small>
        </div>

        <div class="campo-filtro">
          <label for="filtro-estado">Estado</label>
          <select
            id="filtro-estado"
            v-model="filtros.estado"
            :disabled="cargandoLista"
          >
            <option value="activos">Solo activos</option>
            <option value="inactivos">Solo inactivos</option>
            <option value="todos">Todos</option>
          </select>
        </div>

        <div class="acciones-filtro">
          <button
            type="submit"
            class="btn-primario"
            :disabled="cargandoLista"
          >
            {{ cargandoLista ? 'Buscando...' : 'Filtrar' }}
          </button>
          <button
            type="button"
            class="btn-secundario"
            :disabled="cargandoLista"
            @click="limpiarFiltros"
          >
            Limpiar
          </button>
        </div>
      </form>

      <div v-if="cargandoLista" class="estado-carga">
        Cargando personal del sector...
      </div>

      <div v-else-if="personal.length > 0" class="tabla-contenedor">
        <table class="tabla-datos">
          <caption>Listado de Personal Fijo asignado al sector</caption>
          <thead>
            <tr>
              <th scope="col">DNI</th>
              <th scope="col">Apellido y Nombre</th>
              <th scope="col">Sector</th>
              <th scope="col">Menú</th>
              <th scope="col">Estado</th>
              <th scope="col" class="col-acciones">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="persona in personal" :key="persona.id">
              <td>{{ persona.dni }}</td>
              <td>{{ persona.apellido }}, {{ persona.nombre }}</td>
              <td>{{ persona.sector?.nombre || 'Asignado al sector' }}</td>
              <td>
                {{ tiposMenuMap[persona.id_tipo_menu] || `Menú #${persona.id_tipo_menu}` }}
              </td>
              <td>
                <span
                  :class="persona.activo ? 'badge-activo' : 'badge-inactivo'"
                >
                  {{ persona.activo ? 'Activo' : 'Inactivo' }}
                </span>
              </td>
              <td class="col-acciones">
                <button
                  type="button"
                  class="btn-accionEditar"
                  @click="abrirModalEdicion(persona)"
                >
                  Editar
                </button>
                <button
                  v-if="persona.activo"
                  type="button"
                  class="btn-accionEliminar"
                  @click="solicitarConfirmacionBaja(persona)"
                >
                  Eliminar
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <nav
          v-if="paginacion.pages > 1"
          class="paginacion"
          aria-label="Paginación de personal del sector"
        >
          <span>
            Página <strong>{{ paginacion.page }}</strong> de
            <strong>{{ paginacion.pages }}</strong> ({{ paginacion.total }} registros)
          </span>
          <div class="paginacion-botones">
            <button
              type="button"
              class="btn-secundario"
              :disabled="paginacion.page <= 1 || cargandoLista"
              @click="cargarPersonalSector(paginacion.page - 1)"
            >
              Anterior
            </button>
            <button
              type="button"
              class="btn-secundario"
              :disabled="paginacion.page >= paginacion.pages || cargandoLista"
              @click="cargarPersonalSector(paginacion.page + 1)"
            >
              Siguiente
            </button>
          </div>
        </nav>
      </div>

      <p v-else class="sin-resultados">
        No se encontraron personas de tipo Personal Fijo con los criterios seleccionados.
      </p>
    </section>

    <BuscadorResidentes
      v-if="!cargandoCatalogos"
      :id-tipo-residente="idTipoResidente"
      :tipos-menu-map="tiposMenuMap"
    />

    <ModalFormularioPersonal
      :abierto="modalFormAbierto"
      :persona-editar="personaSeleccionada"
      :tipos-menu="tiposMenu"
      :id-tipo-personal-fijo="idTipoPersonalFijo"
      :sector-nombre="nombreSectorActual"
      @cerrar="modalFormAbierto = false"
      @guardado="alGuardarPersona"
      @conflicto="cargarPersonalSector(1)"
    />

    <div
      v-if="personaConfirmarBaja"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="titulo-confirmar-baja"
    >
      <div class="modal-confirmacion">
        <h3 id="titulo-confirmar-baja">Confirmar baja de personal</h3>
        <p>
          ¿Estás seguro de que querés eliminar o desactivar a
          <strong>{{ personaConfirmarBaja.apellido }}, {{ personaConfirmarBaja.nombre }}</strong>
          (DNI {{ personaConfirmarBaja.dni }})?
        </p>
        <p class="nota-baja">
          Si la persona posee historial de pedidos o entregas, el sistema la marcará como inactiva automáticamente.
        </p>
        <div class="acciones-confirmacion">
          <button
            type="button"
            class="btn-secundario"
            :disabled="eliminando"
            @click="personaConfirmarBaja = null"
          >
            Cancelar
          </button>
          <button
            type="button"
            class="btn-peligro"
            :disabled="eliminando"
            @click="confirmarBajaPersona"
          >
            {{ eliminando ? 'Procesando...' : 'Confirmar' }}
          </button>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.contenedor-personal {
  max-width: 1100px;
  margin: 0 auto;
  padding: 1.5rem 1rem 3rem;
}

.encabezado-vista {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.encabezado-vista h1 {
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
  color: #1e293b;
}

.subtitulo {
  margin: 0;
  color: #64748b;
  font-size: 0.95rem;
}

.acciones-encabezado {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.alerta-exito {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.alerta-exito p {
  margin: 0;
}

.btn-cerrar-alerta {
  background: none;
  border: none;
  color: #166534;
  cursor: pointer;
  font-size: 1rem;
}

.panel-sector {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.25rem;
}

.panel-sector h2 {
  margin: 0 0 1rem;
  font-size: 1.2rem;
  color: #1e293b;
}

.barra-filtros {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
  background-color: #f8fafc;
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.campo-filtro {
  display: flex;
  flex-direction: column;
  flex: 1 1 180px;
}

.campo-filtro label {
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 0.3rem;
  color: #334155;
}

.campo-filtro input,
.campo-filtro select {
  padding: 0.55rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}

.acciones-filtro {
  display: flex;
  gap: 0.5rem;
}

.error-texto {
  color: #b91c1c;
  font-size: 0.8rem;
  margin-top: 0.25rem;
}

.tabla-contenedor {
  overflow-x: auto;
}

.tabla-datos {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.tabla-datos caption {
  text-align: left;
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.tabla-datos th,
.tabla-datos td {
  padding: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

.tabla-datos th {
  background-color: #f8fafc;
  font-weight: 600;
  color: #334155;
}

.col-acciones {
  text-align: right;
  white-space: nowrap;
}

.badge-activo {
  background-color: #dcfce7;
  color: #166534;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
}

.badge-inactivo {
  background-color: #f1f5f9;
  color: #64748b;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
}

.btn-accionEditar,
.btn-accionEliminar {
  background: none;
  border: none;
  cursor: pointer;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
}

.btn-accionEditar {
  color: #2563eb;
}

.btn-accionEliminar {
  color: #dc2626;
}

.paginacion {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1rem;
}

.paginacion-botones {
  display: flex;
  gap: 0.5rem;
}

.btn-primario {
  background-color: #2563eb;
  color: #ffffff;
  border: none;
  padding: 0.55rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.btn-secundario {
  background-color: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
  padding: 0.55rem 1rem;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.9rem;
  cursor: pointer;
}

.btn-peligro {
  background-color: #dc2626;
  color: #ffffff;
  border: none;
  padding: 0.55rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.sin-resultados,
.estado-carga {
  padding: 1rem 0;
  color: #64748b;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 1000;
}

.modal-confirmacion {
  background: #ffffff;
  border-radius: 8px;
  max-width: 440px;
  width: 100%;
  padding: 1.5rem;
}

.modal-confirmacion h3 {
  margin: 0 0 0.75rem;
  color: #1e293b;
}

.nota-baja {
  font-size: 0.85rem;
  color: #64748b;
}

.acciones-confirmacion {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.25rem;
}
</style>