<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ApiErrorMessage from '@/components/common/ApiErrorMessage.vue'
import { normalizeApiError } from '@/services/api/error-handler'
import FiltrosReportes from '@/modules/reportes/components/FiltrosReportes.vue'
import IndicadoresKpi from '@/modules/reportes/components/IndicadoresKpi.vue'
import GraficosReportes from '@/modules/reportes/components/GraficosReportes.vue'
import {
  obtenerResumenAutorizaciones,
  obtenerResumenEntregas,
  exportarResumenCsv,
  obtenerSectores,
  obtenerTiposMenu,
} from '@/modules/reportes/services/reportes'

const router = useRouter()

const TIPOS_COMIDA = [
  { idTipoComida: 1, nombre: 'Desayuno' },
  { idTipoComida: 2, nombre: 'Almuerzo' },
  { idTipoComida: 3, nombre: 'Merienda' },
  { idTipoComida: 4, nombre: 'Cena' },
]

function obtenerRangoMesActual() {
  const hoy = new Date()
  const inicio = new Date(hoy.getFullYear(), hoy.getMonth(), 1)
  const formato = (d) => d.toISOString().slice(0, 10)
  return {
    fecha_desde: formato(inicio),
    fecha_hasta: formato(hoy),
  }
}

function crearFiltrosIniciales() {
  const { fecha_desde, fecha_hasta } = obtenerRangoMesActual()
  return {
    fecha_desde,
    fecha_hasta,
    sector: '',
    tipo_comida: '',
    tipo_menu: '',
    estado: '',
    condicion: 'todas',
    agrupamiento: 'dia',
  }
}

const filtros = ref(crearFiltrosIniciales())
const sectores = ref([])
const tiposMenu = ref([])

const resumenAutorizaciones = ref({
  total_pedido: 0,
  total_pedido_regulares: 0,
  total_pedido_excepciones: 0,
  total_pedido_residentes: 0,
  total_autorizado: 0,
  diferencia: 0,
  desglose: [],
  agrupaciones: [],
})

const resumenEntregas = ref({
  total_autorizado: 0,
  total_entregado: 0,
  diferencia: 0,
  desglose: [],
  agrupaciones: [],
})

const cargando = ref(false)
const exportando = ref(false)
const errorApi = ref(null)

async function cargarCatalogos() {
  try {
    const [listaSectores, listaMenus] = await Promise.all([
      obtenerSectores(),
      obtenerTiposMenu(),
    ])
    sectores.value = listaSectores
    tiposMenu.value = listaMenus
  } catch (err) {
    // Si es 503 lo maneja el interceptor global de mantenimiento
    if (err?.response?.status === 503) return
    errorApi.value = normalizeApiError(err)
  }
}

async function cargarReportes() {
  cargando.value = true
  errorApi.value = null

  try {
    const [aut, ent] = await Promise.all([
      obtenerResumenAutorizaciones(filtros.value),
      obtenerResumenEntregas(filtros.value),
    ])
    resumenAutorizaciones.value = aut
    resumenEntregas.value = ent
  } catch (err) {
    if (err?.response?.status === 503) return
    errorApi.value = normalizeApiError(err)
  } finally {
    cargando.value = false
  }
}

async function handleExportarCsv(tipo) {
  exportando.value = true
  errorApi.value = null

  try {
    await exportarResumenCsv(tipo, filtros.value)
  } catch (err) {
    if (err?.response?.status === 503) return
    errorApi.value = normalizeApiError(err)
  } finally {
    exportando.value = false
  }
}

function handleLimpiar() {
  filtros.value = crearFiltrosIniciales()
  cargarReportes()
}

onMounted(async () => {
  await cargarCatalogos()
  await cargarReportes()
})
</script>

<template>
  <main class="contenedor-reportes">
    <header class="encabezado-reportes">
      <div>
        <h1>Reportes y Estadísticas</h1>
        <p class="subtitulo">
          Información consolidada de pedidos, autorizaciones y entregas de comidas.
        </p>
      </div>
      <button
        type="button"
        class="btn-volver"
        @click="router.push('/inicio/servicio-alimentacion')"
      >
        Volver al inicio
      </button>
    </header>

    <FiltrosReportes
      v-model="filtros"
      :sectores="sectores"
      :tipos-comida="TIPOS_COMIDA"
      :tipos-menu="tiposMenu"
      :cargando="cargando"
      :exportando="exportando"
      @aplicar="cargarReportes"
      @limpiar="handleLimpiar"
      @exportar-csv="handleExportarCsv"
    />

    <ApiErrorMessage
      v-if="errorApi"
      :error="errorApi"
      @retry="cargarReportes"
    />

    <div v-if="cargando" class="estado-carga" role="status">
      Cargando estadísticas del período seleccionado...
    </div>

    <template v-else>
      <IndicadoresKpi
        :resumen-autorizaciones="resumenAutorizaciones"
        :resumen-entregas="resumenEntregas"
      />

      <GraficosReportes
        :resumen-autorizaciones="resumenAutorizaciones"
        :resumen-entregas="resumenEntregas"
        :agrupamiento="filtros.agrupamiento"
      />
    </template>
  </main>
</template>

<style scoped>
.contenedor-reportes {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem 1rem 3rem;
}

.encabezado-reportes {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.encabezado-reportes h1 {
  margin: 0;
  font-size: 1.65rem;
  color: #0f172a;
}

.subtitulo {
  margin: 0.3rem 0 0;
  color: #64748b;
  font-size: 0.95rem;
}

.btn-volver {
  padding: 0.5rem 1rem;
  background: #f8fafc;
  color: #334155;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.estado-carga {
  text-align: center;
  padding: 2.5rem;
  color: #475569;
  font-weight: 500;
}
</style>