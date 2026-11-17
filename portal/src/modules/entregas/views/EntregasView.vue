<template>
  <main
    class="kiosko-claro-viewport"
    @pointerdown="reiniciarTemporizadorInactividad"
    @keydown="reiniciarTemporizadorInactividad"
  >
    <div class="kiosko-contenedor">
      <!-- Aviso de pérdida de conexión (Healthcheck) -->
      <div v-if="!conexionActiva" class="alerta-kiosko alerta-error-red" role="alert">
        <span>⚠ Sin conexión con el servidor. Verificando conexión automáticamente...</span>
        <button type="button" class="btn-reintentar" @click="verificarSaludServidor">
          Reintentar ahora
        </button>
      </div>

      <!-- Encabezado Kiosco con estética institucional clara -->
      <header class="kiosko-encabezado">
        <div class="encabezado-info-turno">
          <div class="badge-turno-activo">
            <span class="punto-vivo" aria-hidden="true"></span>
            <span>TURNO EN CURSO · {{ comidaEnCursoObj.rango }}</span>
          </div>
          <div class="titulo-y-reloj">
            <h1>{{ comidaEnCursoObj.nombre }}</h1>
            <span class="reloj-kiosko">{{ fechaActualTexto }} · {{ horaActualTexto }} hs</span>
          </div>
        </div>

        <div class="encabezado-controles">
          <div class="selector-turno-segmentado" role="group" aria-label="Cambiar turno de comida">
            <button
              v-for="comida in COMIDAS_CONFIG"
              :key="comida.id"
              type="button"
              :class="['btn-segmento', comidaEnCursoId === comida.id ? 'activo' : '']"
              @click="seleccionarComidaManual(comida.id)"
            >
              {{ comida.nombre }}
            </button>
          </div>

          <button
            type="button"
            class="btn-panel-discreto"
            aria-label="Abrir resumen del turno y opciones de sesión"
            @click="abrirMenuDiscreto"
          >
            <span>Resumen y Turno</span>
          </button>
        </div>
      </header>

      <!-- Mensajes de feedback (éxito, 409 conflicto, errores) -->
      <div
        v-if="alerta.texto"
        :class="['alerta-kiosko', `alerta-${alerta.tipo}`]"
        role="alert"
      >
        <span>{{ alerta.texto }}</span>
        <button type="button" class="btn-cerrar-alerta" @click="alerta.texto = ''">
          Cerrar
        </button>
      </div>

      <!-- Cuerpo principal en 2 paneles claros -->
      <div class="kiosko-layout-grid">
        <!-- PANEL IZQUIERDO: Buscador y Teclado Táctil -->
        <section class="tarjeta-kiosko panel-buscador" aria-label="Buscador de comensales">
          <div class="buscador-header">
            <h2> Buscar personal</h2>
            <div class="selector-modo-busqueda" role="tablist" aria-label="Método de búsqueda">
              <button
                type="button"
                role="tab"
                :aria-selected="modoBusqueda === 'dni'"
                :class="['btn-modo-busq', modoBusqueda === 'dni' ? 'activo' : '']"
                @click="cambiarModoBusqueda('dni')"
              >
                Por DNI
              </button>
              <button
                type="button"
                role="tab"
                :aria-selected="modoBusqueda === 'nombre'"
                :class="['btn-modo-busq', modoBusqueda === 'nombre' ? 'activo' : '']"
                @click="cambiarModoBusqueda('nombre')"
              >
                Nombre
              </button>
              <button
                type="button"
                role="tab"
                :aria-selected="modoBusqueda === 'sector'"
                :class="['btn-modo-busq', modoBusqueda === 'sector' ? 'activo' : '']"
                @click="cambiarModoBusqueda('sector')"
              >
                Por Sector
              </button>
            </div>
          </div>

          <!-- MODO 1: Teclado numérico propio (sin teclado del SO, 8 dígitos exactos) -->
          <div v-if="modoBusqueda === 'dni'" class="bloque-dni">
            <div :class="['visor-dni-claro', errorDni ? 'visor-invalido' : '']">
              <div class="visor-fila-sup">
                <label for="visor-dni-input">Número de Documento (DNI)</label>
                <span v-if="dniInput" class="contador-digitos">{{ dniInput.length }}/8 dígitos</span>
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
                :disabled="buscando || !dniInput"
                @click="limpiarDni"
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
                :disabled="buscando || !dniInput"
                @click="borrarDigito"
              >
                ← Borrar
              </button>
            </div>

            <button
              type="button"
              class="btn-primario-grande"
              :disabled="buscando || !esDniValido"
              @click="buscarPorDni"
            >
              {{ buscando ? 'Buscando autorización...' : 'Buscar e incluir al retiro' }}
            </button>
          </div>

          <!-- MODO 2: Por Nombre o Apellido -->
          <div v-else-if="modoBusqueda === 'nombre'" class="bloque-busqueda-alternativa">
            <label for="input-nya" class="label-estandar">Apellido o Nombre de la persona</label>
            <div class="barra-input-boton">
              <input
                id="input-nya"
                v-model="nyaInput"
                type="text"
                placeholder="Ej: Gómez o Laura"
                class="input-claro-tactil"
                @keyup.enter="buscarPorNombre"
              />
              <button
                type="button"
                class="btn-primario-tactil"
                :disabled="buscando || nyaInput.trim().length < 2"
                @click="buscarPorNombre"
              >
                Buscar
              </button>
            </div>
            <small v-if="errorNombre" class="texto-error-campo" role="alert">
              {{ errorNombre }}
            </small>

            <div v-if="resultadosNombre.length > 0" class="lista-resultados-clara">
              <div
                v-for="pers in resultadosNombre"
                :key="pers.idPersonal"
                class="fila-persona-resultado"
              >
                <div>
                  <strong class="res-nombre">{{ pers.apellido }}, {{ pers.nombre }}</strong>
                  <span class="res-detalle">
                    DNI {{ formatearDniConPuntos(pers.dni) }} · {{ pers.sector }}
                  </span>
                </div>
                <button
                  type="button"
                  class="btn-incluir-chico"
                  :disabled="estaEnRetiro(pers.idPersonal)"
                  @click="agregarPersonaAlRetiro(pers)"
                >
                  {{ estaEnRetiro(pers.idPersonal) ? 'En bandeja' : '+ Agregar' }}
                </button>
              </div>
            </div>
            <div v-else-if="busquedaSinResultados" class="caja-estado-vacio">
              No se encontraron personas con comidas autorizadas hoy para esa búsqueda.
            </div>
          </div>

          <!-- MODO 3: Por Sector (personas con comidas pendientes hoy) -->
          <div v-else class="bloque-busqueda-alternativa">
            <label for="select-sector" class="label-estandar">
              Seleccionar Sector (comidas autorizadas pendientes hoy)
            </label>
            <div class="barra-input-boton">
              <select
                id="select-sector"
                v-model="sectorFiltroId"
                class="input-claro-tactil"
                @change="buscarPorSector"
              >
                <option value="">Elegí un sector...</option>
                <option v-for="sec in sectoresOpciones" :key="sec.id" :value="sec.id">
                  {{ sec.nombre }}
                </option>
              </select>
              <button
                v-if="resultadosSector.length > 0"
                type="button"
                class="btn-secundario-verde"
                @click="incluirTodoElSector"
              >
                + Agregar todos ({{ resultadosSector.length }})
              </button>
            </div>

            <div v-if="resultadosSector.length > 0" class="lista-resultados-clara">
              <div
                v-for="pers in resultadosSector"
                :key="pers.idPersonal"
                class="fila-persona-resultado"
              >
                <div>
                  <strong class="res-nombre">{{ pers.apellido }}, {{ pers.nombre }}</strong>
                  <span class="res-detalle">
                    DNI {{ formatearDniConPuntos(pers.dni) }} · Menú {{ pers.menuPrincipal }}
                  </span>
                </div>
                <button
                  type="button"
                  class="btn-incluir-chico"
                  :disabled="estaEnRetiro(pers.idPersonal)"
                  @click="agregarPersonaAlRetiro(pers)"
                >
                  {{ estaEnRetiro(pers.idPersonal) ? 'En bandeja' : '+ Agregar' }}
                </button>
              </div>
            </div>
            <div v-else-if="sectorFiltroId && !buscando" class="caja-estado-vacio">
              No hay personas con comidas pendientes de retiro hoy en este sector.
            </div>
          </div>
        </section>

        <!-- PANEL DERECHO: Bandeja limpia de revisión de comidas -->
        <section class="tarjeta-kiosko panel-bandeja" aria-label="Bandeja de retiro en curso">
          <div class="bandeja-encabezado">
            <div>
              <h2>Revisar comidas y confirmar entrega</h2>
              <p class="subtitulo-bandeja">
                Personas incluidas en esta operación:
                <strong>{{ personasEnRetiro.length }}</strong>
              </p>
            </div>

            <div v-if="personasEnRetiro.length > 0" class="bandeja-acciones-top">
              <span class="chip-inactividad" title="Tiempo para reinicio automático">
                Reinicia en {{ segundosInactividad }}s
              </span>
              <button type="button" class="btn-limpiar-bandeja" @click="resetearFlujoKiosko">
                Vaciar bandeja
              </button>
            </div>
          </div>

          <div v-if="personasEnRetiro.length === 0" class="bandeja-vacia">
            <p class="vacia-titulo">No hay personas cargadas en el retiro actual</p>
            <p class="vacia-descripcion">
              Usá el teclado numérico de la izquierda o buscá por nombre/sector para ver las comidas
              autorizadas del día y registrar la entrega.
            </p>
          </div>

          <div v-else class="lista-comensales-retiro">
            <article
              v-for="persona in personasEnRetiro"
              :key="persona.idPersonal"
              class="ficha-comensal-clara"
            >
              <div class="ficha-comensal-top">
                <div class="comensal-identidad">
                  <div class="avatar-iniciales" aria-hidden="true">
                    {{ obtenerIniciales(persona) }}
                  </div>
                  <div>
                    <h3 class="ficha-nya">{{ persona.apellido }}, {{ persona.nombre }}</h3>
                    <div class="ficha-chips-meta">
                      <span class="chip-dni">DNI {{ formatearDniConPuntos(persona.dni) }}</span>
                      <span class="chip-sector">{{ persona.sector }}</span>
                      <span class="chip-menu">Menú {{ persona.menuPrincipal }}</span>
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  class="btn-quitar-ficha"
                  @click="quitarPersona(persona.idPersonal)"
                >
                  Quitar
                </button>
              </div>

              <!-- Grilla de 4 comidas con Color + Ícono + Texto -->
              <div
                class="grilla-comidas-ficha"
                role="group"
                :aria-label="`Comidas del día para ${persona.nombre}`"
              >
                <button
                  v-for="comida in COMIDAS_CONFIG"
                  :key="comida.id"
                  type="button"
                  :disabled="!puedeSeleccionarComida(persona, comida.id)"
                  :class="[
                    'boton-estado-comida',
                    claseVisualComida(persona, comida.id),
                    comidaEnCursoId === comida.id ? 'es-turno-actual' : '',
                    estaComidaMarcada(persona, comida.id) ? 'seleccionada-para-entregar' : '',
                  ]"
                  @click="toggleSeleccionComida(persona, comida.id)"
                >
                  <div class="comida-cabecera-card">
                    <span class="comida-nombre-card">{{ comida.nombre }}</span>
                    <span v-if="comidaEnCursoId === comida.id" class="tag-en-curso">En curso</span>
                  </div>

                  <div class="comida-estado-linea">
                    <span class="icono-estado" aria-hidden="true">
                      {{ iconoComida(persona, comida.id) }}
                    </span>
                    <span class="texto-estado">
                      {{ textoEstadoComida(persona, comida.id) }}
                    </span>
                  </div>
                </button>
              </div>
            </article>
          </div>

          <!-- Pie limpio de confirmación de entrega -->
          <div class="bandeja-pie-confirmacion">
            <div class="resumen-previo-pie">
              <span>Seleccionadas para entregar:</span>
              <strong>{{ solicitudesSeleccionadasIds.length }} vianda(s)</strong>
            </div>

            <button
              type="button"
              :class="[
                'btn-confirmar-entrega-kiosko',
                solicitudesSeleccionadasIds.length > 0 ? 'activo' : 'deshabilitado',
              ]"
              :disabled="solicitudesSeleccionadasIds.length === 0 || enviandoEntrega"
              @click="abrirResumenConfirmacion"
            >
              <template v-if="solicitudesSeleccionadasIds.length === 0">
                Seleccioná al menos una comida autorizada pendiente
              </template>
              <template v-else>
                Revisar y Confirmar Entrega ({{ solicitudesSeleccionadasIds.length }})
              </template>
            </button>
          </div>
        </section>
      </div>
    </div>

    <!-- MODAL DE RESUMEN Y SELECCIÓN DE RESPONSABLE ANTES DE CONFIRMAR -->
    <div
      v-if="modalConfirmacionAbierto"
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

        <!-- Selector de Responsable integrado dentro del modal de confirmación -->
        <div class="caja-responsable-modal">
          <div class="responsable-cabecera-modal">
            <div>
              <span class="etiqueta-resp-modal">Responsable efectivo del retiro</span>
              <strong class="valor-resp-modal">{{ descripcionResponsableActual }}</strong>
            </div>

            <div class="selector-modo-busqueda selector-dos-opciones">
              <button
                type="button"
                :class="['btn-modo-busq', modoResponsable === 'incluida' ? 'activo' : '']"
                @click="seleccionarModoResponsable('incluida')"
              >
                {{ personasEnRetiro.length === 1 ? 'El mismo titular' : 'Persona de la lista' }}
              </button>
              <button
                type="button"
                :class="['btn-modo-busq', modoResponsable === 'tercero' ? 'activo' : '']"
                @click="seleccionarModoResponsable('tercero')"
              >
                Otra persona / Tercero
              </button>
            </div>
          </div>

          <!-- Si hay más de 1 persona y elige "Persona de la lista", elige cuál de ellas retira -->
          <div v-if="modoResponsable === 'incluida' && personasEnRetiro.length > 1" class="bloque-select-resp">
            <label for="select-responsable-modal" class="label-estandar">
              Seleccioná qué persona de la lista retira las viandas
            </label>
            <select
              id="select-responsable-modal"
              v-model="idResponsableSeleccionado"
              class="input-claro-tactil"
              @change="errorResponsable = ''"
            >
              <option value="">Seleccioná quién retira...</option>
              <option
                v-for="p in personasEnRetiro"
                :key="p.idPersonal"
                :value="p.idPersonal"
              >
                {{ p.apellido }}, {{ p.nombre }} — DNI {{ formatearDniConPuntos(p.dni) }}
              </option>
            </select>
          </div>

          <!-- Si elige "Otra persona / Tercero" (para 1 o varias personas) -->
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
                @input="limpiarYValidarDniTercero"
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
          <li v-for="item in itemsResumenConfirmacion" :key="item.idSolicitud">
            <div>
              <strong>{{ item.apellido }}, {{ item.nombre }}</strong>
              <span class="res-detalle">
                DNI {{ formatearDniConPuntos(item.dni) }} · {{ item.sector }}
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
            :disabled="enviandoEntrega"
            @click="modalConfirmacionAbierto = false"
          >
            Volver
          </button>
          <button
            type="button"
            class="btn-primario-tactil"
            :disabled="enviandoEntrega"
            @click="confirmarEntregaDefinitiva"
          >
            {{ enviandoEntrega ? 'Registrando entrega...' : 'Sí, confirmar entrega' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL DISCRETO: Resumen del Día, Entregas del Turno y Cerrar Sesión -->
    <div
      v-if="menuDiscretoAbierto"
      class="modal-kiosko-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Resumen del turno y cierre de sesión"
    >
      <div class="modal-kiosko-card modal-kiosko-ancho">
        <div class="modal-discreto-header">
          <div>
            <h2>Resumen Operativo · Sector Comedor</h2>
            <p class="modal-subtexto">
              Fecha: {{ fechaActualTexto }} · Turno activo: {{ comidaEnCursoObj.nombre }}
            </p>
          </div>
          <div class="acciones-top-discreto">
            <button type="button" class="btn-cerrar-sesion" @click="ejecutarCierreSesion">
              Cerrar sesión
            </button>
            <button
              type="button"
              class="btn-secundario-claro"
              @click="menuDiscretoAbierto = false"
            >
              Volver al Kiosco
            </button>
          </div>
        </div>

        <div class="selector-modo-busqueda tabs-modal-discreto">
          <button
            type="button"
            :class="['btn-modo-busq', tabDiscreta === 'totales' ? 'activo' : '']"
            @click="cambiarTabDiscreta('totales')"
          >
            Totales del día (Autorizadas vs. Entregadas)
          </button>
          <button
            type="button"
            :class="['btn-modo-busq', tabDiscreta === 'entregas' ? 'activo' : '']"
            @click="cambiarTabDiscreta('entregas')"
          >
            Entregas registradas en el turno ({{ comidaEnCursoObj.nombre }})
          </button>
        </div>

        <div v-if="cargandoDiscreto" class="caja-estado-vacio">
          Cargando información del día...
        </div>

        <div v-else-if="tabDiscreta === 'totales'" class="cuerpo-modal-discreto">
          <div class="tarjetas-kpi-claras">
            <div class="kpi-box-claro">
              <span class="kpi-titulo">Total Autorizadas Hoy</span>
              <strong class="kpi-numero">{{ resumenDiaData?.total_autorizado ?? 0 }}</strong>
            </div>
            <div class="kpi-box-claro">
              <span class="kpi-titulo">Total Entregadas Hoy</span>
              <strong class="kpi-numero texto-verde-inst">
                {{ resumenDiaData?.total_entregado ?? 0 }}
              </strong>
            </div>
            <div class="kpi-box-claro">
              <span class="kpi-titulo">Pendientes de Retiro</span>
              <strong class="kpi-numero texto-ambar-inst">
                {{ resumenDiaData?.diferencia ?? 0 }}
              </strong>
            </div>
          </div>

          <div v-if="(resumenDiaData?.desglose || []).length > 0" class="tabla-contenedor-claro">
            <table class="tabla-clara">
              <thead>
                <tr>
                  <th>Comida</th>
                  <th>Tipo de menú</th>
                  <th>Autorizadas</th>
                  <th>Entregadas</th>
                  <th>Pendientes</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(fila, idx) in resumenDiaData.desglose" :key="idx">
                  <td>{{ NOMBRES_COMIDAS[fila.idTipoComida] || `Comida #${fila.idTipoComida}` }}</td>
                  <td>{{ NOMBRES_MENUS[fila.idTipoMenu] || `Menú #${fila.idTipoMenu}` }}</td>
                  <td class="dato-num">{{ fila.total_autorizado }}</td>
                  <td class="dato-num">{{ fila.total_entregado }}</td>
                  <td class="dato-num">
                    {{ (fila.total_autorizado || 0) - (fila.total_entregado || 0) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="caja-estado-vacio">
            No hay comidas autorizadas registradas para el día de hoy.
          </div>
        </div>

        <div v-else class="cuerpo-modal-discreto">
          <div v-if="entregasTurnoLista.length > 0" class="tabla-contenedor-claro">
            <table class="tabla-clara">
              <thead>
                <tr>
                  <th>N.º Entrega</th>
                  <th>Hora</th>
                  <th>Comida</th>
                  <th>Tipo de menú</th>
                  <th>ID Responsable</th>
                  <th>Solicitud</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="e in entregasTurnoLista" :key="e.idEntrega">
                  <td class="dato-num">#{{ e.idEntrega }}</td>
                  <td>{{ extraerHora(e.fecha_hora) }} hs</td>
                  <td>{{ NOMBRES_COMIDAS[e.idTipoComida] || `Comida #${e.idTipoComida}` }}</td>
                  <td>{{ NOMBRES_MENUS[e.idTipoMenu] || `Menú #${e.idTipoMenu}` }}</td>
                  <td class="dato-num">Personal #{{ e.idPersonalResponsable }}</td>
                  <td class="dato-num">#{{ e.idSolicitud }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="caja-estado-vacio">
            Todavía no se registraron entregas en el turno de {{ comidaEnCursoObj.nombre }}.
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  buscarComidasAutorizadas,
  cerrarSesionApi,
  chequearConexionApi,
  listarEntregasTurno,
  listarSectoresActivos,
  obtenerConfiguracionHorarios,
  obtenerResumenEntregasDia,
  registrarEntrega,
} from '../services/entregas'

const router = useRouter()

const NOMBRES_COMIDAS = {
  1: 'Desayuno',
  2: 'Almuerzo',
  3: 'Merienda',
  4: 'Cena',
}

const NOMBRES_MENUS = {
  1: 'General',
  2: 'Vegetariano',
  3: 'Celíaco',
}

const COMIDAS_CONFIG = ref([
  { id: 1, nombre: 'Desayuno', rango: '07:00 a 09:30', inicioMin: 7 * 60, finMin: 9 * 60 + 30 },
  { id: 2, nombre: 'Almuerzo', rango: '11:30 a 14:30', inicioMin: 11 * 60 + 30, finMin: 14 * 60 + 30 },
  { id: 3, nombre: 'Merienda', rango: '16:00 a 17:30', inicioMin: 16 * 60, finMin: 17 * 60 + 30 },
  { id: 4, nombre: 'Cena', rango: '19:30 a 22:00', inicioMin: 19 * 60 + 30, finMin: 22 * 60 },
])

const SEGUNDOS_LIMITE_INACTIVIDAD = 60

function obtenerFechaHoyIso() {
  const d = new Date()
  const anio = d.getFullYear()
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const dia = String(d.getDate()).padStart(2, '0')
  return `${anio}-${mes}-${dia}`
}

function calcularComidaPorHora() {
  const ahora = new Date()
  const min = ahora.getHours() * 60 + ahora.getMinutes()
  for (const c of COMIDAS_CONFIG.value) {
    if (min >= c.inicioMin && min <= c.finMin) return c.id
  }
  if (min < 11 * 60 + 30) return 1
  if (min < 16 * 60) return 2
  if (min < 19 * 60 + 30) return 3
  return 4
}

const fechaHoyIso = ref(obtenerFechaHoyIso())
const relojActual = ref(new Date())
const comidaEnCursoId = ref(calcularComidaPorHora())
const comidaForzadaManual = ref(false)

const modoBusqueda = ref('dni')
const dniInput = ref('')
const errorDni = ref('')
const nyaInput = ref('')
const errorNombre = ref('')
const sectorFiltroId = ref('')

const buscando = ref(false)
const busquedaSinResultados = ref(false)
const resultadosNombre = ref([])
const resultadosSector = ref([])
const sectoresApi = ref([])
const sectoresCache = ref({})

const personasEnRetiro = ref([])
const solicitudesSeleccionadasIds = ref([])

const modoResponsable = ref('incluida')
const idResponsableSeleccionado = ref('')
const tercero = ref({ dni: '', nombre: '' })
const errorResponsable = ref('')

const modalConfirmacionAbierto = ref(false)
const enviandoEntrega = ref(false)
const alerta = ref({ tipo: '', texto: '' })

const segundosInactividad = ref(SEGUNDOS_LIMITE_INACTIVIDAD)
const conexionActiva = ref(true)

const menuDiscretoAbierto = ref(false)
const tabDiscreta = ref('totales')
const cargandoDiscreto = ref(false)
const resumenDiaData = ref(null)
const entregasTurnoLista = ref([])

let timerReloj = null
let timerHealth = null
let timerPostConfirmacion = null

const comidaEnCursoObj = computed(() => {
  return COMIDAS_CONFIG.value.find((c) => c.id === comidaEnCursoId.value) || COMIDAS_CONFIG.value[0]
})

const fechaActualTexto = computed(() => {
  const f = relojActual.value
  const dd = String(f.getDate()).padStart(2, '0')
  const mm = String(f.getMonth() + 1).padStart(2, '0')
  const yyyy = f.getFullYear()
  return `${dd}/${mm}/${yyyy}`
})

const horaActualTexto = computed(() => {
  return relojActual.value.toLocaleTimeString('es-AR', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
})

const dniFormateado = computed(() => {
  if (!dniInput.value) return ''
  return formatearDniConPuntos(dniInput.value)
})

// Estrictamente 8 dígitos numéricos
const esDniValido = computed(() => /^\d{8}$/.test(dniInput.value))

const sectoresOpciones = computed(() => {
  if (sectoresApi.value.length > 0) return sectoresApi.value
  return Object.entries(sectoresCache.value)
    .map(([id, nombre]) => ({ id: Number(id), nombre }))
    .sort((a, b) => a.nombre.localeCompare(b.nombre))
})

const itemsResumenConfirmacion = computed(() => {
  const setIds = new Set(solicitudesSeleccionadasIds.value)
  const items = []
  for (const p of personasEnRetiro.value) {
    for (const c of COMIDAS_CONFIG.value) {
      const sol = p.comidas[c.id]
      if (sol && setIds.has(sol.idSolicitud)) {
        items.push({
          idSolicitud: sol.idSolicitud,
          idPersonal: p.idPersonal,
          nombre: p.nombre,
          apellido: p.apellido,
          dni: p.dni,
          sector: p.sector,
          comida: c.nombre,
          menu: sol.menu || p.menuPrincipal,
        })
      }
    }
  }
  return items
})

const descripcionResponsableActual = computed(() => {
  if (modoResponsable.value === 'tercero') {
    const nom = tercero.value.nombre.trim() || 'Sin nombre'
    const doc = tercero.value.dni ? formatearDniConPuntos(tercero.value.dni) : 'Sin DNI'
    return `${nom} (DNI ${doc} · Tercero)`
  }
  if (personasEnRetiro.value.length === 1) {
    const p = personasEnRetiro.value[0]
    return `${p.apellido}, ${p.nombre} (DNI ${formatearDniConPuntos(p.dni)})`
  }
  const p = personasEnRetiro.value.find(
    (x) => Number(x.idPersonal) === Number(idResponsableSeleccionado.value)
  )
  return p ? `${p.apellido}, ${p.nombre} (DNI ${formatearDniConPuntos(p.dni)})` : 'Sin seleccionar'
})

function obtenerIniciales(persona) {
  const ap = (persona.apellido || '').trim().charAt(0)
  const no = (persona.nombre || '').trim().charAt(0)
  return `${ap}${no}`.toUpperCase() || 'P'
}

function formatearDniConPuntos(dniStr) {
  const limpio = String(dniStr || '').replace(/\D/g, '')
  if (!limpio) return ''
  return limpio.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

function extraerHora(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso).slice(11, 16)
  return d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', hour12: false })
}

function reiniciarTemporizadorInactividad() {
  segundosInactividad.value = SEGUNDOS_LIMITE_INACTIVIDAD
}

function seleccionarComidaManual(idComida) {
  comidaEnCursoId.value = idComida
  comidaForzadaManual.value = true
}

function seleccionarModoResponsable(nuevoModo) {
  modoResponsable.value = nuevoModo
  errorResponsable.value = ''
}

function limpiarYValidarDniTercero() {
  tercero.value.dni = tercero.value.dni.replace(/\D/g, '').slice(0, 8)
  if (tercero.value.dni && tercero.value.dni.length < 8) {
    errorResponsable.value = 'El DNI debe tener exactamente 8 dígitos numéricos.'
  } else {
    errorResponsable.value = ''
  }
}

function cambiarModoBusqueda(modo) {
  modoBusqueda.value = modo
  errorDni.value = ''
  errorNombre.value = ''
  busquedaSinResultados.value = false
  resultadosNombre.value = []
}

function ingresarDigito(digito) {
  if (dniInput.value.length >= 8) {
    errorDni.value = 'El DNI debe tener exactamente 8 dígitos.'
    return
  }
  dniInput.value += digito
  validarDniEnTiempoReal()
}

function borrarDigito() {
  dniInput.value = dniInput.value.slice(0, -1)
  validarDniEnTiempoReal()
}

function limpiarDni() {
  dniInput.value = ''
  errorDni.value = ''
}

function validarDniEnTiempoReal() {
  if (!dniInput.value) {
    errorDni.value = ''
    return
  }
  if (!/^\d+$/.test(dniInput.value)) {
    errorDni.value = 'Solo se permiten caracteres numéricos.'
  } else if (dniInput.value.length < 8) {
    errorDni.value = 'El DNI debe tener 8 dígitos numéricos.'
  } else {
    errorDni.value = ''
  }
}

function consolidarPersonasDesdeSolicitudes(filas) {
  const mapa = new Map()
  const nuevosSectores = { ...sectoresCache.value }

  for (const fila of filas) {
    const idPersonal = fila.idPersonal
    if (!idPersonal) continue

    if (fila.idSector && fila.sector) {
      nuevosSectores[Number(fila.idSector)] = fila.sector
    }

    if (!mapa.has(idPersonal)) {
      mapa.set(idPersonal, {
        idPersonal,
        dni: String(fila.dni || ''),
        nombre: fila.nombre || '',
        apellido: fila.apellido || '',
        idSector: fila.idSector,
        sector: fila.sector || `Sector #${fila.idSector}`,
        menuPrincipal: fila.menu || NOMBRES_MENUS[fila.idTipoMenu] || 'General',
        comidas: { 1: null, 2: null, 3: null, 4: null },
      })
    }

    const persona = mapa.get(idPersonal)
    const idComida = Number(fila.idTipoComida)
    if (idComida >= 1 && idComida <= 4) {
      persona.comidas[idComida] = {
        idSolicitud: fila.idSolicitud,
        idTipoComida: idComida,
        idTipoMenu: fila.idTipoMenu,
        menu: fila.menu || NOMBRES_MENUS[fila.idTipoMenu] || 'General',
        entregada: Boolean(fila.entregada),
        hora_entrega: fila.hora_entrega || null,
      }
    }
  }

  sectoresCache.value = nuevosSectores
  return Array.from(mapa.values())
}

function estaEnRetiro(idPersonal) {
  return personasEnRetiro.value.some((p) => Number(p.idPersonal) === Number(idPersonal))
}

function agregarPersonaAlRetiro(persona) {
  const idx = personasEnRetiro.value.findIndex(
    (p) => Number(p.idPersonal) === Number(persona.idPersonal)
  )
  if (idx >= 0) {
    personasEnRetiro.value[idx] = persona
  } else {
    personasEnRetiro.value.push(persona)
  }

  const solCurso = persona.comidas[comidaEnCursoId.value]
  if (solCurso && !solCurso.entregada) {
    if (!solicitudesSeleccionadasIds.value.includes(solCurso.idSolicitud)) {
      solicitudesSeleccionadasIds.value.push(solCurso.idSolicitud)
    }
  }

  if (personasEnRetiro.value.length === 1 && !idResponsableSeleccionado.value) {
    idResponsableSeleccionado.value = persona.idPersonal
  }
}

async function buscarPorDni() {
  if (!esDniValido.value) {
    errorDni.value = 'Ingresá un DNI válido de 8 dígitos.'
    return
  }

  buscando.value = true
  errorDni.value = ''
  alerta.value = { tipo: '', texto: '' }

  try {
    const data = await buscarComidasAutorizadas({
      fecha: fechaHoyIso.value,
      dni: dniInput.value,
    })
    const personas = consolidarPersonasDesdeSolicitudes(Array.isArray(data) ? data : [])
    const encontrada = personas.find((p) => p.dni === dniInput.value) || personas[0]

    if (!encontrada) {
      alerta.value = {
        tipo: 'advertencia',
        texto: `No se encontraron comidas autorizadas para hoy con el DNI ${formatearDniConPuntos(dniInput.value)}.`,
      }
      return
    }

    agregarPersonaAlRetiro(encontrada)
    dniInput.value = ''
  } catch (err) {
    alerta.value = {
      tipo: 'error',
      texto: err?.message || 'No se pudo consultar el DNI ingresado.',
    }
  } finally {
    buscando.value = false
  }
}

async function buscarPorNombre() {
  const q = nyaInput.value.trim()
  if (q.length < 2) {
    errorNombre.value = 'Ingresá al menos 2 letras para buscar.'
    return
  }

  buscando.value = true
  errorNombre.value = ''
  busquedaSinResultados.value = false
  alerta.value = { tipo: '', texto: '' }

  try {
    const data = await buscarComidasAutorizadas({
      fecha: fechaHoyIso.value,
      nya: q,
    })
    const personas = consolidarPersonasDesdeSolicitudes(Array.isArray(data) ? data : [])
    resultadosNombre.value = personas
    busquedaSinResultados.value = personas.length === 0
  } catch (err) {
    alerta.value = {
      tipo: 'error',
      texto: err?.message || 'Error al buscar por nombre o apellido.',
    }
  } finally {
    buscando.value = false
  }
}

async function buscarPorSector() {
  if (!sectorFiltroId.value) {
    resultadosSector.value = []
    return
  }

  buscando.value = true
  alerta.value = { tipo: '', texto: '' }

  try {
    const data = await buscarComidasAutorizadas({
      fecha: fechaHoyIso.value,
      sector: sectorFiltroId.value,
    })
    const personas = consolidarPersonasDesdeSolicitudes(Array.isArray(data) ? data : [])
    resultadosSector.value = personas.filter((p) =>
      Object.values(p.comidas).some((c) => c && !c.entregada)
    )
  } catch (err) {
    alerta.value = {
      tipo: 'error',
      texto: err?.message || 'No se pudieron obtener las autorizaciones del sector.',
    }
  } finally {
    buscando.value = false
  }
}

function incluirTodoElSector() {
  for (const p of resultadosSector.value) {
    agregarPersonaAlRetiro(p)
  }
}

function quitarPersona(idPersonal) {
  const p = personasEnRetiro.value.find((x) => Number(x.idPersonal) === Number(idPersonal))
  if (p) {
    const idsPersona = Object.values(p.comidas)
      .filter(Boolean)
      .map((c) => c.idSolicitud)
    solicitudesSeleccionadasIds.value = solicitudesSeleccionadasIds.value.filter(
      (id) => !idsPersona.includes(id)
    )
  }
  personasEnRetiro.value = personasEnRetiro.value.filter(
    (x) => Number(x.idPersonal) !== Number(idPersonal)
  )
  if (Number(idResponsableSeleccionado.value) === Number(idPersonal)) {
    idResponsableSeleccionado.value = personasEnRetiro.value[0]?.idPersonal || ''
  }
}

function puedeSeleccionarComida(persona, idComida) {
  const c = persona.comidas[idComida]
  return Boolean(c && !c.entregada)
}

function estaComidaMarcada(persona, idComida) {
  const c = persona.comidas[idComida]
  if (!c) return false
  return solicitudesSeleccionadasIds.value.includes(c.idSolicitud)
}

function toggleSeleccionComida(persona, idComida) {
  const c = persona.comidas[idComida]
  if (!c || c.entregada) return
  const pos = solicitudesSeleccionadasIds.value.indexOf(c.idSolicitud)
  if (pos >= 0) {
    solicitudesSeleccionadasIds.value.splice(pos, 1)
  } else {
    solicitudesSeleccionadasIds.value.push(c.idSolicitud)
  }
}

function claseVisualComida(persona, idComida) {
  const c = persona.comidas[idComida]
  if (!c) return 'estado-no-autorizada'
  if (c.entregada) return 'estado-entregada'
  return 'estado-pendiente'
}

function iconoComida(persona, idComida) {
  const c = persona.comidas[idComida]
  if (!c) return '✕'
  if (c.entregada) return '✓'
  return '●'
}

function textoEstadoComida(persona, idComida) {
  const c = persona.comidas[idComida]
  if (!c) return 'No autorizada'
  if (c.entregada) {
    return c.hora_entrega ? `Entregada (${c.hora_entrega})` : 'Entregada'
  }
  return 'Autorizada · Pendiente'
}

function validarResponsableRetiro() {
  errorResponsable.value = ''

  if (modoResponsable.value === 'tercero') {
    const dniTercero = tercero.value.dni.trim()
    const nomTercero = tercero.value.nombre.trim()
    if (!/^\d{8}$/.test(dniTercero)) {
      errorResponsable.value = 'El DNI de la persona que retira debe tener exactamente 8 dígitos numéricos.'
      return false
    }
    if (nomTercero.length < 3) {
      errorResponsable.value = 'Ingresá el apellido y nombre de la persona que retira.'
      return false
    }
    return true
  }

  if (personasEnRetiro.value.length > 1 && !idResponsableSeleccionado.value) {
    errorResponsable.value = 'Seleccioná qué persona de la lista retira las viandas.'
    return false
  }
  return true
}

function abrirResumenConfirmacion() {
  if (solicitudesSeleccionadasIds.value.length === 0) return
  errorResponsable.value = ''
  if (personasEnRetiro.value.length === 1 && !idResponsableSeleccionado.value) {
    idResponsableSeleccionado.value = personasEnRetiro.value[0].idPersonal
  }
  modalConfirmacionAbierto.value = true
}

async function refrescarDatosPersonasEnRetiro() {
  const recargadas = []
  for (const p of personasEnRetiro.value) {
    try {
      const data = await buscarComidasAutorizadas({
        fecha: fechaHoyIso.value,
        dni: p.dni,
      })
      const agrupadas = consolidarPersonasDesdeSolicitudes(Array.isArray(data) ? data : [])
      const act = agrupadas.find((x) => Number(x.idPersonal) === Number(p.idPersonal))
      if (act) recargadas.push(act)
    } catch {
      recargadas.push(p)
    }
  }
  personasEnRetiro.value = recargadas

  const idsAunPendientes = new Set()
  for (const p of recargadas) {
    for (const c of Object.values(p.comidas)) {
      if (c && !c.entregada) idsAunPendientes.add(c.idSolicitud)
    }
  }
  solicitudesSeleccionadasIds.value = solicitudesSeleccionadasIds.value.filter((id) =>
    idsAunPendientes.has(id)
  )
}

async function confirmarEntregaDefinitiva() {
  if (!validarResponsableRetiro()) return

  enviandoEntrega.value = true
  alerta.value = { tipo: '', texto: '' }

  const payload = {
    ids_solicitudes: [...solicitudesSeleccionadasIds.value],
  }

  if (modoResponsable.value === 'tercero') {
    payload.tercero = {
      dni: tercero.value.dni.trim(),
      nombre: tercero.value.nombre.trim(),
    }
  } else if (personasEnRetiro.value.length === 1) {
    payload.id_personal = personasEnRetiro.value[0].idPersonal
  } else {
    payload.id_personal = Number(idResponsableSeleccionado.value)
  }

  try {
    await registrarEntrega(payload)
    modalConfirmacionAbierto.value = false
    alerta.value = {
      tipo: 'exito',
      texto: `✓ Entrega registrada con éxito (${payload.ids_solicitudes.length} ${
        payload.ids_solicitudes.length === 1 ? 'vianda' : 'viandas'
      }). Reiniciando pantalla para el siguiente comensal...`,
    }

    if (timerPostConfirmacion) clearTimeout(timerPostConfirmacion)
    timerPostConfirmacion = setTimeout(() => {
      resetearFlujoKiosko()
      alerta.value = { tipo: '', texto: '' }
    }, 3000)
  } catch (err) {
    modalConfirmacionAbierto.value = false
    const status = err?.status || err?.response?.status
    if (status === 409 || err?.isConflict) {
      const msgServidor = err?.response?.data?.error || err?.message || ''
      const matchId = /solicitud\s+(\d+)/i.exec(msgServidor)
      let texto409 = msgServidor || 'Una de las comidas seleccionadas ya fue entregada.'
      if (matchId) {
        const idSol = Number(matchId[1])
        const item = itemsResumenConfirmacion.value.find((i) => Number(i.idSolicitud) === idSol)
        if (item) {
          texto409 = `Atención (409): La comida ${item.comida} de ${item.apellido}, ${item.nombre} ya había sido entregada.`
        }
      }
      alerta.value = { tipo: 'advertencia', texto: texto409 }
      await refrescarDatosPersonasEnRetiro()
      return
    }
    alerta.value = {
      tipo: 'error',
      texto: err?.response?.data?.error || err?.message || 'No se pudo registrar la entrega.',
    }
  } finally {
    enviandoEntrega.value = false
  }
}

function resetearFlujoKiosko() {
  personasEnRetiro.value = []
  solicitudesSeleccionadasIds.value = []
  dniInput.value = ''
  errorDni.value = ''
  nyaInput.value = ''
  errorNombre.value = ''
  resultadosNombre.value = []
  resultadosSector.value = []
  sectorFiltroId.value = ''
  modoResponsable.value = 'incluida'
  idResponsableSeleccionado.value = ''
  tercero.value = { dni: '', nombre: '' }
  errorResponsable.value = ''
  modalConfirmacionAbierto.value = false
  modoBusqueda.value = 'dni'
  segundosInactividad.value = SEGUNDOS_LIMITE_INACTIVIDAD
}

async function inicializarCatalogosYConfig() {
  try {
    await obtenerConfiguracionHorarios()
  } catch {
    // Mantenemos configuración por defecto
  }

  try {
    const dataSec = await listarSectoresActivos()
    if (Array.isArray(dataSec)) {
      sectoresApi.value = dataSec
    } else if (Array.isArray(dataSec?.sectores)) {
      sectoresApi.value = dataSec.sectores
    }
  } catch {
    sectoresApi.value = []
  }

  try {
    const comidasHoy = await buscarComidasAutorizadas({ fecha: fechaHoyIso.value })
    if (Array.isArray(comidasHoy)) {
      consolidarPersonasDesdeSolicitudes(comidasHoy)
    }
  } catch {
    // Ignorar si no hay comidas hoy
  }
}

function abrirMenuDiscreto() {
  menuDiscretoAbierto.value = true
  cambiarTabDiscreta('totales')
}

async function cambiarTabDiscreta(tab) {
  tabDiscreta.value = tab
  cargandoDiscreto.value = true
  try {
    if (tab === 'totales') {
      resumenDiaData.value = await obtenerResumenEntregasDia({ fecha: fechaHoyIso.value })
    } else {
      const lista = await listarEntregasTurno({
        fecha: fechaHoyIso.value,
        tipo_comida: comidaEnCursoId.value,
      })
      entregasTurnoLista.value = Array.isArray(lista) ? lista : []
    }
  } catch {
    // Mantenemos estado vacío
  } finally {
    cargandoDiscreto.value = false
  }
}

async function verificarSaludServidor() {
  conexionActiva.value = await chequearConexionApi(fechaHoyIso.value)
}

async function ejecutarCierreSesion() {
  await cerrarSesionApi()
  localStorage.removeItem('token')
  localStorage.removeItem('auth_token')
  localStorage.removeItem('user')
  sessionStorage.clear()
  router.push('/login')
}

onMounted(() => {
  inicializarCatalogosYConfig()

  timerReloj = setInterval(() => {
    relojActual.value = new Date()
    if (!comidaForzadaManual.value) {
      comidaEnCursoId.value = calcularComidaPorHora()
    }

    if (personasEnRetiro.value.length > 0 && !enviandoEntrega.value) {
      segundosInactividad.value -= 1
      if (segundosInactividad.value <= 0) {
        resetearFlujoKiosko()
        alerta.value = {
          tipo: 'advertencia',
          texto: 'La operación en curso se reinició automáticamente por inactividad (60 s).',
        }
      }
    }
  }, 1000)

  timerHealth = setInterval(() => {
    verificarSaludServidor()
  }, 15000)
})

onBeforeUnmount(() => {
  if (timerReloj) clearInterval(timerReloj)
  if (timerHealth) clearInterval(timerHealth)
  if (timerPostConfirmacion) clearTimeout(timerPostConfirmacion)
})
</script>

<style scoped>
/* Modo Kiosco a pantalla completa en paleta clara institucional */
.kiosko-claro-viewport {
  position: fixed;
  inset: 0;
  z-index: 40;
  overflow-y: auto;
  background: #f8fafc;
  color: #0f172a;
  padding: 1.15rem 1.5rem;
  box-sizing: border-box;
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  user-select: none;
}

.kiosko-contenedor {
  max-width: 1380px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: calc(100vh - 2.3rem);
}

/* Encabezado Kiosco Claro */
.kiosko-encabezado {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 0.95rem 1.3rem;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}

.encabezado-info-turno {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.badge-turno-activo {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.76rem;
  font-weight: 700;
  color: #0f766e;
  letter-spacing: 0.05em;
}

.punto-vivo {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #0f766e;
}

.titulo-y-reloj {
  display: flex;
  align-items: baseline;
  gap: 0.85rem;
  flex-wrap: wrap;
}

.titulo-y-reloj h1 {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.015em;
}

.reloj-kiosko {
  font-size: 0.95rem;
  font-weight: 600;
  color: #64748b;
}

.encabezado-controles {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.selector-turno-segmentado {
  display: inline-flex;
  gap: 0.3rem;
  background: #f1f5f9;
  padding: 0.3rem;
  border-radius: 12px;
  border: 1px solid #cbd5e1;
}

.btn-segmento {
  min-height: 48px;
  min-width: 96px;
  padding: 0.45rem 1rem;
  border-radius: 9px;
  border: 1px solid transparent;
  background: transparent;
  color: #334155;
  font-size: 0.92rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-segmento.activo {
  background: #0f766e;
  color: #ffffff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.14);
}

.btn-panel-discreto {
  min-height: 48px;
  padding: 0.5rem 1rem;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #0f172a;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-panel-discreto:hover {
  background: #f1f5f9;
}

/* Alertas */
.alerta-kiosko {
  padding: 0.85rem 1.15rem;
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  font-size: 0.95rem;
  font-weight: 700;
}

.alerta-exito {
  background: #dcfce7;
  border: 1px solid #86efac;
  color: #166534;
}

.alerta-advertencia {
  background: #fef3c7;
  border: 1px solid #fcd34d;
  color: #92400e;
}

.alerta-error,
.alerta-error-red {
  background: #fee2e2;
  border: 1px solid #fca5a5;
  color: #991b1b;
}

.btn-cerrar-alerta,
.btn-reintentar {
  min-height: 48px;
  padding: 0.4rem 0.95rem;
  border-radius: 8px;
  border: 1px solid currentColor;
  background: #ffffff;
  color: inherit;
  font-weight: 700;
  cursor: pointer;
}

/* Grilla Principal de 2 Columnas */
.kiosko-layout-grid {
  display: grid;
  grid-template-columns: minmax(350px, 430px) 1fr;
  gap: 1.25rem;
  flex: 1;
}

.tarjeta-kiosko {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 1.15rem 1.25rem;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;
  gap: 0.95rem;
}

.buscador-header {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.buscador-header h2,
.bandeja-encabezado h2 {
  margin: 0;
  font-size: 1.12rem;
  font-weight: 700;
  color: #0f172a;
}

.selector-modo-busqueda {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.35rem;
  background: #f1f5f9;
  padding: 0.3rem;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
}

.selector-modo-busqueda.selector-dos-opciones {
  grid-template-columns: repeat(2, 1fr);
}

.btn-modo-busq {
  min-height: 44px;
  padding: 0.35rem 0.75rem;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #334155;
  font-size: 0.86rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-modo-busq.activo {
  background: #0f766e;
  color: #ffffff;
}

/* Visor DNI Claro + Teclado Táctil */
.bloque-dni {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.visor-dni-claro {
  background: #f8fafc;
  border: 2px solid #cbd5e1;
  border-radius: 12px;
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.visor-dni-claro:focus-within {
  border-color: #0f766e;
}

.visor-dni-claro.visor-invalido {
  border-color: #dc2626;
  background: #fff5f5;
}

.visor-fila-sup {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.78rem;
  font-weight: 700;
  color: #475569;
}

.contador-digitos {
  color: #0f766e;
}

.visor-input-grande {
  width: 100%;
  border: none;
  background: transparent;
  color: #0f172a;
  font-size: 2rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.03em;
  outline: none;
}

.visor-input-grande::placeholder {
  color: #94a3b8;
  font-weight: 600;
  font-size: 1.35rem;
}

.texto-error-campo {
  color: #b91c1c;
  font-size: 0.82rem;
  font-weight: 700;
}

.teclado-tactil-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.6rem;
}

.tecla-tactil {
  min-height: 58px;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #0f172a;
  font-size: 1.35rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
}

.tecla-tactil:active:not(:disabled) {
  background: #f0fdfa;
  border-color: #0f766e;
}

.tecla-tactil.tecla-auxiliar {
  background: #f8fafc;
  color: #475569;
  font-size: 0.95rem;
}

.btn-primario-grande {
  min-height: 56px;
  border-radius: 10px;
  border: 1px solid #0f766e;
  background: #0f766e;
  color: #ffffff;
  font-size: 1.05rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-primario-grande:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Buscadores por Nombre y Sector */
.bloque-busqueda-alternativa {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.label-estandar {
  display: block;
  font-size: 0.82rem;
  font-weight: 700;
  color: #334155;
  margin-bottom: 0.25rem;
}

.barra-input-boton {
  display: flex;
  gap: 0.5rem;
}

.input-claro-tactil {
  flex: 1;
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

.btn-primario-tactil {
  min-height: 50px;
  padding: 0.5rem 1.15rem;
  border-radius: 10px;
  border: 1px solid #0f766e;
  background: #0f766e;
  color: #ffffff;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-secundario-verde {
  min-height: 50px;
  padding: 0.5rem 1rem;
  border-radius: 10px;
  border: 1px solid #0f766e;
  background: #f0fdfa;
  color: #0f766e;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
}

.lista-resultados-clara {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 360px;
  overflow-y: auto;
}

.fila-persona-resultado {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.7rem 0.9rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}

.res-nombre {
  display: block;
  font-size: 0.98rem;
  color: #0f172a;
}

.res-detalle {
  display: block;
  font-size: 0.83rem;
  color: #64748b;
  margin-top: 0.15rem;
}

.btn-incluir-chico {
  min-height: 48px;
  min-width: 98px;
  padding: 0.4rem 0.85rem;
  border-radius: 8px;
  border: 1px solid #0f766e;
  background: #0f766e;
  color: #ffffff;
  font-weight: 700;
  cursor: pointer;
}

.btn-incluir-chico:disabled {
  background: #e2e8f0;
  border-color: #cbd5e1;
  color: #64748b;
}

/* Panel Derecho: Bandeja de Retiro */
.bandeja-encabezado {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid #f1f5f9;
}

.subtitulo-bandeja {
  margin: 0.2rem 0 0;
  font-size: 0.88rem;
  color: #475569;
}

.bandeja-acciones-top {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.chip-inactividad {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  color: #475569;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.btn-limpiar-bandeja {
  min-height: 48px;
  padding: 0.4rem 0.9rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #334155;
  font-weight: 700;
  cursor: pointer;
}

.bandeja-vacia,
.caja-estado-vacio {
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  padding: 2.5rem 1.5rem;
  text-align: center;
  color: #475569;
}

.vacia-titulo {
  margin: 0 0 0.35rem;
  font-size: 1.08rem;
  font-weight: 700;
  color: #334155;
}

.vacia-descripcion {
  margin: 0;
  font-size: 0.92rem;
  color: #64748b;
}

.lista-comensales-retiro {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.ficha-comensal-clara {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1rem 1.15rem;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.ficha-comensal-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.comensal-identidad {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.avatar-iniciales {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: #ccfbf1;
  border: 1px solid #99f6e4;
  color: #0f766e;
  font-size: 1.1rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ficha-nya {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 800;
  color: #0f172a;
}

.ficha-chips-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.3rem;
}

.chip-dni,
.chip-sector,
.chip-menu {
  font-size: 0.8rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 6px;
}

.chip-dni {
  background: #e2e8f0;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.chip-sector {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #334155;
}

.chip-menu {
  background: #f0fdfa;
  border: 1px solid #99f6e4;
  color: #0f766e;
}

.btn-quitar-ficha {
  min-height: 48px;
  padding: 0.4rem 0.85rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #475569;
  font-weight: 700;
  cursor: pointer;
}

/* Grilla de las 4 comidas en paleta clara */
.grilla-comidas-ficha {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.65rem;
}

.boton-estado-comida {
  min-height: 76px;
  padding: 0.65rem 0.8rem;
  border-radius: 10px;
  border: 2px solid #e2e8f0;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.35rem;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.comida-cabecera-card {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.3rem;
}

.comida-nombre-card {
  font-size: 0.98rem;
  font-weight: 800;
  color: #0f172a;
}

.tag-en-curso {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 0.12rem 0.4rem;
  border-radius: 999px;
  background: #0f766e;
  color: #ffffff;
}

.comida-estado-linea {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.82rem;
  font-weight: 700;
}

/* 1. Entregada (Verde claro institucional) */
.boton-estado-comida.estado-entregada {
  background: #f0fdf4;
  border-color: #86efac;
  color: #166534;
  cursor: not-allowed;
}

/* 2. Autorizada Pendiente (Ámbar claro) */
.boton-estado-comida.estado-pendiente {
  background: #fffbeb;
  border-color: #fcd34d;
  color: #92400e;
}

.boton-estado-comida.estado-pendiente.seleccionada-para-entregar {
  background: #ecfdf5;
  border-color: #0f766e;
  color: #0f766e;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.18);
}

/* 3. No Autorizada (Gris claro neutro) */
.boton-estado-comida.estado-no-autorizada {
  background: #f1f5f9;
  border-color: #e2e8f0;
  color: #64748b;
  cursor: not-allowed;
}

.boton-estado-comida.es-turno-actual {
  box-shadow: inset 0 0 0 1px #0f766e;
}

/* Pie de Bandeja */
.bandeja-pie-confirmacion {
  margin-top: auto;
  padding-top: 0.85rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.85rem;
}

.resumen-previo-pie {
  display: flex;
  flex-direction: column;
  font-size: 0.88rem;
  color: #475569;
}

.resumen-previo-pie strong {
  font-size: 1.15rem;
  color: #0f766e;
}

.btn-confirmar-entrega-kiosko {
  flex: 1;
  min-width: 260px;
  min-height: 58px;
  padding: 0.65rem 1.25rem;
  border-radius: 12px;
  font-size: 1.08rem;
  font-weight: 800;
  border: 1px solid #cbd5e1;
  cursor: pointer;
}

.btn-confirmar-entrega-kiosko.activo {
  background: #0f766e;
  border-color: #0f766e;
  color: #ffffff;
}

.btn-confirmar-entrega-kiosko.deshabilitado {
  background: #f1f5f9;
  color: #64748b;
  cursor: not-allowed;
}

/* Modales Claros */
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

.modal-kiosko-card.modal-kiosko-ancho {
  max-width: 840px;
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

/* Caja de Responsable adentro del Modal */
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
  letter-spacing: 0.03em;
}

.valor-resp-modal {
  font-size: 0.98rem;
  color: #0f172a;
}

.bloque-select-resp {
  display: flex;
  flex-direction: column;
}

.grilla-tercero-clara {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
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
.btn-cerrar-sesion {
  min-height: 50px;
  padding: 0.5rem 1.1rem;
  border-radius: 10px;
  font-size: 0.92rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-secundario-claro {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #0f172a;
}

.btn-cerrar-sesion {
  background: #fee2e2;
  border: 1px solid #fca5a5;
  color: #991b1b;
}

.modal-discreto-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.acciones-top-discreto {
  display: flex;
  gap: 0.5rem;
}

.tabs-modal-discreto {
  grid-template-columns: 1fr 1fr;
}

.tarjetas-kpi-claras {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-bottom: 0.9rem;
}

.kpi-box-claro {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.8rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.kpi-titulo {
  font-size: 0.76rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
}

.kpi-numero {
  font-size: 1.55rem;
  font-weight: 800;
  color: #0f172a;
}

.texto-verde-inst {
  color: #0f766e;
}

.texto-ambar-inst {
  color: #b45309;
}

.tabla-contenedor-claro {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow-x: auto;
}

.tabla-clara {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.tabla-clara th,
.tabla-clara td {
  padding: 0.65rem 0.85rem;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
}

.tabla-clara th {
  background: #f8fafc;
  color: #475569;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.dato-num {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
}

/* Adaptación para Tablets en vertical y pantallas < 1024px */
@media (max-width: 1024px) {
  .kiosko-layout-grid {
    grid-template-columns: 1fr;
  }

  .grilla-comidas-ficha {
    grid-template-columns: repeat(2, 1fr);
  }

  .grilla-tercero-clara,
  .tarjetas-kpi-claras {
    grid-template-columns: 1fr;
  }
}
</style>