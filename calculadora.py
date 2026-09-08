from funciones import validador_numero as validador
<<<<<<< HEAD
from funciones import suma as suma
=======
from funciones import resta
>>>>>>> 809be7698b6b17cba74d8a224f15d51fcb5b3baa

print("Por favor, ingrese la operacion: ")
print("- Suma: +")
print("- Resta: -")
print("- Multiplicacion: *")
print("- Division: /")

operador = input("Ingrese la operacion: ")
operando_1 = input("Ingrese el primer operando: ")
operando_2 = input("Ingrese el segundo operando: ")

if validador.operando_es_invalido(operando_1):
    print("El operando 1 es inválido: " + operando_1)
    exit(1)

if validador.operando_es_invalido(operando_2):
    print("El operando 2 es inválido: " + operando_2)
    exit(1)

operando_1 = int(operando_1)
operando_2 = int(operando_2)

#if operador == "+":
    #resultado = suma(operando_1, operando_2)
#elif operador == "-":
    #resultado = resta(operando_1, operando_2)
#elif operador == "*":
    #resultado = multiplicacion(operando_1, operando_2)
#elif operador == "/":
    #resultado = division(operando_1, operando_2)
#else:
    #print("Operador desconocido")

#print("El resultado de la operacion es: " + str(resultado))