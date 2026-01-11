import re
from datetime import datetime

class AemetParser:

    def parse(
        texto : str
    ) -> dict:
        """
        Parsea el texto natural recibido por AEMET y devuelve un diccionario con
        los elementos más relevantes
        """

        result = {}

        if "despejado" in texto.lower():
            result["estado_cielo"] = "despejado"
        elif "nuboso" in texto.lower():
            result["estado_cielo"] = "nuboso"
        else:
            result["estado_cielo"] = None
        
        # Tendencia temperatura maxima
        match_max = re.search(r"máximas? en (\w+)", texto, re.IGNORECASE)
        result["tendencia_temp_max"] = match_max.group(1) if match_max else None

        # Tendencia temperatura minima
        match_min = re.search(r"mínimas? en (\w+) ", texto, re.IGNORECASE)
        result["tendencia_temp_min"] = match_min.group(1) if match_min else None

        # Viento
        viento = re.search(r"([Vv]ientos?[^.]+\n)", texto, re.IGNORECASE)
        result["viento"] = viento.group(1) if viento else None

        # Precipitacion
        precipitacion = re.search(r"(Precipitaciones?[^.]+\n+[^.]+\.)", texto, re.IGNORECASE)
        result["precipitaciones"] = precipitacion.group(1) if precipitacion else None

        # Cota de nieve
        nieve = re.search(r"([Cc]ota de nieve?[^.]+\n+?[^.]+\.)", texto, re.IGNORECASE)
        result["cota_nieve"] = nieve.group(1) if nieve else None

        # Existencia de heladas
        heladas_existe = re.search(r"([Nn]o [^.]+\n+(\w+))", texto, re.IGNORECASE)
        result["existencia_helada"] = heladas_existe.group(1) if heladas_existe else None

        # Zona de heladas
        if heladas_existe:
            zona_heladas = re.search(r"([Nn]o [^.]+\n+(\w+)+[^.]+\.)", texto, re.IGNORECASE)
            result["zona_helada"] = zona_heladas.group(1) if zona_heladas else None

        return result