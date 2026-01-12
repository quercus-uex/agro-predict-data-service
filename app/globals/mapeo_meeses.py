from datetime import datetime

def mes_a_entero(nombre_mes):
    """
    Convierte el nombre de un mes pasado por parámetro a entero
    """

    nombre_mes = nombre_mes.lower().strip()

    meses = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12
    }

    return meses.get(nombre_mes, None)
