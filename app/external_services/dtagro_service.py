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
        fecha_inicio : list[date] | date,
        fecha_fin : date,
        nombre_dtagro : str,
        nombre_predictor : str
    ):
        cliente = cls._get_cliente()
        lista_resultados = []  # Contiene una lista de diccionarios, identificador por el eui del sensor analizado

        iter = 0
        for eui in euis:
            # Almaceno la estructura incial del json de datos por eui
            json_eui = {'eui' : eui, 'resultados' : []}

            datos_por_eui = cliente.get_dtagro_data(
                eui = eui,
                fecha_inicio = fecha_inicio if isinstance(fecha_inicio, date) else fecha_inicio[iter],
                fecha_fin = fecha_fin
            )
            lista_datos = []
            for dato in datos_por_eui:
                lista_datos.append(
                    {
                        "timestamp" : dato['time'],
                        f"{nombre_predictor}" : dato['measurements'].get(nombre_dtagro)
                    }
                )

            # Actualizo el valor de los resultados por la lista de datos obtenido del sensor analizado
            json_eui['resultados'] = lista_datos
            lista_resultados.append(json_eui)
            iter += 1
        
        return lista_resultados
