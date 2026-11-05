document.addEventListener("DOMContentLoaded", function () {
    const btnToggle = document.getElementById("btn-toggle-filtros");
    const panelFiltros = document.getElementById("panel-filtros-usuarios");

    if (btnToggle && panelFiltros) {
        btnToggle.addEventListener("click", function () {
            panelFiltros.classList.toggle("oculto");

            const expandido = !panelFiltros.classList.contains("oculto");
            btnToggle.setAttribute("aria-expanded", String(expandido));
        });
    }

    const dialogo = document.getElementById("dialogo-confirmacion");
    const mensaje = document.getElementById("dialogo-confirmacion-mensaje");
    const botonCancelar = document.getElementById(
        "dialogo-confirmacion-cancelar"
    );
    const botonAceptar = document.getElementById(
        "dialogo-confirmacion-aceptar"
    );

    if (!dialogo || !mensaje || !botonCancelar || !botonAceptar) {
        return;
    }

    let formularioPendiente = null;

    document.addEventListener("submit", function (evento) {
        const formulario = evento.target;

        if (!formulario.matches("form[data-confirm-message]")) {
            return;
        }

        evento.preventDefault();

        formularioPendiente = formulario;
        mensaje.textContent = formulario.dataset.confirmMessage;

        dialogo.showModal();
    });

    botonCancelar.addEventListener("click", function () {
        formularioPendiente = null;
        dialogo.close();
    });

    botonAceptar.addEventListener("click", function () {
        if (!formularioPendiente) {
            dialogo.close();
            return;
        }

        const formularioConfirmado = formularioPendiente;
        formularioPendiente = null;

        dialogo.close();

        HTMLFormElement.prototype.submit.call(formularioConfirmado);
    });

    dialogo.addEventListener("close", function () {
        formularioPendiente = null;
    });
});