<template>
  <div
    class="modal-backdrop"
    role="dialog"
    aria-modal="true"
    aria-labelledby="titulo-detalle-pedido"
  >
    <div class="modal-panel">
      <header class="modal-header">
        <div>
          <div class="header-titulo-fila">
            <h2 id="titulo-detalle-pedido">Pedido #{{ detalle.idPedido }}</h2>
            <span :class="['estado-pill', `estado-${detalle.estado}`]">
              {{ formatearEstadoPedido(detalle.estado) }}
            </span>
            <span v-if="esDiaAnterior" class="lectura-pill">Solo lectura (fecha pasada)</span>
          </div>
          <p class="origen-pedido">
            <strong>Sector:</strong> {{ nombreSector }}
            <span v-if="detalle.fecha_desde">
              · <strong>Fecha:</strong> {{ formatearFechaDdMmAaaa(detalle.fecha_desde) }}
            </span>
            <span v-if="detalle.periodicidad">
              · <strong>Periodicidad:</strong> {{ detalle.periodicidad }}
            </span>
          </p>
          <p class="subtitulo">
            Estado actual: <strong>{{ formatearEstadoPedido(detalle.estado) }}</strong>
            <span v-if="detalle.motivo_rechazo">
              · <strong>Motivo de rechazo:</strong> {{ detalle.motivo_rechazo }}
            </span>
          </p>
        </div>
        <button
          type="button"
          class="btn-cerrar"
          aria-label="Cerrar detalle del pedido"
          :disabled="guardando"
          @click="$emit('cerrar')"
        >
          ✕
        </button>
      </header>

      <section
        v-if="esDiaAnterior || detalle.estado === 'rechazado'"
        class="aviso-solo-lectura"
        role="note"
      >
        <span v-if="esDiaAnterior">
          Este pedido corresponde a una fecha anterior a hoy y se muestra en modo de solo lectura.
        </span>
        <span v-else>
          Este pedido fue rechazado y no admite modificaciones de autorización.
        </span>
      </section>

      <section class="resumen-comparador" aria-label="Cantidades pedidas y autorizadas">
        <div class="stat-box">
          <span>Solicitudes Pedidas</span>
          <strong>{{ totalSolicitudesPedidas }}</strong>
        </div>
        <div class="stat-box destacado">
          <span>Quedarán Autorizadas</span>
          <strong>{{ totalSimuladoAutorizado }}</strong>
        </div>
      </section>

      <section
        v-if="desgloseAgrupado.length > 0"
        class="desglose-box"
        aria-label="Totales por comida y tipo de menú"
      >
        <span class="acciones-etiqueta">Totales por comida y menú (simulado)</span>
        <div class="desglose-chips">
          <div v-for="item in desgloseAgrupado" :key="item.clave" class="chip-desglose">
            <span>{{ item.comida }} · {{ item.menu }}</span>
            <strong>{{ item.autorizadas }} / {{ item.pedidas }} aut.</strong>
          </div>
        </div>
      </section>

      <section class="acciones-masivas" aria-label="Acciones masivas de autorización">
        <span class="acciones-etiqueta">Acciones rápidas</span>
        <div class="acciones-masivas-botones">
          <button
            type="button"
            class="btn-accion btn-regulares"
            :disabled="guardando || bloqueadoEdicion"
            @click="autorizarSoloRegulares"
          >
            Autorizar todas las Regulares
          </button>
          <button
            type="button"
            class="btn-accion btn-todo"
            :disabled="guardando || bloqueadoEdicion"
            @click="autorizarTodo"
          >
            Autorizar pedido completo
          </button>
          <button
            type="button"
            class="btn-accion btn-ninguna"
            :disabled="guardando || bloqueadoEdicion"
            @click="desautorizarTodo"
          >
            Marcar todas como No autorizadas
          </button>
        </div>
      </section>

      <section class="lista-solicitudes" aria-label="Detalle nominado de solicitudes">
        <table class="tabla-sol">
          <thead>
            <tr>
              <th scope="col">Solicitud</th>
              <th scope="col">Personal</th>
              <th scope="col">Comida</th>
              <th scope="col">Tipo de menú</th>
              <th scope="col">Condición</th>
              <th scope="col">Autorización</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="sol in solicitudesEditables"
              :key="sol.idSolicitud"
              :class="{ 'fila-desmarcada': sol.estado !== 'AUTORIZADA' }"
            >
              <td class="dato-mono">#{{ sol.idSolicitud }}</td>
              <td>
                <span class="nombre-principal">{{ resolverNombrePersonal(sol) }}</span>
              </td>
              <td>
                <span class="nombre-principal">{{ resolverNombreComida(sol) }}</span>
              </td>
              <td>
                <span class="menu-badge">{{ resolverNombreMenu(sol) }}</span>
              </td>
              <td>
                <span :class="['tag-cond', esExcepcion(sol) ? 'excepcion' : 'regular']">
                  {{ esExcepcion(sol) ? 'Excepción' : 'Regular' }}
                </span>
              </td>
              <td>
                <button
                  type="button"
                  :class="[
                    'btn-toggle-autorizacion',
                    sol.estado === 'AUTORIZADA' ? 'autorizada' : 'no-autorizada',
                  ]"
                  :aria-pressed="sol.estado === 'AUTORIZADA'"
                  :disabled="guardando || bloqueadoEdicion"
                  @click="alternarSolicitud(sol, sol.estado !== 'AUTORIZADA')"
                >
                  <span class="icono-estado">
                    {{ sol.estado === 'AUTORIZADA' ? '✓' : '✕' }}
                  </span>
                  <span>
                    {{ sol.estado === 'AUTORIZADA' ? 'Autorizada' : 'No autorizada' }}
                  </span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section
        v-if="detalle.estado === 'confirmado' && !bloqueadoEdicion"
        class="bloque-rechazo"
      >
        <label for="motivo-rechazo">Rechazar pedido completo (motivo obligatorio)</label>
        <div class="fila-rechazo">
          <input
            id="motivo-rechazo"
            v-model="motivoRechazo"
            type="text"
            placeholder="Ej: Supera el cupo asignado sin justificación"
            :disabled="guardando"
            @input="errorMotivoLocal = ''"
          />
          <button
            type="button"
            class="btn-rechazar"
            :disabled="guardando || !motivoRechazo.trim()"
            @click="solicitarRechazo"
          >
            Rechazar pedido
          </button>
        </div>
        <p v-if="errorMotivoLocal" class="error-campo" role="alert">
          {{ errorMotivoLocal }}
        </p>
      </section>

      <footer class="modal-footer">
        <button
          type="button"
          class="btn-cancelar"
          :disabled="guardando"
          @click="$emit('cerrar')"
        >
          {{ bloqueadoEdicion ? 'Cerrar' : 'Cancelar' }}
        </button>
        <button
          v-if="!bloqueadoEdicion"
          type="button"
          class="btn-confirmar"
          :disabled="guardando"
          @click="solicitarConfirmacionAutorizacion"
        >
          {{ guardando ? 'Guardando...' : 'Confirmar autorización' }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  detalle: {
    type: Object,
    required: true,
  },
  guardando: {
    type: Boolean,
    default: false,
  },
  sectores: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['cerrar', 'confirmar-autorizacion', 'confirmar-rechazo'])

