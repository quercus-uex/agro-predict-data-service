from .base_client import BaseClient
from typing import Optional
from datetime import date
from flask import current_app
from circuitbreaker import circuit
from config.config import CircuitBreakerPersonalizado
from flask import Flask
import requests
import logging

logger = logging.getLogger(__name__)

class SiARClient(BaseClient):
    def __init__(self, app : Flask):
        super().__init__(app = app, service_name = "siar_service")
        self.base_data_url = app.config['SIAR_SERVICE_DATA_URL']
        self.base_info_url = app.config['SIAR_SERVICE_INFO_URL']

    @circuit(cls=CircuitBreakerPersonalizado)
    def get_historical_data_by_date(
        self, 
        estacion_id : Optional[str],
        provincia_id : Optional[str],
        tipo,
        fec_init : date,
        fec_fin: date
    ) : 
        try:
            if estacion_id and not provincia_id:
                url = f"{self.base_data_url}/{tipo.value}/estaciones?Id={estacion_id}&FechaInicial={fec_init}&FechaFinal={fec_fin}"
            elif not estacion_id and provincia_id:
                url = f"{self.base_data_url}/{tipo.value}/provincias?Id={provincia_id}&FechaInicial={fec_init}&FechaFinal={fec_fin}"

            response = self._make_request(
                method = 'GET',
                url = url
            )
            
            if response.status_code == 404:
                logger.error(f"No se han encontrado datos para la los parámetros indicados")
                return None
            if response.status_code >= 500:
                logger.error("Ha ocurrido un problema con el servicio al que te comunicas")
                return None

            response.raise_for_status()
            
            return response.json().get('data')
        
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Servicio SiAR no disponible: {e}")
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Error al obtener datos SiAR: {e}")
            return None

    @circuit(cls=CircuitBreakerPersonalizado)
    def get_informacion(
        self,
        estaciones : bool = True
    ):
        try:
            if estaciones:
                url = f"{self.base_info_url}/estacionesInfo"
            else:
                url = f"{self.base_info_url}/provinciasInfo"

            response = self._make_request(
                method = 'GET',
                url = url
            )

            if response.status_code >= 500:
                logger.error("Ha ocurrido un problema con el servicio al que te comunicas")
                return None
            logger.info(f"Respuesta INFO: {response.json}")
            return response.json().get('data')
            
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Servicio SiAR no disponible: {e}")
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Erro al obtener datos SiAR: {e}")
            return None     