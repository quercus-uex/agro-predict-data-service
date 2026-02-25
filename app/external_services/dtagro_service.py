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
        eui : str,
        fecha_inicio : date,
        fecha_fin : date
    ):
        cliente = cls._get_cliente()
        datos = cliente.get_dtagro_data(
            eui = eui,
            fecha_inicio = fecha_inicio,
            fecha_fin = fecha_fin
        )

        lista_datos = []

        for dato in datos:
            lista_datos.append(
                {
                    "humedad_foliar" : dato['measurements'].get('Leaf_Moisture', 0.0),
                    "temp_DS18B20": dato['measurements'].get('TempC_DS18B20', 0),
                    "temperatura_hoja" : dato['measurements'].get('Leaf_Temperature', 0.0),
                    "timestamp" : dato['time']
                }
            )
        
        return lista_datos