const PERSONAL_POR_ID = {
  1: 'Soyadmin, Juan',
  2: 'Detal, Fulano',
  3: 'Perez, Mengano',
  4: 'Gomez, Pascuala',
  5: 'Gonzalez, Agus',
}

const COMIDAS_POR_ID = {
  1: 'Desayuno',
  2: 'Almuerzo',
  3: 'Merienda',
  4: 'Cena',
}

const MENUS_POR_ID = {
  1: 'General',
  2: 'Vegetariano',
  3: 'Celíaco',
}

const solicitudesEditables = ref([])
const motivoRechazo = ref('')
const errorMotivoLocal = ref('')

watch(
  () => props.detalle,
  (nuevoDetalle) => {
    motivoRechazo.value = nuevoDetalle?.motivo_rechazo || ''
    errorMotivoLocal.value = ''
    solicitudesEditables.value = (nuevoDetalle?.solicitudes || []).map((s) => ({
      ...s,
      estado: s.estadoAutorizacion === 'autorizada' ? 'AUTORIZADA' : 'NO_AUTORIZADA',
    }))
  },
  { immediate: true }
)

function fechaLocalIso() {
  const hoy = new Date()
  const anio = hoy.getFullYear()
  const mes = String(hoy.getMonth() + 1).padStart(2, '0')
  const dia = String(hoy.getDate()).padStart(2, '0')
  return `${anio}-${mes}-${dia}`
}

