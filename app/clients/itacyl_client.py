# Cliente que consulta y obtiene datos del servicio ITACYL
from .base_client import BaseClient
from typing import Optional
from circuitbreaker import circuit
from config.config import CircuitBreakerPersonalizado
from flask import Flask
from enum import Enum
import requests
import logging
from ..globals.grupo_plagas import GrupoPlaga

logger = logging.getLogger(__name__)

class ItacylClient(BaseClient):
    def __init__(self, app : Flask):
        super().__init__(app, "itacyl_service")
        self.base_url  = app.config.get('ITACYL_SERVICE_BASE_URL')

    @circuit(cls=CircuitBreakerPersonalizado)
    def get_itacyl_data(
        self,
        cultivo : Optional[int],
        grupo : Optional[str]
    ) :
        try:

            if grupo:
                grupo : Enum = GrupoPlaga[grupo.upper()]

            if cultivo and not grupo:
                url = f"{self.base_url}?crop={cultivo}"
            elif grupo and not cultivo:
                url = f"{self.base_url}?group={grupo.name}"
            else:
                url = f"{self.base_url}?crop={cultivo}&group={grupo.name}"

            response = self._make_request(
                method = 'GET',
                url = url
            )

            if response.status_code == 404:
                logger.error("No se han encontrado datos para los parámetros indicados")
                return None
            if response.status_code == 500:
                logger.error("Ha ocurrido un error con el servicio al que te comunicas")
                return None
            
            response.raise_for_status()

            if response.json().get('success') is True:
                return response.json().get('data')
            else:
                return None
        
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Servicio Aemet no disponible: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener datos de Aemet: {e}")
            return None