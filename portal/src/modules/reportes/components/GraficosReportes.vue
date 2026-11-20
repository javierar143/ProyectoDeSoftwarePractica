<script setup>
import { computed } from 'vue'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  PointElement,
  LineElement,
} from 'chart.js'
import { Bar, Doughnut, Line } from 'vue-chartjs'

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  PointElement,
  LineElement
)

const props = defineProps({
  resumenAutorizaciones: {
    type: Object,
    required: true,
  },
  resumenEntregas: {
    type: Object,
    required: true,
  },
  agrupamiento: {
    type: String,
    default: 'dia',
  },
})

const opcionesBase = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' },
  },
}

// Comparacion Pedidas vs Autorizadas vs Entregadas
const filasComparacion = computed(() => [
  { concepto: 'Pedidas (Total)', cantidad: props.resumenAutorizaciones.total_pedido ?? 0 },
  { concepto: 'Autorizadas', cantidad: props.resumenAutorizaciones.total_autorizado ?? 0 },
  { concepto: 'Entregadas', cantidad: props.resumenEntregas.total_entregado ?? 0 },
])

const dataComparacion = computed(() => ({
  labels: ['Pedidas', 'Autorizadas', 'Entregadas'],
  datasets: [
    {
      label: 'Cantidad de viandas',
      backgroundColor: ['#3b82f6', '#10b981', '#6366f1'],
      data: [
        props.resumenAutorizaciones.total_pedido ?? 0,
        props.resumenAutorizaciones.total_autorizado ?? 0,
        props.resumenEntregas.total_entregado ?? 0,
      ],
    },
  ],
}))

// distribucion por Sector (combinando desglose de autorizaciones y entregas del backend)
const filasPorSector = computed(() => {
  const mapa = new Map()

  for (const item of props.resumenAutorizaciones.desglose ?? []) {
    const clave = item.sector || `Sector #${item.idSector}`
    if (!mapa.has(clave)) {
      mapa.set(clave, { sector: clave, pedidas: 0, autorizadas: 0, entregadas: 0 })
    }
    const fila = mapa.get(clave)
    fila.pedidas += item.cantidad_pedida ?? 0
    fila.autorizadas += item.cantidad_autorizada ?? 0
  }

  for (const item of props.resumenEntregas.desglose ?? []) {
    const clave = item.sector || `Sector #${item.idSector}`
    if (!mapa.has(clave)) {
      mapa.set(clave, { sector: clave, pedidas: 0, autorizadas: 0, entregadas: 0 })
    }
    const fila = mapa.get(clave)
    fila.entregadas += item.total_entregado ?? 0
  }

  return Array.from(mapa.values()).sort((a, b) => a.sector.localeCompare(b.sector))
})

const dataPorSector = computed(() => ({
  labels: filasPorSector.value.map((f) => f.sector),
  datasets: [
    {
      label: 'Pedidas',
      backgroundColor: '#3b82f6',
      data: filasPorSector.value.map((f) => f.pedidas),
    },
    {
      label: 'Autorizadas',
      backgroundColor: '#10b981',
      data: filasPorSector.value.map((f) => f.autorizadas),
    },
    {
      label: 'Entregadas',
      backgroundColor: '#6366f1',
      data: filasPorSector.value.map((f) => f.entregadas),
    },
  ],
}))

// Distribución por Tipo de Menú
const filasPorMenu = computed(() => {
  const mapa = new Map()

  for (const item of props.resumenAutorizaciones.desglose ?? []) {
    const clave = item.tipo_menu || `Menú #${item.idTipoMenu}`
    if (!mapa.has(clave)) {
      mapa.set(clave, { menu: clave, pedidas: 0, autorizadas: 0, entregadas: 0 })
    }
    const fila = mapa.get(clave)
    fila.pedidas += item.cantidad_pedida ?? 0
    fila.autorizadas += item.cantidad_autorizada ?? 0
  }

  for (const item of props.resumenEntregas.desglose ?? []) {
    const clave = item.tipo_menu || `Menú #${item.idTipoMenu}`
    if (!mapa.has(clave)) {
      mapa.set(clave, { menu: clave, pedidas: 0, autorizadas: 0, entregadas: 0 })
    }
    const fila = mapa.get(clave)
    fila.entregadas += item.total_entregado ?? 0
  }

  return Array.from(mapa.values()).sort((a, b) => a.menu.localeCompare(b.menu))
})

const dataPorMenu = computed(() => ({
  labels: filasPorMenu.value.map((f) => f.menu),
  datasets: [
    {
      backgroundColor: ['#2563eb', '#16a34a', '#f59e0b', '#ec4899', '#8b5cf6'],
      data: filasPorMenu.value.map((f) => f.pedidas),
    },
  ],
}))

// evolución en el período (agrupaciones temporales devueltas por el backend)
const filasEvolucion = computed(() => {
  const mapa = new Map()

  for (const item of props.resumenAutorizaciones.agrupaciones ?? []) {
    mapa.set(item.clave, {
      periodo: item.etiqueta || item.clave,
      pedidas: item.total_pedido ?? 0,
      autorizadas: item.total_autorizado ?? 0,
      entregadas: 0,
    })
  }

  for (const item of props.resumenEntregas.agrupaciones ?? []) {
    if (!mapa.has(item.clave)) {
      mapa.set(item.clave, {
        periodo: item.etiqueta || item.clave,
        pedidas: 0,
        autorizadas: item.total_autorizado ?? 0,
        entregadas: item.total_entregado ?? 0,
      })
    } else {
      mapa.get(item.clave).entregadas = item.total_entregado ?? 0
    }
  }

  return Array.from(mapa.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([, valor]) => valor)
})

