from enum import Enum
from datetime import datetime, date

def convertir_tipo(valor, tipo_destino):
    """
    Convierte un valor a un tipo destino.
    - tipo_destino puede ser un tipo builtin (int, str, bool, float)
    - o un Enum
    """
    if tipo_destino in (int, str, bool, float):
        return tipo_destino(valor)
    
    if tipo_destino in (datetime, date):
        datetime_obj = datetime.strptime(valor, "%Y-%m-%d").date()
        return datetime_obj
    
    if issubclass(tipo_destino, Enum):
        return tipo_destino[valor.upper()]

    raise ValueError(f"Tipo destino no soportado: {tipo_destino}")
