document.addEventListener("DOMContentLoaded", function () {
    const btnToggle = document.getElementById("btn-toggle-filtros");
    const panelFiltros = document.getElementById("panel-filtros-usuarios");

    if (btnToggle && panelFiltros) {
        btnToggle.addEventListener("click", function () {
            panelFiltros.classList.toggle("oculto");
        });
    }
});