const dataEvolucion = computed(() => ({
  labels: filasEvolucion.value.map((f) => f.periodo),
  datasets: [
    {
      label: 'Pedidas',
      borderColor: '#3b82f6',
      backgroundColor: '#3b82f6',
      tension: 0.2,
      data: filasEvolucion.value.map((f) => f.pedidas),
    },
    {
      label: 'Autorizadas',
      borderColor: '#10b981',
      backgroundColor: '#10b981',
      tension: 0.2,
      data: filasEvolucion.value.map((f) => f.autorizadas),
    },
    {
      label: 'Entregadas',
      borderColor: '#6366f1',
      backgroundColor: '#6366f1',
      tension: 0.2,
      data: filasEvolucion.value.map((f) => f.entregadas),
    },
  ],
}))
</script>

<template>
  <div class="grid-graficos">
    <!-- 1. Comparación general -->
    <section class="card-grafico">
      <h2>Comparación: Pedidas, Autorizadas y Entregadas</h2>
      <div class="contenedor-canvas">
        <Bar :data="dataComparacion" :options="opcionesBase" />
      </div>
      <table class="tabla-detalle">
        <thead>
          <tr>
            <th>Concepto</th>
            <th>Cantidad</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="fila in filasComparacion" :key="fila.concepto">
            <td>{{ fila.concepto }}</td>
            <td>{{ fila.cantidad }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- 2. Distribución por Menú -->
    <section class="card-grafico">
      <h2>Distribución por Tipo de Menú</h2>
      <div v-if="filasPorMenu.length" class="contenedor-canvas">
        <Doughnut :data="dataPorMenu" :options="opcionesBase" />
      </div>
      <p v-else class="sin-datos">No hay datos para mostrar con los filtros seleccionados.</p>
      <table v-if="filasPorMenu.length" class="tabla-detalle">
        <thead>
          <tr>
            <th>Tipo de Menú</th>
            <th>Pedidas</th>
            <th>Autorizadas</th>
            <th>Entregadas</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="fila in filasPorMenu" :key="fila.menu">
            <td>{{ fila.menu }}</td>
            <td>{{ fila.pedidas }}</td>
            <td>{{ fila.autorizadas }}</td>
            <td>{{ fila.entregadas }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- 3. Distribución por Sector -->
    <section class="card-grafico card-ancho-completo">
      <h2>Distribución por Sector (incluye Residentes)</h2>
      <div v-if="filasPorSector.length" class="contenedor-canvas">
        <Bar :data="dataPorSector" :options="opcionesBase" />
      </div>
      <p v-else class="sin-datos">No hay datos por sector para los filtros seleccionados.</p>
      <table v-if="filasPorSector.length" class="tabla-detalle">
        <thead>
          <tr>
            <th>Sector</th>
            <th>Pedidas</th>
            <th>Autorizadas</th>
            <th>Entregadas</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="fila in filasPorSector" :key="fila.sector">
            <td>{{ fila.sector }}</td>
            <td>{{ fila.pedidas }}</td>
            <td>{{ fila.autorizadas }}</td>
            <td>{{ fila.entregadas }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- 4. Evolución en el período -->
    <section class="card-grafico card-ancho-completo">
      <h2>Evolución en el período (agrupado por {{ agrupamiento }})</h2>
      <div v-if="filasEvolucion.length" class="contenedor-canvas">
        <Line :data="dataEvolucion" :options="opcionesBase" />
      </div>
      <p v-else class="sin-datos">No hay evolución registrada para el período seleccionado.</p>
      <table v-if="filasEvolucion.length" class="tabla-detalle">
        <thead>
          <tr>
            <th>Período</th>
            <th>Pedidas</th>
            <th>Autorizadas</th>
            <th>Entregadas</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="fila in filasEvolucion" :key="fila.periodo">
            <td>{{ fila.periodo }}</td>
            <td>{{ fila.pedidas }}</td>
            <td>{{ fila.autorizadas }}</td>
            <td>{{ fila.entregadas }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
.grid-graficos {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 1.5rem;
}

.card-grafico {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.25rem;
}

.card-ancho-completo {
  grid-column: 1 / -1;
}

.card-grafico h2 {
  margin: 0 0 1rem 0;
  font-size: 1.05rem;
  color: #1e293b;
}

.contenedor-canvas {
  position: relative;
  height: 280px;
  margin-bottom: 1.25rem;
}

.sin-datos {
  color: #64748b;
  font-size: 0.9rem;
  padding: 1rem 0;
}

.tabla-detalle {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.tabla-detalle th,
.tabla-detalle td {
  border-bottom: 1px solid #e2e8f0;
  padding: 0.55rem 0.65rem;
  text-align: left;
}

.tabla-detalle th {
  background: #f8fafc;
  color: #334155;
  font-weight: 600;
}
</style>