<template>
  <main class="crear-pedido-page">
    <header class="encabezado">
      <div>
        <h1>Crear Pedido de Prueba</h1>
        <p>Envía pedidos contra <code>POST /api/requests</code> y consulta/autoriza desde la vista correspondiente.</p>
      </div>
      <router-link class="btn-link" to="/inicio/servicio-alimentacion">
        Ir a Autorización de Pedidos →
      </router-link>
    </header>

    <div v-if="aviso.texto" :class="['aviso', aviso.tipo]" role="alert">
      <span>{{ aviso.texto }}</span>
      <router-link v-if="pedidoCreadoId" class="btn-ir-autorizar" to="/inicio/servicio-alimentacion">
        Revisar pedido #{{ pedidoCreadoId }} en Autorizaciones
      </router-link>
    </div>

    <section class="card datos-pedido">
      <div class="card-header-flex">
        <h2>Datos generales del pedido</h2>
        <label class="toggle-local">
          <input v-model="modoLocal" type="checkbox" />
          <span>Modo local (sin pegar al backend)</span>
        </label>
      </div>

      <div class="grid-campos">
        <label>
          Fecha desde
          <input v-model="form.fecha_desde" type="date" />
        </label>
        <label>
          Fecha hasta
          <input v-model="form.fecha_hasta" type="date" />
        </label>
        <label>
          Periodicidad
          <select v-model="form.periodicidad">
            <option value="diaria">diaria</option>
            <option value="semanal">semanal</option>
            <option value="mensual">mensual</option>
          </select>
        </label>
        <label v-if="!modoLocal">
          Endpoint POST
          <input v-model="endpointCrear" type="text" placeholder="/requests" />
        </label>
        <label v-if="!modoLocal">
          Endpoint Comidas
          <input v-model="endpointComidas" type="text" placeholder="/tipos-comida" />
        </label>
      </div>
    </section>

    <section class="card">
      <div class="card-header-flex">
        <h2>Personal incluido ({{ filas.length }})</h2>
        <div class="acciones-rapidas">
          <button
            type="button"
            class="btn-secundario"
            :disabled="cargandoComidas"
            @click="cargarComidas"
          >
            {{ cargandoComidas ? 'Cargando comidas...' : 'Cargar comidas' }}
          </button>
          <button type="button" class="btn-secundario" @click="cargarPersonalDemo">
            Cargar personal del hospital
          </button>
          <button type="button" class="btn-primario" @click="agregarFila">
            + Agregar persona
          </button>
        </div>
      </div>

      <div class="tabla-wrap">
        <table class="tabla">
          <thead>
            <tr>
              <th>Persona</th>
              <th>ID Personal</th>
              <th v-for="comida in comidas" :key="comida.idTipoComida" class="th-comida">
                <div>{{ comida.label }}</div>
                <small class="id-hint">ID {{ comida.idTipoComida }}</small>
                <div>
                  <button
                    type="button"
                    class="link-todos"
                    @click="alternarTodosComida(comida.idTipoComida)"
                  >
                    Todos
                  </button>
                </div>
              </th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(fila, idx) in filas" :key="fila.uid">
              <td>
                <select v-model="fila.idPersonal" @change="sincronizarPersona(fila)">
                  <option v-for="p in catalogoPersonal" :key="p.idPersonal" :value="p.idPersonal">
                    {{ p.nombre }} (DNI {{ p.dni }})
                  </option>
                </select>
              </td>
              <td>
                <input v-model.number="fila.idPersonal" type="number" min="1" class="input-id" />
              </td>
              <td v-for="comida in comidas" :key="comida.idTipoComida" class="td-comida">
                <button
                  type="button"
                  :class="['check-box', fila.comidas[comida.idTipoComida] ? 'marcado' : '']"
                  :aria-pressed="Boolean(fila.comidas[comida.idTipoComida])"
                  @click="fila.comidas[comida.idTipoComida] = !fila.comidas[comida.idTipoComida]"
                >
                  <span v-if="fila.comidas[comida.idTipoComida]">✓</span>
                </button>
              </td>
              <td>
                <button type="button" class="btn-borrar" @click="quitarFila(idx)">
                  Quitar
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="payload-box">
        <strong>Payload armado:</strong>
        <pre>{{ payloadPreview }}</pre>
      </div>

      <div class="footer-envio">
        <button
          type="button"
          class="btn-enviar"
          :disabled="enviando || filas.length === 0"
          @click="crearPedido"
        >
          {{
            enviando
              ? 'Enviando...'
              : modoLocal
                ? 'Guardar local'
                : 'Crear y confirmar pedido'
          }}
        </button>
      </div>
    </section>
  </main>
</template>

<script setup>
import { computed, ref } from 'vue'
import apiClient from '@/services/api/client'

