import re
from datetime import datetime, date
from app.globals.mapeo_meeses import mes_a_entero
class AemetParser:

    def parse(
        texto : str,
        respuesta_queue : bool
    ) -> dict:
        """
        Parsea el texto natural recibido por AEMET y devuelve un diccionario con
        los elementos más relevantes
        """

        result = {}

        # Caso en el que haya ocurrido problemas con el broker
        if not respuesta_queue:

            if "despejado" in texto.lower():
                result["estado_cielo"] = "despejado"
            elif "nuboso" in texto.lower():
                result["estado_cielo"] = "nuboso"
            else:
                result["estado_cielo"] = ""
            
            # Tendencia general de temperatura
            match_temp_general = re.search(
                r"Temperaturas\s+(sin\n?cambios|en ligero ascenso|en ligero descenso)",
                texto, re.IGNORECASE)
            result["tendencia_temp_general"] = match_temp_general.group(1) if match_temp_general else None

            print(f"Temperatura general: {result["tendencia_temp_general"]}")
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
            heladas_existe = re.search(r"heladas", texto, re.IGNORECASE)
            helada_puede_existir = re.search(r"([Nn]o [^.]+\n+(\w+)+[^.]+\.)", texto, re.IGNORECASE)
            if heladas_existe or helada_puede_existir:
                result["existencia_helada"] = True

            # Zona de heladas
            if heladas_existe or helada_puede_existir:
                zona_heladas_condicional = re.search(r"([Nn]o [^.]+\n+(\w+)+[^.]+\.)", texto, re.IGNORECASE)
                if not zona_heladas_condicional:
                    zona_heladas_confirmadas = re.search(r"[Hh]eladas[^.]+\.", texto, re.IGNORECASE)
                zona_heladas = zona_heladas_condicional or zona_heladas_confirmadas

                result["zona_helada"] = zona_heladas.group(0) if zona_heladas else None

        # Fecha de prediccion:
        fecha_prediccion = re.search(r"DÍA\s+(\d{1,2})\s+DE\s+([A-ZÁÉÍÓÚ]+)\s+DE\s+(\d{4})", texto, re.IGNORECASE)
        
        if fecha_prediccion:
            dia = int(fecha_prediccion.group(1))
            mes_texto = fecha_prediccion.group(2).lower()
            anio = int(fecha_prediccion.group(3))
            mes = mes_a_entero(mes_texto)
            print(f"mes: {mes}")
            fecha = date(anio, mes, dia)

            result["fecha_prediccion"] = fecha
        
        # Temperaturas maximas y minimas 
        if "temperaturas mínimas y máximas previstas" in texto.lower():
            # Inicializo el contenido de esta key como que va a ser un diccionario
            result["temperaturas_localidades"] = {}

            # Regex para coger el contenido de localidades junto a sus temperaturas que me interesan
            localidades_temperatura = r"^([A-ZÁÉÍÓÚÜÑa-záéíóúüñ]+(?:\s[A-ZÁÉÍÓÚÜÑa-záéíóúüñ]+)*)\s+(-?\d+)\s+(-?\d+)"

            if localidades_temperatura:
                result["temperaturas_localidades"] = {
                    match.group(1) : {
                        'temp_min' : int(match.group(2)),
                        'temp_max' : int(match.group(3))
                    }
                    for match in re.finditer(localidades_temperatura, texto, re.MULTILINE)
                }
            
        return result