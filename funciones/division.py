def division(operando1, operando2):
    if operando2 == 0:
        raise ValueError("No se puede dividir por cero")
    return operando1 / operando2