function formatearFechaDdMmAaaa(valorFecha) {
  if (!valorFecha) return '-'
  const iso = String(valorFecha).slice(0, 10)
  const partes = iso.split('-')
  if (partes.length !== 3) return valorFecha
  return `${partes[2]}/${partes[1]}/${partes[0]}`
}

function formatearEstadoPedido(estado) {
  const mapa = {
    confirmado: 'Confirmado',
    autorizado: 'Autorizado',
    rechazado: 'Rechazado',
  }
  return mapa[String(estado || '').toLowerCase()] || estado || '-'
}

const mapaSectoresModal = computed(() => {
  const map = {}
  for (const sec of props.sectores || []) {
    if (sec?.id !== undefined) {
      map[Number(sec.id)] = sec.nombre
    }
  }
  return map
})

const nombreSector = computed(() => {
  if (props.detalle?.nombreSector) return props.detalle.nombreSector
  const idSector = Number(props.detalle?.idSector)
  if (Number.isInteger(idSector) && mapaSectoresModal.value[idSector]) {
    return mapaSectoresModal.value[idSector]
  }
  return idSector ? `Sector #${idSector}` : 'Sin sector'
})

function resolverNombrePersonal(sol) {
  if (sol?.nombrePersonal) return sol.nombrePersonal
  const id = Number(sol?.idPersonal)
  if (Number.isInteger(id) && PERSONAL_POR_ID[id]) {
    return PERSONAL_POR_ID[id]
  }
  return id ? `Personal #${id}` : 'Sin asignar'
}

function resolverNombreComida(sol) {
  if (sol?.nombreTipoComida) return sol.nombreTipoComida
  const id = Number(sol?.idTipoComida)
  if (Number.isInteger(id) && COMIDAS_POR_ID[id]) {
    return COMIDAS_POR_ID[id]
  }
  return id ? `Comida #${id}` : 'Sin comida'
}

function resolverNombreMenu(sol) {
  if (sol?.nombreTipoMenu) return sol.nombreTipoMenu
  const id = Number(sol?.idTipoMenu)
  if (Number.isInteger(id) && MENUS_POR_ID[id]) {
    return MENUS_POR_ID[id]
  }
  return id ? `Menú #${id}` : 'Menú estándar'
}

const esDiaAnterior = computed(() => {
  if (!props.detalle?.fecha_desde) return false
  return String(props.detalle.fecha_desde).slice(0, 10) < fechaLocalIso()
})

const bloqueadoEdicion = computed(() => {
  const estado = String(props.detalle?.estado || '').toLowerCase()
  return esDiaAnterior.value || estado === 'rechazado'
})

const totalSolicitudesPedidas = computed(() => {
  if (typeof props.detalle?.cantidad_pedida === 'number') {
    return props.detalle.cantidad_pedida
  }
  return solicitudesEditables.value.length
})

const totalSimuladoAutorizado = computed(() =>
  solicitudesEditables.value.filter((s) => s.estado === 'AUTORIZADA').length
)

const desgloseAgrupado = computed(() => {
  const mapa = new Map()
  for (const sol of solicitudesEditables.value) {
    const comida = resolverNombreComida(sol)
    const menu = resolverNombreMenu(sol)
    const clave = `${comida}__${menu}`
    if (!mapa.has(clave)) {
      mapa.set(clave, { clave, comida, menu, pedidas: 0, autorizadas: 0 })
    }
    const entry = mapa.get(clave)
    entry.pedidas += 1
    if (sol.estado === 'AUTORIZADA') {
      entry.autorizadas += 1
    }
  }
  return Array.from(mapa.values())
})

