from funciones import validador_numero as validador
from funciones.suma import suma 
from funciones.resta import resta
from funciones.division import division
from funciones.multiplicacion import multiplicacion


while True:
    print("Por favor, ingrese la operacion: ")
    print("- Suma: +")
    print("- Resta: -")
    print("- Multiplicacion: *")
    print("- Division: /")

    operador = input("Ingrese la operacion: ")

    while operador not in ["+", "-", "*", "/"]:
        print("Operador inválido: " + operador)
        print("Por favor, ingrese la operacion: ")
        print("- Suma: +")
        print("- Resta: -")
        print("- Multiplicacion: *")
        print("- Division: /")
        operador = input("Ingrese la operacion: ")


    operando_1 = input("Ingrese el primer operando: ")

    while validador.operando_es_invalido(operando_1):
        print("El operando 1 es inválido: " + operando_1)
        operando_1 = input("Ingrese el primer operando: ")


    operando_2 = input("Ingrese el segundo operando: ")

    while validador.operando_es_invalido(operando_2):
        print("El operando 2 es inválido: " + operando_2)
        operando_2 = input("Ingrese el segundo operando: ")


    operando_1 = int(operando_1)
    operando_2 = int(operando_2)

    if operador == "+":
        resultado = suma(operando_1, operando_2)
    elif operador == "-":
        resultado = resta(operando_1, operando_2)
    elif operador == "*":
        resultado = multiplicacion(operando_1, operando_2)
    elif operador == "/":
        resultado = division(operando_1, operando_2)
    else:
        print("Operador desconocido")

    print("El resultado de la operacion es: " + str(resultado))