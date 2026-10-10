/**
 * Inicializa los controles del formulario de alta de usuarios.
 * Gestiona la visibilidad y habilitación de los paneles
 * de alta de usuario existente y de personal nuevo.
 */
document.addEventListener("DOMContentLoaded", function () {
    const botonExistente = document.getElementById("btn-existente");
    const botonNuevo = document.getElementById("btn-nuevo");
    const panelExistente = document.getElementById("panel-existente");
    const panelNuevo = document.getElementById("panel-nuevo");

    /**
     * Muestra el panel activo y deshabilita los campos
     * del panel inactivo para evitar el envío de sus datos.
     *
     * @param {HTMLElement} panelActivo - Panel que se mostrará.
     * @param {HTMLElement} panelInactivo - Panel que se ocultará.
     */
    function mostrarPanel(panelActivo, panelInactivo) {
        panelActivo.hidden = false;
        panelInactivo.hidden = true;

        panelActivo
            .querySelectorAll("input, select, textarea, button")
            .forEach(function (campo) {
                campo.disabled = false;
            });

        panelInactivo
            .querySelectorAll("input, select, textarea, button")
            .forEach(function (campo) {
                campo.disabled = true;
            });
    }

    botonExistente.addEventListener("click", function () {
        mostrarPanel(panelExistente, panelNuevo);
    });

    botonNuevo.addEventListener("click", function () {
        mostrarPanel(panelNuevo, panelExistente);
    });

    if (panelExistente.dataset.mostrarInicial === "true") {
        mostrarPanel(panelExistente, panelNuevo);
    } else {
        panelExistente.hidden = true;
        panelNuevo.hidden = true;
    }
});