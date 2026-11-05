document.addEventListener("DOMContentLoaded", () => {
    const formularios = document.querySelectorAll("form");

    formularios.forEach((formulario) => {
        const camposObligatorios = formulario.querySelectorAll(
            "input[required], select[required], textarea[required]"
        );

        const password = formulario.querySelector(
            'input[name="password"]'
        );

        const confirmarPassword = formulario.querySelector(
            'input[name="confirmar_password"]'
        );

        function validarCampo(campo) {
            campo.setCustomValidity("");

            const valor = campo.value.trim();

            if (valor === "") {
                campo.setCustomValidity(
                    "Este campo es obligatorio. Por favor, completalo."
                );
            }
        }

        function validarCoincidenciaPassword() {
            if (!password || !confirmarPassword) {
                return;
            }

            confirmarPassword.setCustomValidity("");

            if (confirmarPassword.value === "") {
                confirmarPassword.setCustomValidity(
                    "Debés confirmar la contraseña."
                );
            } else if (password.value !== confirmarPassword.value) {
                confirmarPassword.setCustomValidity(
                    "Las contraseñas no coinciden."
                );
            }
        }

        camposObligatorios.forEach((campo) => {
            campo.addEventListener("input", () => {
                validarCampo(campo);
            });

            campo.addEventListener("change", () => {
                validarCampo(campo);
            });

            campo.addEventListener("invalid", () => {
                validarCampo(campo);
            });

            validarCampo(campo);
        });

        if (password && confirmarPassword) {
            password.addEventListener(
                "input",
                validarCoincidenciaPassword
            );

            confirmarPassword.addEventListener(
                "input",
                validarCoincidenciaPassword
            );
        }

        formulario.addEventListener("submit", (evento) => {
            camposObligatorios.forEach(validarCampo);
            validarCoincidenciaPassword();

            if (!formulario.checkValidity()) {
                evento.preventDefault();
                formulario.reportValidity();
            }
        });
    });
});