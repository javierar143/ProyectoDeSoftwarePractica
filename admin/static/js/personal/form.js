document.addEventListener("DOMContentLoaded", function () {
    const selectTipo = document.getElementById("idTipoPersonal");
    const contenedorSector = document.getElementById("contenedorSector");
    const selectSector = document.getElementById("idSector");

    function actualizarVisibilidadSector() {
        const opcionSeleccionada = selectTipo.options[selectTipo.selectedIndex];
        const nombreTipo = opcionSeleccionada ? (opcionSeleccionada.getAttribute("data-nombre") || opcionSeleccionada.text.toLowerCase()) : "";

        if (nombreTipo.includes("residente")) {
            contenedorSector.style.display = "none";
            selectSector.value = "";
            selectSector.removeAttribute("required");
            selectSector.disabled = true;
        } else if (nombreTipo.includes("fijo")) {
            contenedorSector.style.display = "block";
            selectSector.disabled = false;
            selectSector.setAttribute("required", "required");
        } else {
            contenedorSector.style.display = "block";
            selectSector.disabled = false;
            selectSector.removeAttribute("required");
        }
    }

    if (selectTipo) {
        selectTipo.addEventListener("change", actualizarVisibilidadSector);
        actualizarVisibilidadSector();
    }
});
