<template>
  <div
    class="modal-kiosko-backdrop"
    role="dialog"
    aria-modal="true"
    aria-labelledby="modal-conf-title"
  >
    <div class="modal-kiosko-card">
      <h2 id="modal-conf-title">Confirmar registro de entrega</h2>
      <p class="modal-subtexto">
        Verificá las comidas a entregar y confirmá o cambiá quién retira las viandas.
      </p>
      <p v-if="resultadoIncierto" class="texto-error-campo" role="alert">
        No se puede volver a enviar hasta comprobar si la entrega quedó registrada.
      </p>

      <div class="caja-responsable-modal">
        <div class="responsable-cabecera-modal">
          <div>
            <span class="etiqueta-resp-modal">Responsable efectivo del retiro</span>
            <strong class="valor-resp-modal">{{ descripcionResponsable }}</strong>
          </div>

          <div class="selector-dos-opciones">
            <button
              type="button"
              :class="['btn-modo-busq', modoResponsable === 'incluida' ? 'activo' : '']"
              @click="cambiarModo('incluida')"
            >
              {{ personas.length === 1 ? 'El mismo titular' : 'Persona de la lista' }}
            </button>
            <button
              type="button"
              :class="['btn-modo-busq', modoResponsable === 'tercero' ? 'activo' : '']"
              @click="cambiarModo('tercero')"
            >
              Otra persona / Tercero
            </button>
          </div>
        </div>

        <div v-if="modoResponsable === 'incluida' && personas.length > 1" class="bloque-select-resp">
          <label for="select-responsable-modal" class="label-estandar">
            Seleccioná qué persona de la lista retira las viandas
          </label>
          <select
            id="select-responsable-modal"
            v-model="idResponsable"
            class="input-claro-tactil"
            @change="errorResponsable = ''"
          >
            <option value="">Seleccioná quién retira...</option>
            <option v-for="p in personas" :key="p.idPersonal" :value="p.idPersonal">
              {{ p.apellido }}, {{ p.nombre }} — DNI {{ formatearPuntos(p.dni) }}
            </option>
          </select>
        </div>

        <div v-if="modoResponsable === 'tercero'" class="grilla-tercero-clara">
          <div>
            <label for="dni-tercero-modal" class="label-estandar">
              DNI de quien retira (8 dígitos)
            </label>
            <input
              id="dni-tercero-modal"
              v-model="tercero.dni"
              type="text"
              inputmode="numeric"
              maxlength="8"
              placeholder="8 dígitos numéricos"
              class="input-claro-tactil"
              @input="validarDniTercero"
            />
          </div>
          <div>
            <label for="nombre-tercero-modal" class="label-estandar">
              Apellido y Nombre de quien retira
            </label>
            <input
              id="nombre-tercero-modal"
              v-model="tercero.nombre"
              type="text"
              placeholder="Ej: González, Agustín"
              class="input-claro-tactil"
              @input="errorResponsable = ''"
            />
          </div>
        </div>

        <small v-if="errorResponsable" class="texto-error-campo" role="alert">
          {{ errorResponsable }}
        </small>
      </div>

      <ul class="lista-confirmacion-clara">
        <li v-for="item in items" :key="item.idSolicitud">
          <div>
            <strong>{{ item.apellido }}, {{ item.nombre }}</strong>
            <span class="res-detalle">
              DNI {{ formatearPuntos(item.dni) }} · {{ item.sector }}
            </span>
          </div>
          <div class="chips-confirmacion">
            <span class="chip-comida-conf">{{ item.comida }}</span>
            <span class="chip-menu-conf">Menú {{ item.menu }}</span>
          </div>
        </li>
      </ul>

      <div class="modal-acciones-pie">
        <button
          type="button"
          class="btn-secundario-claro"
          :disabled="enviando"
          @click="$emit('cerrar')"
        >
          Volver
        </button>
        <button
          type="button"
          class="btn-primario-tactil"
          :disabled="enviando || resultadoIncierto"
          @click="validarYConfirmar"
        >
          {{ enviando ? 'Registrando entrega...' : 'Sí, confirmar entrega' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  personas: {
    type: Array,
    required: true,
  },
  items: {
    type: Array,
    required: true,
  },
  enviando: {
    type: Boolean,
    default: false,
  },
  resultadoIncierto: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['cerrar', 'confirmar'])

const modoResponsable = ref('incluida')
const idResponsable = ref(props.personas[0]?.idPersonal || '')
const tercero = ref({ dni: '', nombre: '' })
const errorResponsable = ref('')

function formatearPuntos(valor) {
  const limpio = String(valor || '').replace(/\D/g, '')
  return limpio.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

const descripcionResponsable = computed(() => {
  if (modoResponsable.value === 'tercero') {
    const nom = tercero.value.nombre.trim() || 'Sin nombre'
    const doc = tercero.value.dni ? formatearPuntos(tercero.value.dni) : 'Sin DNI'
    return `${nom} (DNI ${doc} · Tercero)`
  }
  if (props.personas.length === 1) {
    const p = props.personas[0]
    return `${p.apellido}, ${p.nombre} (DNI ${formatearPuntos(p.dni)})`
  }
  const p = props.personas.find((x) => Number(x.idPersonal) === Number(idResponsable.value))
  return p ? `${p.apellido}, ${p.nombre} (DNI ${formatearPuntos(p.dni)})` : 'Sin seleccionar'
})

function cambiarModo(nuevoModo) {
  modoResponsable.value = nuevoModo
  errorResponsable.value = ''
}

function validarDniTercero() {
  tercero.value.dni = tercero.value.dni.replace(/\D/g, '').slice(0, 8)
  if (tercero.value.dni && tercero.value.dni.length < 8) {
    errorResponsable.value = 'El DNI debe tener exactamente 8 dígitos numéricos.'
  } else {
    errorResponsable.value = ''
  }
}

function validarYConfirmar() {
  errorResponsable.value = ''

  if (modoResponsable.value === 'tercero') {
    const dniT = tercero.value.dni.trim()
    const nomT = tercero.value.nombre.trim()
    if (!/^\d{8}$/.test(dniT)) {
      errorResponsable.value =
        'El DNI de la persona que retira debe tener exactamente 8 dígitos numéricos.'
      return
    }
    if (nomT.length < 3) {
      errorResponsable.value = 'Ingresá el apellido y nombre de la persona que retira.'
      return
    }
    emit('confirmar', {
      tercero: { dni: dniT, nombre: nomT },
    })
    return
  }

  if (props.personas.length > 1 && !idResponsable.value) {
    errorResponsable.value = 'Seleccioná qué persona de la lista retira las viandas.'
    return
  }

  const idElegido =
    props.personas.length === 1 ? props.personas[0].idPersonal : Number(idResponsable.value)

  emit('confirmar', {
    id_personal: idElegido,
  })
}
</script>

<style scoped>
.modal-kiosko-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
  z-index: 90;
}

.modal-kiosko-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 1.4rem;
  max-width: 640px;
  width: 100%;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.22);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.modal-kiosko-card h2 {
  margin: 0;
  font-size: 1.3rem;
}

