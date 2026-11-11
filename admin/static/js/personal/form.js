document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("formPersonal");
    const inputDni = document.getElementById("dni");
    const inputNombre = document.getElementById("nombre");
    const inputApellido = document.getElementById("apellido");
    const selectTipo = document.getElementById("idTipoPersonal");
    const selectMenu = document.getElementById("idTipoMenu");
    const contenedorSector = document.getElementById("contenedorSector");
    const selectSector = document.getElementById("idSector");
    const seccionErrores = document.getElementById("erroresCliente");
    const listaErrores = document.getElementById("listaErroresCliente");

    function obtenerNombreTipo() {
        if (!selectTipo || selectTipo.selectedIndex < 0) {
            return "";
        }
        const opcionSeleccionada = selectTipo.options[selectTipo.selectedIndex];
        return opcionSeleccionada
            ? (opcionSeleccionada.getAttribute("data-nombre") || opcionSeleccionada.text.toLowerCase())
            : "";
    }

    function actualizarVisibilidadSector() {
        const nombreTipo = obtenerNombreTipo();

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

    if (form) {
        form.addEventListener("submit", function (event) {
            const errores = [];

            const dni = inputDni ? inputDni.value.trim() : "";
            const nombre = inputNombre ? inputNombre.value.trim() : "";
            const apellido = inputApellido ? inputApellido.value.trim() : "";
            const nombreTipo = obtenerNombreTipo();

            if (inputDni) inputDni.value = dni;
            if (inputNombre) inputNombre.value = nombre;
            if (inputApellido) inputApellido.value = apellido;

            if (!dni || !/^\d+$/.test(dni)) {
                errores.push("El DNI es obligatorio y debe contener solo números.");
            }

            if (!nombre) {
                errores.push("El nombre es obligatorio.");
            }

            if (!apellido) {
                errores.push("El apellido es obligatorio.");
            }

            if (!selectTipo || !selectTipo.value) {
                errores.push("Debe seleccionar un tipo de personal.");
            }

            if (!selectMenu || !selectMenu.value) {
                errores.push("Debe seleccionar un tipo de menú.");
            }

            if (nombreTipo.includes("fijo") && (!selectSector || !selectSector.value)) {
                errores.push("Debe seleccionar un sector para el personal fijo.");
            }

            if (errores.length > 0) {
                event.preventDefault();
                if (listaErrores && seccionErrores) {
                    listaErrores.innerHTML = "";
                    errores.forEach(function (err) {
                        const li = document.createElement("li");
                        li.textContent = err;
                        listaErrores.appendChild(li);
                    });
                    seccionErrores.style.display = "block";
                }
            }
        });
    }
});