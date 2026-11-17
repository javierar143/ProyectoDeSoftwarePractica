<template>
  <div
    class="modal-confirmacion-backdrop"
    role="alertdialog"
    aria-modal="true"
  >
    <div class="modal-confirmacion-box">
      <h3>Confirmar operación</h3>

      <div v-if="confirmacion.tipo === 'autorizar'" class="detalle-confirmacion-lista">
        <p>
          ¿Confirmás registrar la autorización del
          <strong>pedido #{{ confirmacion.payload?.idPedido }}</strong>?
        </p>
        <p class="sub-resumen">
          Autorizadas:
          <strong>
            {{
              (confirmacion.payload?.resumenSolicitudes || []).filter(
                (r) => r.estado === 'AUTORIZADA'
              ).length
            }}
          </strong>
          de
          <strong>{{ (confirmacion.payload?.resumenSolicitudes || []).length }}</strong>
        </p>
        <ul class="lista-resumen-sol">
          <li
            v-for="item in confirmacion.payload?.resumenSolicitudes || []"
            :key="item.idSolicitud"
            :class="item.estado === 'AUTORIZADA' ? 'item-aut' : 'item-no-aut'"
          >
            <span>
              <strong>#{{ item.idSolicitud }}</strong> · {{ item.persona }} —
              <strong>{{ item.comida }}</strong> ({{ item.menu }})
            </span>
            <span class="badge-mini">
              {{ item.estado === 'AUTORIZADA' ? '✓ Autorizada' : '✕ No autorizada' }}
            </span>
          </li>
        </ul>
      </div>

      <p v-else>
        ¿Confirmás rechazar el pedido #{{ confirmacion.payload?.idPedido }} completo por el
        motivo indicado? Esta acción no se puede deshacer.
      </p>

      <div class="confirmacion-acciones">
        <button type="button" :disabled="guardando" @click="$emit('cancelar')">
          Volver
        </button>
        <button
          type="button"
          class="btn-ejecutar"
          :disabled="guardando"
          @click="$emit('confirmar')"
        >
          {{ guardando ? 'Procesando...' : 'Sí, confirmar' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  confirmacion: {
    type: Object,
    required: true,
  },
  guardando: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['cancelar', 'confirmar'])
</script>

<style scoped>
.modal-confirmacion-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 60;
}

.modal-confirmacion-box {
  background: #ffffff;
  border-radius: 12px;
  padding: 1.35rem;
  max-width: 490px;
  width: 100%;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.25);
}

.modal-confirmacion-box h3 {
  margin: 0 0 0.65rem;
}

.detalle-confirmacion-lista p {
  margin: 0 0 0.45rem;
}

.sub-resumen {
  font-size: 0.85rem;
  color: #475569;
}

.lista-resumen-sol {
  list-style: none;
  margin: 0.5rem 0 0;
  padding: 0;
  max-height: 220px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.84rem;
}

.lista-resumen-sol li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  border-radius: 7px;
  border: 1px solid #e2e8f0;
}

.lista-resumen-sol li.item-aut {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #14532d;
}

.lista-resumen-sol li.item-no-aut {
  background: #f8fafc;
  color: #64748b;
}

.badge-mini {
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
}

.confirmacion-acciones {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
}

button {
  min-height: 36px;
  padding: 0.38rem 0.8rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #0f172a;
}

.btn-ejecutar {
  background: #0f766e;
  border-color: #0f766e;
  color: #ffffff;
}

button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>