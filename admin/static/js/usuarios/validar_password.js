document.addEventListener("DOMContentLoaded", () => {
    const formularios = document.querySelectorAll("form");

    formularios.forEach((formulario) => {
        const camposObligatorios = formulario.querySelectorAll(
            "input[required], select[required], textarea[required]"
        );

        const password = formulario.querySelector('input[name="password"]');
        const confirmarPassword = formulario.querySelector('input[name="confirmar_password"]');

        // Desactiva la validación automática para controlarla manualmente con JS
        formulario.noValidate = true;

        function validarCampo(campo) {
            campo.setCustomValidity(""); // Limpia el error previo

            if (campo.value.trim() === "") {
                campo.setCustomValidity("Este campo es obligatorio. Por favor, completalo (no uses solo espacios).");
            } else if (campo.validity.tooShort) {
                const min = campo.getAttribute("minlength");
                campo.setCustomValidity(`Este campo debe tener al menos ${min} caracteres.`);
            } else if (campo.validity.patternMismatch) {
                const title = campo.getAttribute("title");
                campo.setCustomValidity(title ? title : "El formato ingresado no es válido.");
            }
        }

        function validarCoincidenciaPassword() {
            if (!password || !confirmarPassword) return;

            password.setCustomValidity("");
            confirmarPassword.setCustomValidity("");

            // En edición, si ambos están vacíos, es válido.
            if (password.value === "" && confirmarPassword.value === "") return;

            if (password.value.length > 0 && password.value.length < 8) {
                password.setCustomValidity("La contraseña debe tener al menos 8 caracteres.");
            }

            if (confirmarPassword.value.trim() === "") {
                confirmarPassword.setCustomValidity("Debés confirmar la contraseña.");
            } else if (password.value !== confirmarPassword.value) {
                confirmarPassword.setCustomValidity("Las contraseñas no coinciden.");
            }
        }

        camposObligatorios.forEach((campo) => {
            campo.addEventListener("input", () => {
                validarCampo(campo);
                if (campo === password || campo === confirmarPassword) validarCoincidenciaPassword();
            });
        });

        formulario.addEventListener("submit", (evento) => {
            camposObligatorios.forEach(validarCampo);
            validarCoincidenciaPassword();

            if (!formulario.checkValidity()) {
                evento.preventDefault(); // Detiene el envío, NO recarga la página, conserva los datos.
                formulario.reportValidity(); // Muestra el globo de error nativo del navegador.
            }
        });
    });
});