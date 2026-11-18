<script setup>
import { onMounted, reactive, ref } from 'vue'
import { listarPersonal } from '../services/personal'
import { normalizeApiError } from '@/services/api/error-handler'
import ApiErrorMessage from '@/modules/shared/components/ApiErrorMessage.vue'

const props = defineProps({
  idTipoResidente: {
    type: Number,
    required: true,
  },
  tiposMenuMap: {
    type: Object,
    default: () => ({}),
  },
  permitirSeleccion: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['seleccionar'])

const filtros = reactive({
  q: '',
  dni: '',
})

const errorDni = ref('')
const cargando = ref(false)
const apiError = ref(null)

const residentes = ref([])
const paginacion = reactive({
  page: 1,
  per_page: 10,
  total: 0,
  pages: 1,
})

function validarFiltroDni() {
  const valor = filtros.dni.trim()
  if (valor && !/^\d+$/.test(valor)) {
    errorDni.value = 'Ingresá solo números para buscar por DNI.'
    return false
  }
  errorDni.value = ''
  return true
}

async function buscarResidentes(pagina = 1) {
  if (!validarFiltroDni()) {
    return
  }

  cargando.value = true
  apiError.value = null

  try {
    const respuesta = await listarPersonal({
      q: filtros.q.trim(),
      dni: filtros.dni.trim(),
      id_tipo_personal: props.idTipoResidente,
      estado: 'activos',
      page: pagina,
      per_page: paginacion.per_page,
    })

    residentes.value = respuesta.items ?? []
    paginacion.page = respuesta.page ?? 1
    paginacion.total = respuesta.total ?? 0
    paginacion.pages = respuesta.pages ?? 1
  } catch (error) {
    apiError.value = normalizeApiError(error)
  } finally {
    cargando.value = false
  }
}

function limpiarFiltros() {
  filtros.q = ''
  filtros.dni = ''
  errorDni.value = ''
  buscarResidentes(1)
}

onMounted(() => {
  if (props.idTipoResidente) {
    buscarResidentes(1)
  }
})
</script>

<template>
  <section class="panel-residentes" aria-labelledby="titulo-buscador-residentes">
    <header class="panel-header">
      <div>
        <h2 id="titulo-buscador-residentes">Búsqueda de Residentes</h2>
        <p class="subtitulo">
          Consultá residentes activos por nombre, apellido o DNI (personal rotativo sin sector fijo).
        </p>
      </div>
    </header>

    <form class="barra-filtros" novalidate @submit.prevent="buscarResidentes(1)">
      <div class="campo-filtro">
        <label for="residente-q">Nombre o Apellido</label>
        <input
          id="residente-q"
          v-model="filtros.q"
          type="text"
          placeholder="Ej: Gómez"
          :disabled="cargando"
        />
      </div>

      <div class="campo-filtro">
        <label for="residente-dni">DNI</label>
        <input
          id="residente-dni"
          v-model="filtros.dni"
          type="text"
          inputmode="numeric"
          maxlength="10"
          placeholder="Ej: 40111222"
          :disabled="cargando"
          @input="validarFiltroDni"
        />
        <small v-if="errorDni" class="error-texto">{{ errorDni }}</small>
      </div>

      <div class="acciones-filtro">
        <button type="submit" class="btn-primario" :disabled="cargando">
          {{ cargando ? 'Buscando...' : 'Buscar' }}
        </button>
        <button
          type="button"
          class="btn-secundario"
          :disabled="cargando"
          @click="limpiarFiltros"
        >
          Limpiar
        </button>
      </div>
    </form>

    <ApiErrorMessage
      :error="apiError"
      @retry="buscarResidentes(paginacion.page)"
      @refresh="buscarResidentes(1)"
    />

    <div v-if="cargando" class="estado-carga">Cargando residentes...</div>

    <div v-else-if="residentes.length > 0" class="tabla-contenedor">
      <table class="tabla-datos">
        <caption>Listado de residentes activos</caption>
        <thead>
          <tr>
            <th scope="col">DNI</th>
            <th scope="col">Apellido y Nombre</th>
            <th scope="col">Menú Predeterminado</th>
            <th scope="col">Condición</th>
            <th v-if="permitirSeleccion" scope="col" class="col-acciones">Acción</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="res in residentes" :key="res.id">
            <td>{{ res.dni }}</td>
            <td>{{ res.apellido }}, {{ res.nombre }}</td>
            <td>{{ tiposMenuMap[res.id_tipo_menu] || `Menú #${res.id_tipo_menu}` }}</td>
            <td><span class="badge-residente">Residente (Rotativo)</span></td>
            <td v-if="permitirSeleccion" class="col-acciones">
              <button
                type="button"
                class="btn-link"
                @click="emit('seleccionar', res)"
              >
                Incluir en pedido
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <nav
        v-if="paginacion.pages > 1"
        class="paginacion"
        aria-label="Paginación de residentes"
      >
        <span>
          Página <strong>{{ paginacion.page }}</strong> de
          <strong>{{ paginacion.pages }}</strong> ({{ paginacion.total }} residentes)
        </span>
        <div class="paginacion-botones">
          <button
            type="button"
            class="btn-secundario"
            :disabled="paginacion.page <= 1 || cargando"
            @click="buscarResidentes(paginacion.page - 1)"
          >
            Anterior
          </button>
          <button
            type="button"
            class="btn-secundario"
            :disabled="paginacion.page >= paginacion.pages || cargando"
            @click="buscarResidentes(paginacion.page + 1)"
          >
            Siguiente
          </button>
        </div>
      </nav>
    </div>

    <p v-else class="sin-resultados">
      No se encontraron residentes activos con los criterios ingresados.
    </p>
  </section>
</template>

<style scoped>
.panel-residentes {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.25rem;
  margin-top: 1.5rem;
}

.panel-header h2 {
  margin: 0 0 0.25rem;
  font-size: 1.2rem;
  color: #1e293b;
}

.subtitulo {
  margin: 0 0 1rem;
  color: #64748b;
  font-size: 0.9rem;
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
  flex: 1 1 200px;
}

.campo-filtro label {
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 0.3rem;
  color: #334155;
}

.campo-filtro input {
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
  padding: 0.7rem 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

.tabla-datos th {
  background-color: #f8fafc;
  font-weight: 600;
  color: #334155;
}

.badge-residente {
  background-color: #e0f2fe;
  color: #0369a1;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
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
  cursor: pointer;
}

.btn-link {
  background: none;
  border: none;
  color: #2563eb;
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
}

.sin-resultados,
.estado-carga {
  padding: 1rem 0;
  color: #64748b;
}
</style>