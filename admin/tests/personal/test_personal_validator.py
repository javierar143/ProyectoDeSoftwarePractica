from types import SimpleNamespace

import pytest

from src.web.validators.personal.personal import validar_datos_personal


TIPOS_PERSONAL = [SimpleNamespace(idTipoPersonal=1, nombre="Fijo")]


def validar(dni="40123456", nombre="Lucía", apellido="Gómez"):
    return validar_datos_personal(
        {
            "dni": dni,
            "nombre": nombre,
            "apellido": apellido,
            "idTipoPersonal": "1",
            "idTipoMenu": "1",
            "idSector": "1",
        },
        TIPOS_PERSONAL,
    )


@pytest.mark.parametrize("dni", ["123456", "12345678901", "12A45678"])
def test_rechaza_dni_invalido(dni):
    errores = validar(dni=dni)

    assert any("DNI" in error for error in errores)


@pytest.mark.parametrize("dni", ["1234567", "1234567890"])
def test_acepta_dni_en_limites_validos(dni):
    assert validar(dni=dni) == []


@pytest.mark.parametrize("campo", ["nombre", "apellido"])
def test_rechaza_nombres_con_numeros(campo):
    valores = {"nombre": "Lucía", "apellido": "Gómez"}
    valores[campo] = "Nombre2"

    errores = validar(**valores)

    assert any(campo in error.lower() for error in errores)


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("nombre", "A"),
        ("apellido", "A"),
        ("nombre", "A" * 51),
        ("apellido", "A" * 51),
    ],
)
def test_rechaza_longitudes_extremas_en_nombre_y_apellido(campo, valor):
    valores = {"nombre": "Lucía", "apellido": "Gómez"}
    valores[campo] = valor

    errores = validar(**valores)

    assert any(campo in error.lower() for error in errores)


def test_acepta_nombres_con_tildes_y_apostrofe():
    errores = validar(nombre="María José", apellido="O'Connor")

    assert errores == []