const STORAGE_KEY = 'pedidos_prueba_locales'

const endpointComidas = ref('/tipos-comida')
const cargandoComidas = ref(false)

const comidasBase = [
  { idTipoComida: 1, label: 'Desayuno' },
  { idTipoComida: 2, label: 'Almuerzo' },
  { idTipoComida: 3, label: 'Merienda' },
  { idTipoComida: 4, label: 'Cena' },
]

const comidas = ref([...comidasBase])

function normalizarComida(item, idx) {
  const id = Number(item?.idTipoComida ?? item?.id_tipo_comida ?? item?.id ?? idx + 1)
  const label = String(item?.nombre ?? item?.label ?? `Comida ${id}`)
  return { idTipoComida: id, label }
}

async function cargarComidas() {
  cargandoComidas.value = true
  aviso.value = { tipo: '', texto: '' }

  try {
    const res = await apiClient.get(endpointComidas.value.trim() || '/tipos-comida')
    const raw = Array.isArray(res?.data)
      ? res.data
      : Array.isArray(res?.data?.items)
        ? res.data.items
        : Array.isArray(res?.data?.data)
          ? res.data.data
          : null

    if (raw && raw.length > 0) {
      comidas.value = raw.map(normalizarComida)
      aviso.value = {
        tipo: 'ok',
        texto: `Se cargaron ${comidas.value.length} tipos de comida desde el backend.`,
      }
      return
    }

    comidas.value = [...comidasBase]
    aviso.value = {
      tipo: 'info',
      texto: 'No hubo comidas en la respuesta; se mantienen las 4 comidas base.',
    }
  } catch {
    comidas.value = [...comidasBase]
    aviso.value = {
      tipo: 'info',
      texto: 'Se mantienen las 4 comidas base (Desayuno, Almuerzo, Merienda, Cena).',
    }
  } finally {
    cargandoComidas.value = false
  }
}

const catalogoPersonal = [
  { idPersonal: 1, dni: '11111111', nombre: 'Soyadmin, Juan' },
  { idPersonal: 2, dni: '22222222', nombre: 'Detal, Fulano' },
  { idPersonal: 3, dni: '33333333', nombre: 'Perez, Mengano' },
  { idPersonal: 4, dni: '44444444', nombre: 'Gomez, Pascuala' },
  { idPersonal: 5, dni: '555555555', nombre: 'Gonzalez, Agus' },
]

const hoyIso = new Date().toISOString().slice(0, 10)

let seqUid = 1
function nuevaFila(base = {}) {
  return {
    uid: seqUid++,
    idPersonal: Number(base.idPersonal) || 4,
    comidas: {
      1: Boolean(base.comidas?.[1]),
      2: base.comidas?.[2] ?? true,
      3: Boolean(base.comidas?.[3]),
      4: Boolean(base.comidas?.[4]),
    },
  }
}

// Desactivado por defecto para que le pegue directo a los endpoints reales
const modoLocal = ref(false)
const endpointCrear = ref('/requests')
const form = ref({
  fecha_desde: hoyIso,
  fecha_hasta: hoyIso,
  periodicidad: 'diaria',
})

const filas = ref([])
const enviando = ref(false)
const pedidoCreadoId = ref(null)
const aviso = ref({ tipo: '', texto: '' })

function construirDiccionarioComidas() {
  const diccionario = {}
  for (const comida of comidas.value) {
    const idComida = Number(comida.idTipoComida)
    const ids = []
    for (const fila of filas.value) {
      const idP = Number(fila.idPersonal)
      if (fila.comidas[idComida] && Number.isInteger(idP) && idP > 0 && !ids.includes(idP)) {
        ids.push(idP)
      }
    }
    if (ids.length > 0) {
      diccionario[idComida] = ids
    }
  }
  return diccionario
}

const payload = computed(() => {
  const body = {
    fecha_desde: form.value.fecha_desde,
    periodicidad: form.value.periodicidad,
    comidas: construirDiccionarioComidas(),
  }
  if (form.value.fecha_hasta) {
    body.fecha_hasta = form.value.fecha_hasta
  }
  return body
})

const payloadPreview = computed(() => JSON.stringify(payload.value, null, 2))

function cargarPersonalDemo() {
  filas.value = [
    nuevaFila({ idPersonal: 4, comidas: { 2: true } }),
    nuevaFila({ idPersonal: 5, comidas: { 2: true, 4: true } }),
    nuevaFila({ idPersonal: 3, comidas: { 3: true } }),
  ]
  aviso.value = { tipo: 'info', texto: 'Datos de ejemplo cargados.' }
}

cargarPersonalDemo()

function sincronizarPersona(fila) {
  fila.idPersonal = Number(fila.idPersonal) || 1
}

