<template>
  <div class="bloque-dni">
    <div :class="['visor-dni-claro', errorDni ? 'visor-invalido' : '']">
      <div class="visor-fila-sup">
        <label for="visor-dni-input">Número de Documento (DNI)</label>
        <span v-if="modelValue" class="contador-digitos">{{ modelValue.length }}/8 dígitos</span>
      </div>
      <input
        id="visor-dni-input"
        :value="dniFormateado"
        type="text"
        inputmode="none"
        readonly
        placeholder="Ingresá los 8 dígitos..."
        class="visor-input-grande"
        aria-label="Número de documento ingresado"
      />
      <small v-if="errorDni" class="texto-error-campo" role="alert">
        {{ errorDni }}
      </small>
    </div>

    <div class="teclado-tactil-grid" role="group" aria-label="Teclado numérico táctil">
      <button
        v-for="n in ['1', '2', '3', '4', '5', '6', '7', '8', '9']"
        :key="n"
        type="button"
        class="tecla-tactil"
        :disabled="buscando"
        @click="ingresarDigito(n)"
      >
        {{ n }}
      </button>
      <button
        type="button"
        class="tecla-tactil tecla-auxiliar"
        :disabled="buscando || !modelValue"
        @click="limpiar"
      >
        Limpiar
      </button>
      <button
        type="button"
        class="tecla-tactil"
        :disabled="buscando"
        @click="ingresarDigito('0')"
      >
        0
      </button>
      <button
        type="button"
        class="tecla-tactil tecla-auxiliar"
        :disabled="buscando || !modelValue"
        @click="borrar"
      >
        ← Borrar
      </button>
    </div>

    <button
      type="button"
      class="btn-primario-grande"
      :disabled="buscando || !esDniValido"
      @click="emitirBusqueda"
    >
      {{ buscando ? 'Buscando autorización...' : 'Buscar e incluir al retiro' }}
    </button>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  buscando: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'buscar'])

const errorDni = ref('')

const esDniValido = computed(() => /^\d{8}$/.test(props.modelValue))

const dniFormateado = computed(() => {
  const limpio = String(props.modelValue || '').replace(/\D/g, '')
  if (!limpio) return ''
  return limpio.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
})

watch(
  () => props.modelValue,
  (val) => {
    if (!val) {
      errorDni.value = ''
    }
  }
)

function validar(valor) {
  if (!valor) {
    errorDni.value = ''
    return
  }
  if (!/^\d+$/.test(valor)) {
    errorDni.value = 'Solo se permiten caracteres numéricos.'
  } else if (valor.length < 8) {
    errorDni.value = 'El DNI debe tener 8 dígitos numéricos.'
  } else {
    errorDni.value = ''
  }
}

function ingresarDigito(digito) {
  if (props.modelValue.length >= 8) {
    errorDni.value = 'El DNI debe tener exactamente 8 dígitos.'
    return
  }
  const nuevo = props.modelValue + digito
  emit('update:modelValue', nuevo)
  validar(nuevo)
}

function borrar() {
  const nuevo = props.modelValue.slice(0, -1)
  emit('update:modelValue', nuevo)
  validar(nuevo)
}

function limpiar() {
  emit('update:modelValue', '')
  errorDni.value = ''
}

function emitirBusqueda() {
  if (!esDniValido.value) {
    errorDni.value = 'Ingresá un DNI válido de 8 dígitos.'
    return
  }
  emit('buscar')
}
</script>

<style scoped>
.bloque-dni {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.visor-dni-claro {
  background: #f8fafc;
  border: 2px solid #cbd5e1;
  border-radius: 10px;
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.visor-dni-claro.visor-invalido {
  border-color: #b91c1c;
  background: #fef2f2;
}

.visor-fila-sup {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.78rem;
  font-weight: 600;
  color: #64748b;
}

.contador-digitos {
  color: #2563eb;
  font-weight: 700;
}

.visor-input-grande {
  width: 100%;
  border: none;
  background: transparent;
  color: #1e293b;
  font-size: 2rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.03em;
  outline: none;
}

.visor-input-grande::placeholder {
  color: #94a3b8;
  font-weight: 500;
  font-size: 1.3rem;
}

.texto-error-campo {
  color: #b91c1c;
  font-size: 0.8rem;
  font-weight: 600;
}

.teclado-tactil-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.6rem;
}

.tecla-tactil {
  min-height: 56px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #1e293b;
  font-size: 1.3rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.tecla-tactil:active:not(:disabled) {
  background: #eff6ff;
  border-color: #2563eb;
  color: #1d4ed8;
}

.tecla-tactil.tecla-auxiliar {
  background: #f8fafc;
  color: #475569;
  font-size: 0.92rem;
}

.btn-primario-grande {
  min-height: 52px;
  border-radius: 8px;
  border: 1px solid #2563eb;
  background: #2563eb;
  color: #ffffff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-primario-grande:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primario-grande:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>