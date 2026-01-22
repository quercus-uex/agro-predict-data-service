from .base_client import BaseClient
from typing import Optional
from enum import Enum
from datetime import date
from flask import current_app
from circuitbreaker import circuit
from config.config import CircuitBreakerPersonalizado
from flask import Flask
import requests
import logging
from app.forecast.forecast_dto import TipoZona, TipoPrediccion

logger = logging.getLogger(__name__)

class AemetClient(BaseClient):
    def __init__(self, app : Flask):
        super().__init__(app, "aemet_service")
        self.base_url_actuales = app.config.get('AEMET_SERVICE_CURRENT_URL')
        self.base_url_futuros = app.config.get('AEMET_SERVICE_FUTURE_URL')

    @circuit(cls=CircuitBreakerPersonalizado)
    def get_current_data_by_zone(
        self,
        tipo : TipoZona,
        ccaa_code : Optional[str],
        provincia_code : Optional[str]
    ):
        try:
            if tipo is TipoZona.CCAA and ccaa_code is not None:
                url = f"{self.base_url_actuales}/{tipo.value}/{ccaa_code}"
            elif tipo is TipoZona.PROVINCIAL and provincia_code is not None:
                url = f"{self.base_url_actuales}/{tipo.value}/{provincia_code}"
            else:
                url = f"{self.base_url_actuales}/{tipo}"

            response = self._make_request(
                method = 'GET',
                url = url
            )

            if response.status_code == 404:
                logger.error("No se han encontrado datos para la los parámetros indicados")
                return None
            if response.status_code >= 500:
                logger.error("Ha ocurrido un problema con el servicio al que te comunicas")
                return None
            
            response.raise_for_status()

            return response.text
        
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Servicio Aemet no disponible: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener datos de Aemet: {e}")
            return None
        
    @circuit(cls=CircuitBreakerPersonalizado)
    def get_future_data_by_zone(
        self, 
        tipo_prediccion : TipoPrediccion,
        tipo_zone : TipoZona,
        ccaa_code : Optional[str],
        provincia_code : Optional[str],
        fecha : date
    ):
        try:
            if tipo_zone is TipoZona.NACIONAL:
                url = f"{self.base_url_futuros}/{tipo_prediccion.value}/{tipo_zone.value}/{fecha}"
            elif tipo_zone is TipoZona.CCAA:
                url = f"{self.base_url_futuros}/{tipo_prediccion.value}/{tipo_zone.value}/{ccaa_code}/{fecha}"
            else:
                url = f"{self.base_url_futuros}/tomorrow/{tipo_zone.value}/{provincia_code}/{fecha}"

            response = self._make_request(
                method = 'GET',
                url = url
            )

            if response.status_code == 404:
                logger.error("No se han encontrado datos para la los parámetros indicados")
                return None
            if response.status_code >= 500:
                logger.error("Ha ocurrido un problema con el servicio al que te comunicas")
                return None

            response.raise_for_status()

            return response.text
        
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Servicio Aemet no disponible: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener datos de Aemet: {e}")
            return None


