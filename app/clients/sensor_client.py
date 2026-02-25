from .base_client import BaseClient
from circuitbreaker import circuit
from config.config import CircuitBreakerPersonalizado
from flask import Flask
from datetime import date
import requests
import logging

logger = logging.getLogger(__name__)

class DTAgroClient(BaseClient):
    def __init__(self, app : Flask):
        super().__init__(app, "dtagro_service")
        self.base_url = app.config.get('DTAGRO_SERVICE_BASE_URL')
        self.token = app.config.get('DTAGRO_API_TOKEN')

    @circuit(cls = CircuitBreakerPersonalizado)
    def get_dtagro_data(
        self,
        eui : str,
        fecha_inicio : date,
        fecha_fin : date
    ):
        """
        Obtiene los datos de un sensor recibidos por la API del servicio
        DTAgro
        """
        try:
            if not all([eui, fecha_inicio, fecha_fin]):
                raise ValueError("Error, se debe especificar el eui del sensor al que se quiere consultar datos junto con las fechas inicio y fin de recogida")
            
            url = f"{self.base_url}?eui={eui}&fecha_inicio={fecha_inicio}&fecha_fin={fecha_fin}"

            # Construyo la cabecera porque este endpoint a consultar está protegido
            headers = {
                "Authorization": f"Bearer {self.token}"
            }

            # Creamos la petición y almacenamos la respuesta obtenida
            response = self._make_request(
                method = 'GET',
                url = url,
                headers = headers
            )

            # Control de errores
            if response.status_code == 404:
                logger.error(f"No se han encontrado datos asociados a los parámetros indicados {eui} - {fecha_inicio} - {fecha_fin}")
                return None
            if response.status_code >= 500:
                logger.error("Se ha producido un error con el servicio al que te comunicas")
                return None
            
            response.raise_for_status()

            return response.json()
        
        except requests.RequestException as e:
            logger.error(f"Se ha producido un error con el cliente de dtagro : {e}")
            return None
            