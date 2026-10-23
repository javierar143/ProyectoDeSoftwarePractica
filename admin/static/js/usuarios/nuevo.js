
/**
 * Inicializa los controles del formulario de alta de usuarios.
 * Gestiona la visibilidad de los paneles y conserva deshabilitados
 * los controles que todavía no están implementados.
 */
document.addEventListener("DOMContentLoaded", function () {
    const botonExistente = document.getElementById("btn-existente");
    const botonNuevo = document.getElementById("btn-nuevo");
    const panelExistente = document.getElementById("panel-existente");
    const panelNuevo = document.getElementById("panel-nuevo");

    /**
     * Muestra el panel activo y oculta el otro.
     *
     * No modifica el estado disabled de los controles: cada formulario
     * define qué campos están disponibles según su implementación.
     *
     * @param {HTMLElement} panelActivo - Panel que se mostrará.
     * @param {HTMLElement} panelInactivo - Panel que se ocultará.
     */
    function mostrarPanel(panelActivo, panelInactivo) {
        panelActivo.hidden = false;
        panelInactivo.hidden = true;
    }

    botonExistente.addEventListener("click", function () {
        mostrarPanel(panelExistente, panelNuevo);
    });

    botonNuevo.addEventListener("click", function () {
        mostrarPanel(panelNuevo, panelExistente);
    });

    if (panelExistente.dataset.mostrarInicial === "true") {
        mostrarPanel(panelExistente, panelNuevo);
    } else if (panelNuevo.dataset.mostrarInicial === "true") {
        mostrarPanel(panelNuevo, panelExistente);
    } else {
        panelExistente.hidden = true;
        panelNuevo.hidden = true;
    }
});
