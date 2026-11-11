document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("modalConfirmacion");
    const mensaje = document.getElementById("mensajeConfirmacion");
    const btnCancelar = document.getElementById("btnCancelarModal");
    const btnConfirmar = document.getElementById("btnConfirmarModal");
    let formularioPendiente = null;

    document.querySelectorAll("form[data-confirm-message]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            if (form.dataset.confirmed === "true") {
                return;
            }
            event.preventDefault();
            formularioPendiente = form;
            if (mensaje) {
                mensaje.textContent = form.getAttribute("data-confirm-message");
            }
            if (modal && typeof modal.showModal === "function") {
                modal.showModal();
            }
        });
    });

    if (btnCancelar && modal) {
        btnCancelar.addEventListener("click", function () {
            formularioPendiente = null;
            modal.close();
        });
    }

    if (btnConfirmar) {
        btnConfirmar.addEventListener("click", function () {
            if (formularioPendiente) {
                formularioPendiente.dataset.confirmed = "true";
                formularioPendiente.submit();
            }
        });
    }
});