function esExcepcion(sol) {
  const cond = String(sol.condicionCupo || '').toLowerCase()
  return cond === 'excepcion'
}

function alternarSolicitud(sol, marcada) {
  if (bloqueadoEdicion.value) return
  sol.estado = marcada ? 'AUTORIZADA' : 'NO_AUTORIZADA'
}

function autorizarSoloRegulares() {
  if (bloqueadoEdicion.value) return
  solicitudesEditables.value.forEach((s) => {
    s.estado = esExcepcion(s) ? 'NO_AUTORIZADA' : 'AUTORIZADA'
  })
}

function autorizarTodo() {
  if (bloqueadoEdicion.value) return
  solicitudesEditables.value.forEach((s) => {
    s.estado = 'AUTORIZADA'
  })
}

function desautorizarTodo() {
  if (bloqueadoEdicion.value) return
  solicitudesEditables.value.forEach((s) => {
    s.estado = 'NO_AUTORIZADA'
  })
}

function solicitarConfirmacionAutorizacion() {
  if (bloqueadoEdicion.value) return
  emit('confirmar-autorizacion', {
    idPedido: props.detalle.idPedido,
    ultima_modificacion: props.detalle.ultima_modificacion ?? null,
    solicitudes: solicitudesEditables.value.map((s) => ({
      idSolicitud: s.idSolicitud,
      estado: s.estado,
    })),
    resumenSolicitudes: solicitudesEditables.value.map((s) => ({
      idSolicitud: s.idSolicitud,
      persona: resolverNombrePersonal(s),
      comida: resolverNombreComida(s),
      menu: resolverNombreMenu(s),
      estado: s.estado,
    })),
  })
}

function solicitarRechazo() {
  if (bloqueadoEdicion.value) return
  const limpio = motivoRechazo.value.trim()
  if (!limpio) {
    errorMotivoLocal.value = 'Debe ingresar un motivo obligatorio para rechazar el pedido.'
    return
  }
  errorMotivoLocal.value = ''
  emit('confirmar-rechazo', {
    idPedido: props.detalle.idPedido,
    motivo: limpio,
  })
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.58);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 50;
}

.modal-panel {
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 22px 48px rgba(15, 23, 42, 0.22);
  width: 100%;
  max-width: 840px;
  max-height: 90vh;
  overflow-y: auto;
  padding: 1.35rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 0.85rem;
}

.header-titulo-fila {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.55rem;
}

.header-titulo-fila h2 {
  margin: 0;
  font-size: 1.35rem;
  color: #0f172a;
}

.estado-pill {
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  padding: 0.18rem 0.65rem;
  font-size: 0.78rem;
  font-weight: 700;
}

.estado-pill.estado-autorizado {
  background: #dcfce7;
  color: #166534;
  border-color: #86efac;
}

.estado-pill.estado-rechazado {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fca5a5;
}

.lectura-pill {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fde68a;
  border-radius: 999px;
  padding: 0.18rem 0.65rem;
  font-size: 0.78rem;
  font-weight: 700;
}

.origen-pedido {
  margin: 0.35rem 0 0;
  font-size: 0.9rem;
  color: #0f172a;
}

.subtitulo {
  margin: 0.2rem 0 0;
  color: #475569;
  font-size: 0.86rem;
}

.aviso-solo-lectura {
  background: #fffbeb;
  border: 1px solid #fcd34d;
  color: #92400e;
  border-radius: 8px;
  padding: 0.65rem 0.85rem;
  font-size: 0.86rem;
  font-weight: 600;
}

.resumen-comparador {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.8rem;
}

.stat-box {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 0.8rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #334155;
  font-weight: 600;
}

.stat-box strong {
  font-size: 1.2rem;
  color: #0f172a;
}

.stat-box.destacado {
  background: #f0fdfa;
  border-color: #0f766e;
  color: #115e59;
}

.stat-box.destacado strong {
  color: #0f766e;
}

