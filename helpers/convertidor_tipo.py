from app.historicos.historico_dto import TipoHistorico

def convertir_tipo(valor, tipo_destino):
    """Convierte un valor a un tipo específico"""
    conversores = {
        'int' : int,
        'string' : str,
        'bool' : bool,
        'float' : float,
        'list' : list,
        'tuple' : tuple,
        'tipo_historico' : lambda v: TipoHistorico[v] # Accedo al enum por nombre
    }

    if tipo_destino in conversores:
        return conversores[tipo_destino](valor)
    else:
        raise ValueError(f"'Tipo '{tipo_destino}' no soportado'")