function alternarTodosComida(idTipoComida) {
  if (!filas.value.length) return
  const todasMarcadas = filas.value.every((f) => Boolean(f.comidas[idTipoComida]))
  filas.value.forEach((f) => {
    f.comidas[idTipoComida] = !todasMarcadas
  })
}

function agregarFila() {
  filas.value.push(nuevaFila())
}

function quitarFila(idx) {
  filas.value.splice(idx, 1)
}

function guardarPedidoEnLocalStorage(body) {
  let actuales = []
  try {
    actuales = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    if (!Array.isArray(actuales)) actuales = []
  } catch {
    actuales = []
  }

  const nuevoId = Date.now()
  const registro = {
    idPedido: nuevoId,
    estado: 'confirmado',
    creadoEnLocal: true,
    ...body,
  }
  actuales.unshift(registro)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(actuales))
  return nuevoId
}

async function crearPedido() {
  enviando.value = true
  pedidoCreadoId.value = null
  aviso.value = { tipo: '', texto: '' }

  try {
    if (modoLocal.value) {
      const idSimulado = guardarPedidoEnLocalStorage(payload.value)
      pedidoCreadoId.value = idSimulado
      aviso.value = {
        tipo: 'ok',
        texto: `Pedido #${idSimulado} guardado localmente.`,
      }
      return
    }

    const res = await apiClient.post(endpointCrear.value.trim() || '/requests', payload.value)
    const creado = res?.data || {}
    pedidoCreadoId.value = creado.idPedido ?? creado.id ?? 'nuevo'
    aviso.value = {
      tipo: 'ok',
      texto: `Pedido #${pedidoCreadoId.value} creado en el backend.`,
    }
  } catch (err) {
    const status = err?.response?.status
    const detalle =
      err?.response?.data?.error ||
      err?.response?.data?.message ||
      err?.response?.data?.description ||
      err?.message ||
      'Error al crear el pedido'
    aviso.value = {
      tipo: 'err',
      texto: `Error (${status ?? 'red'}): ${detalle}.`,
    }
  } finally {
    enviando.value = false
  }
}
</script>

<style scoped>
.crear-pedido-page {
  max-width: 1150px;
  margin: 0 auto;
  padding: 1.25rem;
  font-family: system-ui, -apple-system, sans-serif;
}

.encabezado {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.encabezado h1 {
  margin: 0;
  font-size: 1.4rem;
}

.encabezado p {
  margin: 0.25rem 0 0;
  color: #475569;
}

.card {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.card h2 {
  margin: 0 0 0.75rem;
  font-size: 1.05rem;
}

.card-header-flex {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.card-header-flex h2 {
  margin: 0;
}

.toggle-local {
  flex-direction: row;
  align-items: center;
  gap: 0.45rem;
  cursor: pointer;
  user-select: none;
}

.grid-campos {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  font-weight: 600;
}

input,
select {
  padding: 0.42rem 0.55rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}

.input-id {
  width: 80px;
}

.tabla-wrap {
  overflow-x: auto;
}

.tabla {
  width: 100%;
  border-collapse: collapse;
}

.tabla th,
.tabla td {
  padding: 0.55rem;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
}

.th-comida,
.td-comida {
  text-align: center;
}

.id-hint {
  color: #64748b;
  font-weight: 500;
}

.link-todos {
  background: none;
  border: none;
  padding: 0;
  min-height: auto;
  color: #0284c7;
  font-size: 0.8rem;
  text-decoration: underline;
  cursor: pointer;
}

.check-box {
  width: 44px;
  height: 36px;
  border-radius: 7px;
  border: 1px solid #cbd5e1;
  background: #f1f5f9;
  color: #ffffff;
  font-size: 1.05rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.check-box.marcado {
  background: #38bdf8;
  border-color: #0284c7;
  color: #0f172a;
}

.payload-box {
  margin-top: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
  font-size: 0.85rem;
}

.payload-box pre {
  margin: 0.4rem 0 0;
  font-size: 0.8rem;
  overflow-x: auto;
}

.acciones-rapidas,
.footer-envio {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.footer-envio {
  justify-content: flex-end;
  margin-top: 1rem;
}

button,
.btn-link,
.btn-ir-autorizar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.45rem 0.85rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #0f172a;
}

.btn-primario,
.btn-enviar,
.btn-ir-autorizar {
  background: #0f766e;
  border-color: #0f766e;
  color: #ffffff;
}

.btn-borrar {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #991b1b;
}

button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.aviso {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-weight: 600;
}

.aviso.info {
  background: #e0f2fe;
  color: #075985;
}

.aviso.ok {
  background: #dcfce7;
  color: #166534;
}

.aviso.err {
  background: #fee2e2;
  color: #991b1b;
}
</style>