from flask import current_app
from datetime import date
import logging

logger = logging.getLogger(__name__)

class DTAgroService:
    _cliente = None

    @classmethod
    def _get_cliente(cls):
        """Lazy initialization: crea el cliente solo cuando se necesita"""
        if cls._cliente is None:
            from ..clients.sensor_client import DTAgroClient
            cls._cliente = DTAgroClient(app=current_app)
        return cls._cliente
    
    @classmethod
    def get_dtagro_datos(
        cls,
        euis : list[str],
        fecha_inicio : date,
        fecha_fin : date
    ):
        cliente = cls._get_cliente()
        lista_resultados = []  # Contiene una lista de diccionarios, identificador por el eui del sensor analizado

        for eui in euis:
            # Almaceno la estructura incial del json de datos por eui
            json_eui = {'eui' : eui, 'resultados' : []}

            datos_por_eui = cliente.get_dtagro_data(
                eui = eui,
                fecha_inicio = fecha_inicio,
                fecha_fin = fecha_fin
            )
            lista_datos = []
            for dato in datos_por_eui:
                lista_datos.append(
                    {
                        "humedad_foliar" : dato['measurements'].get('Leaf_Moisture', 0.0),
                        "temp_DS18B20": dato['measurements'].get('TempC_DS18B20', 0),
                        "temperatura_hoja" : dato['measurements'].get('Leaf_Temperature', 0.0),
                        "timestamp" : dato['time'],
                        "temperatura_suelo" : dato['measurements'].get('temp_SOIL', 0.0),
                        "humedad_suelo" : dato['measurements'].get('water_SOIL', 0.0),
                        "temperatura_minima" : dato['measurements'].get('Temp_Channel1', 0.0),
                        "temperatura_maxima" : dato['measurements'].get('Temp_Channel2', 0.0)
                    }
                )

            # Actualizo el valor de los resultados por la lista de datos obtenido del sensor analizado
            json_eui['resultados'] = lista_datos
            lista_resultados.append(json_eui)
        
        return lista_resultados
