<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { crearPersona, modificarPersona } from '../services/personal'
import { normalizeApiError } from '@/services/api/error-handler'
import ApiErrorMessage from '@/modules/shared/components/ApiErrorMessage.vue'

const props = defineProps({
  abierto: {
    type: Boolean,
    default: false,
  },
  personaEditar: {
    type: Object,
    default: null,
  },
  tiposMenu: {
    type: Array,
    default: () => [],
  },
  idTipoPersonalFijo: {
    type: Number,
    required: true,
  },
  sectorNombre: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['cerrar', 'guardado', 'conflicto'])

const form = reactive({
  dni: '',
  nombre: '',
  apellido: '',
  idTipoMenu: '',
})

const erroresCampos = reactive({
  dni: '',
  nombre: '',
  apellido: '',
  idTipoMenu: '',
})

const guardando = ref(false)
const apiError = ref(null)

const esEdicion = computed(() => Boolean(props.personaEditar?.id))

watch(
  () => props.abierto,
  (abierto) => {
    if (abierto) {
      limpiarErrores()
      if (props.personaEditar) {
        form.dni = String(props.personaEditar.dni ?? '')
        form.nombre = props.personaEditar.nombre ?? ''
        form.apellido = props.personaEditar.apellido ?? ''
        form.idTipoMenu = props.personaEditar.id_tipo_menu ?? ''
      } else {
        form.dni = ''
        form.nombre = ''
        form.apellido = ''
        form.idTipoMenu = props.tiposMenu[0]?.id ?? ''
      }
    }
  }
)

function limpiarErrores() {
  erroresCampos.dni = ''
  erroresCampos.nombre = ''
  erroresCampos.apellido = ''
  erroresCampos.idTipoMenu = ''
  apiError.value = null
}

function validarCampo(campo) {
  const regexTexto = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s'-]+$/

  if (campo === 'dni') {
    const valor = form.dni.trim()
    if (!valor) {
      erroresCampos.dni = 'El DNI es obligatorio.'
    } else if (!/^\d+$/.test(valor)) {
      erroresCampos.dni = 'El DNI debe contener solo números.'
    } else if (valor.length < 7 || valor.length > 10) {
      erroresCampos.dni = 'El DNI debe tener entre 7 y 10 dígitos.'
    } else {
      erroresCampos.dni = ''
    }
  }

  if (campo === 'nombre') {
    const valor = form.nombre.trim()
    if (!valor) {
      erroresCampos.nombre = 'El nombre es obligatorio.'
    } else if (valor.length < 2 || valor.length > 50) {
      erroresCampos.nombre = 'El nombre debe tener entre 2 y 50 caracteres.'
    } else if (!regexTexto.test(valor)) {
      erroresCampos.nombre = 'El nombre solo puede contener letras y espacios.'
    } else {
      erroresCampos.nombre = ''
    }
  }

  if (campo === 'apellido') {
    const valor = form.apellido.trim()
    if (!valor) {
      erroresCampos.apellido = 'El apellido es obligatorio.'
    } else if (valor.length < 2 || valor.length > 50) {
      erroresCampos.apellido = 'El apellido debe tener entre 2 y 50 caracteres.'
    } else if (!regexTexto.test(valor)) {
      erroresCampos.apellido = 'El apellido solo puede contener letras y espacios.'
    } else {
      erroresCampos.apellido = ''
    }
  }

  if (campo === 'idTipoMenu') {
    if (!form.idTipoMenu) {
      erroresCampos.idTipoMenu = 'Seleccioná un tipo de menú.'
    } else {
      erroresCampos.idTipoMenu = ''
    }
  }
}

function validarFormulario() {
  validarCampo('dni')
  validarCampo('nombre')
  validarCampo('apellido')
  validarCampo('idTipoMenu')

  return (
    !erroresCampos.dni &&
    !erroresCampos.nombre &&
    !erroresCampos.apellido &&
    !erroresCampos.idTipoMenu
  )
}

async function enviarFormulario() {
  apiError.value = null

  if (!validarFormulario()) {
    return
  }

  guardando.value = true

  const payload = {
    dni: form.dni.trim(),
    nombre: form.nombre.trim(),
    apellido: form.apellido.trim(),
    idTipoPersonal: props.idTipoPersonalFijo,
    idTipoMenu: Number(form.idTipoMenu),
  }

  try {
    const resultado = esEdicion.value
      ? await modificarPersona(props.personaEditar.id, payload)
      : await crearPersona(payload)

    emit('guardado', resultado)
  } catch (error) {
    const normalizado = normalizeApiError(error)
    apiError.value = normalizado

    if (normalizado.fieldErrors) {
      if (normalizado.fieldErrors.dni) erroresCampos.dni = normalizado.fieldErrors.dni
      if (normalizado.fieldErrors.nombre) erroresCampos.nombre = normalizado.fieldErrors.nombre
      if (normalizado.fieldErrors.apellido) erroresCampos.apellido = normalizado.fieldErrors.apellido
    }
  } finally {
    guardando.value = false
  }
}

function manejarRefreshConflicto() {
  emit('conflicto')
  emit('cerrar')
}
</script>

<template>
  <div
    v-if="abierto"
    class="modal-backdrop"
    role="dialog"
    aria-modal="true"
    :aria-labelledby="esEdicion ? 'titulo-editar-personal' : 'titulo-nuevo-personal'"
  >
    <div class="modal-card">
      <header class="modal-header">
        <h2 :id="esEdicion ? 'titulo-editar-personal' : 'titulo-nuevo-personal'">
          {{ esEdicion ? 'Editar Personal Fijo' : 'Agregar Personal Fijo' }}
        </h2>
        <button
          type="button"
          class="btn-cerrar"
          aria-label="Cerrar formulario"
          :disabled="guardando"
          @click="emit('cerrar')"
        >
          ✕
        </button>
      </header>

      <p v-if="sectorNombre" class="sector-info">
        Sector asignado por el sistema: <strong>{{ sectorNombre }}</strong>
      </p>

      <ApiErrorMessage
        :error="apiError"
        @retry="enviarFormulario"
        @refresh="manejarRefreshConflicto"
      />

      <form novalidate @submit.prevent="enviarFormulario">
        <div class="campo-form">
          <label for="input-dni">DNI *</label>
          <input
            id="input-dni"
            v-model="form.dni"
            type="text"
            inputmode="numeric"
            maxlength="10"
            placeholder="Ej: 38123456"
            :disabled="guardando"
            @input="validarCampo('dni')"
            @blur="validarCampo('dni')"
          />
          <small v-if="erroresCampos.dni" class="error-texto">
            {{ erroresCampos.dni }}
          </small>
        </div>

        <div class="campo-form">
          <label for="input-apellido">Apellido *</label>
          <input
            id="input-apellido"
            v-model="form.apellido"
            type="text"
            maxlength="50"
            placeholder="Ej: Pérez"
            :disabled="guardando"
            @input="validarCampo('apellido')"
            @blur="validarCampo('apellido')"
          />
          <small v-if="erroresCampos.apellido" class="error-texto">
            {{ erroresCampos.apellido }}
          </small>
        </div>

        <div class="campo-form">
          <label for="input-nombre">Nombre *</label>
          <input
            id="input-nombre"
            v-model="form.nombre"
            type="text"
            maxlength="50"
            placeholder="Ej: María"
            :disabled="guardando"
            @input="validarCampo('nombre')"
            @blur="validarCampo('nombre')"
          />
          <small v-if="erroresCampos.nombre" class="error-texto">
            {{ erroresCampos.nombre }}
          </small>
        </div>

        <div class="campo-form">
          <label for="select-tipo-menu">Tipo de Menú *</label>
          <select
            id="select-tipo-menu"
            v-model="form.idTipoMenu"
            :disabled="guardando"
            @change="validarCampo('idTipoMenu')"
          >
            <option value="" disabled>Seleccioná un menú</option>
            <option
              v-for="menu in tiposMenu"
              :key="menu.id"
              :value="menu.id"
            >
              {{ menu.nombre }}
            </option>
          </select>
          <small v-if="erroresCampos.idTipoMenu" class="error-texto">
            {{ erroresCampos.idTipoMenu }}
          </small>
        </div>

        <footer class="modal-acciones">
          <button
            type="button"
            class="btn-secundario"
            :disabled="guardando"
            @click="emit('cerrar')"
          >
            Cancelar
          </button>
          <button
            type="submit"
            class="btn-primario"
            :disabled="guardando"
          >
            {{ guardando ? 'Guardando...' : esEdicion ? 'Guardar cambios' : 'Registrar persona' }}
          </button>
        </footer>
      </form>
    </div>
  </div>
</template>

<style scoped>
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

.modal-card {
  background: #ffffff;
  border-radius: 8px;
  width: 100%;
  max-width: 480px;
  padding: 1.5rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #1e293b;
}

.btn-cerrar {
  background: transparent;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #64748b;
  padding: 0.25rem 0.5rem;
}

.sector-info {
  margin: 0 0 1rem;
  padding: 0.5rem 0.75rem;
  background-color: #f1f5f9;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #334155;
}

.campo-form {
  display: flex;
  flex-direction: column;
  margin-bottom: 1rem;
}

.campo-form label {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 0.35rem;
  color: #334155;
}

.campo-form input,
.campo-form select {
  padding: 0.6rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.95rem;
}

.error-texto {
  color: #b91c1c;
  font-size: 0.82rem;
  margin-top: 0.25rem;
}

.modal-acciones {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.25rem;
}

.btn-primario {
  background-color: #2563eb;
  color: #ffffff;
  border: none;
  padding: 0.6rem 1.1rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primario:disabled,
.btn-secundario:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secundario {
  background-color: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
  padding: 0.6rem 1.1rem;
  border-radius: 6px;
  cursor: pointer;
}
</style>