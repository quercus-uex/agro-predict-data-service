#from app.historicos.historico_dto import TipoHistorico
#from actuales_futuros_dto import TipoPrediccion, TipoZona

#def convertir_tipo(valor, tipo_destino):
#    """Convierte un valor a un tipo específico"""
#    conversores = {
#        'int' : int,
#        'string' : str,
#        'bool' : bool,
#        'float' : float,
#        'list' : list,
#        'tuple' : tuple,
#        'tipo_historico' : lambda v: TipoHistorico[v], # Accedo al enum por nombre
#        'tipo_zona' : lambda v: TipoZona[v],
#        'tipo_prediccion' : lambda v: TipoPrediccion[v]
#    }

#    if tipo_destino in conversores:
#        return conversores[tipo_destino](valor)
#    else:
#        raise ValueError(f"'Tipo '{tipo_destino}' no soportado'")
#"""
from enum import Enum

def convertir_tipo(valor, tipo_destino):
    """
    Convierte un valor a un tipo destino.
    - tipo_destino puede ser un tipo builtin (int, str, bool, float)
    - o un Enum
    """
    if tipo_destino in (int, str, bool, float):
        return tipo_destino(valor)

    if issubclass(tipo_destino, Enum):
        return tipo_destino[valor.upper()]

    raise ValueError(f"Tipo destino no soportado: {tipo_destino}")