.desglose-box,
.acciones-masivas {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.75rem 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.desglose-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.chip-desglose {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 0.35rem 0.65rem;
  font-size: 0.8rem;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  color: #1e293b;
}

.acciones-etiqueta {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #64748b;
}

.acciones-masivas-botones {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.btn-accion.btn-regulares {
  background: #ffffff;
  border-color: #94a3b8;
  color: #0f172a;
}

.btn-accion.btn-regulares:hover:not(:disabled) {
  background: #f1f5f9;
}

.btn-accion.btn-todo {
  background: #ecfdf5;
  border-color: #6ee7b7;
  color: #065f46;
}

.btn-accion.btn-todo:hover:not(:disabled) {
  background: #d1fae5;
}

.btn-accion.btn-ninguna {
  background: #fff1f2;
  border-color: #fda4af;
  color: #9f1239;
}

.btn-accion.btn-ninguna:hover:not(:disabled) {
  background: #ffe4e6;
}

.lista-solicitudes {
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.tabla-sol {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.tabla-sol th {
  background: #f8fafc;
  color: #475569;
  font-size: 0.76rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 0.65rem 0.75rem;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
}

.tabla-sol td {
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid #f1f5f9;
  text-align: left;
  vertical-align: middle;
}

.tabla-sol tr:last-child td {
  border-bottom: none;
}

.fila-desmarcada {
  background: #fffafa;
}

.dato-mono {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  color: #475569;
}

.nombre-principal {
  font-weight: 600;
  color: #0f172a;
}

.menu-badge {
  display: inline-block;
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 0.16rem 0.5rem;
  font-size: 0.78rem;
  font-weight: 600;
}

.tag-cond {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
}

.tag-cond.regular {
  background: #e0f2fe;
  color: #075985;
  border: 1px solid #bae6fd;
}

.tag-cond.excepcion {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fde68a;
}

.btn-toggle-autorizacion {
  min-height: 36px;
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.82rem;
  font-weight: 700;
  transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.btn-toggle-autorizacion.autorizada {
  background: #dcfce7;
  border-color: #86efac;
  color: #166534;
}

.btn-toggle-autorizacion.autorizada:hover:not(:disabled) {
  background: #bbf7d0;
}

.btn-toggle-autorizacion.no-autorizada {
  background: #f1f5f9;
  border-color: #cbd5e1;
  color: #475569;
}

.btn-toggle-autorizacion.no-autorizada:hover:not(:disabled) {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #991b1b;
}

.icono-estado {
  font-size: 0.8rem;
  line-height: 1;
}

.bloque-rechazo {
  border-top: 1px solid #e2e8f0;
  padding-top: 0.85rem;
}

.bloque-rechazo label {
  font-size: 0.88rem;
  font-weight: 700;
  color: #334155;
}

.fila-rechazo {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.45rem;
}

.fila-rechazo input {
  flex: 1;
  min-height: 40px;
  padding: 0.5rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 0.9rem;
}

.fila-rechazo input:focus {
  outline: none;
  border-color: #0f766e;
}

.error-campo {
  margin: 0.35rem 0 0;
  font-size: 0.82rem;
  font-weight: 600;
  color: #b91c1c;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  border-top: 1px solid #e2e8f0;
  padding-top: 0.85rem;
}

button {
  min-height: 40px;
  padding: 0.45rem 0.95rem;
  border-radius: 8px;
  font-size: 0.86rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #0f172a;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.btn-cerrar {
  min-height: 36px;
  width: 36px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-cancelar:hover:not(:disabled),
.btn-cerrar:hover:not(:disabled) {
  background: #e2e8f0;
}

.btn-confirmar {
  background: #0f766e;
  border-color: #0f766e;
  color: #ffffff;
}

.btn-confirmar:hover:not(:disabled) {
  background: #115e59;
}

.btn-rechazar {
  background: #dc2626;
  border-color: #dc2626;
  color: #ffffff;
}

.btn-rechazar:hover:not(:disabled) {
  background: #b91c1c;
}

button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 767px) {
  .resumen-comparador {
    grid-template-columns: 1fr;
  }

  .fila-rechazo {
    flex-direction: column;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .modal-footer button {
    width: 100%;
  }
}
</style>