.modal-subtexto {
  margin: 0.2rem 0 0;
  font-size: 0.9rem;
  color: #475569;
}

.caja-responsable-modal {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 0.95rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.responsable-cabecera-modal {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.etiqueta-resp-modal {
  display: block;
  font-size: 0.76rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #0f766e;
}

.valor-resp-modal {
  font-size: 0.98rem;
  color: #0f172a;
}

.selector-dos-opciones {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.35rem;
  background: #f1f5f9;
  padding: 0.3rem;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
}

.btn-modo-busq {
  min-height: 44px;
  padding: 0.35rem 0.75rem;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #334155;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-modo-busq.activo {
  background: #0f766e;
  color: #ffffff;
}

.label-estandar {
  display: block;
  font-size: 0.82rem;
  font-weight: 700;
  color: #334155;
  margin-bottom: 0.25rem;
}

.input-claro-tactil {
  min-height: 48px;
  padding: 0.45rem 0.8rem;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #0f172a;
  font-size: 0.95rem;
  width: 100%;
  box-sizing: border-box;
}

.grilla-tercero-clara {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.texto-error-campo {
  color: #b91c1c;
  font-size: 0.82rem;
  font-weight: 700;
}

.lista-confirmacion-clara {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 240px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.lista-confirmacion-clara li {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.7rem 0.95rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}

.res-detalle {
  display: block;
  font-size: 0.83rem;
  color: #64748b;
  margin-top: 0.15rem;
}

.chips-confirmacion {
  display: flex;
  gap: 0.4rem;
  align-items: center;
}

.chip-comida-conf {
  background: #ccfbf1;
  color: #0f766e;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.82rem;
}

.chip-menu-conf {
  background: #e2e8f0;
  color: #334155;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.82rem;
}

.modal-acciones-pie {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
}

.btn-secundario-claro,
.btn-primario-tactil {
  min-height: 50px;
  padding: 0.5rem 1.15rem;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-secundario-claro {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #0f172a;
}

.btn-primario-tactil {
  background: #0f766e;
  border: 1px solid #0f766e;
  color: #ffffff;
}

@media (max-width: 767px) {
  .grilla-tercero-clara {
    grid-template-columns: 1fr;
  }
}
</style>
