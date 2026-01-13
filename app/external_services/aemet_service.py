from ..clients.aemet_client import AemetClient, TipoZona, TipoPrediccion
from helpers.aemet_parser import AemetParser
from app import create_app
from typing import Optional
from datetime import date, datetime
from ..external_communication.rabbitmq_send import RabbitMQPublisher
from ..external_communication.rabbitmq_config import RabbitMQConfig
import logging

logger = logging.getLogger(__name__)

class AemetService:
    app = create_app()
    cliente = AemetClient(app)

    @staticmethod
    def get_aemet_data(
        tipo_zona : TipoZona,
        tipo_prediccion : Optional[TipoPrediccion],
        codigo_zona : Optional[str],
        fecha : Optional[date]
    ):
        texto = None

        # Llamada a AemetClient 
        ## Obtener datos predictivos
        if tipo_prediccion in [TipoPrediccion.TOMORROW, TipoPrediccion.AFTERTOMORROW]:
            texto = AemetService.cliente.get_future_data_by_zone(
                tipo_prediccion = tipo_prediccion,
                tipo_zone = tipo_zona,
                ccaa_code = codigo_zona if tipo_zona == TipoZona.CCAA else None,
                provincia_code = codigo_zona if tipo_zona == TipoZona.PROVINCIAL else None,
                fecha = fecha
            ) 
        else: ## Obtener datos de hoy
            texto = AemetService.cliente.get_current_data_by_zone(
                tipo = tipo_zona,
                ccaa_code = codigo_zona if tipo_zona == TipoZona.CCAA else None,
                provincia_code = codigo_zona if tipo_zona == TipoZona.PROVINCIAL else None
            )
        
        if texto is None:
            logger.warning(f"No se ha obtenido datos de AEMET sobre los parámetros indicados - [ {tipo_zona} - {tipo_prediccion} - {codigo_zona} - {fecha}]")
            return None
        
        # Obtenemos datos parseados obtenidos del texto de respuesta por Aemet
        # Esto será un respaldo por si no obtengo datos del broker
        #parseo = AemetParser.parse(texto = texto)
        
        # Configuramos la conexion con el broker
        conexion = RabbitMQConfig.init_config()
        # Creamos la publicacion en la cola
        RabbitMQPublisher.create_publish(conexion, texto)
        # Obtenemos la respuesta de la cola

        # Formateamos el json recibido incluyendo datos obtenidos con el parser

        """json_final = {
            "tipo_prediccion" : tipo_prediccion,
            "tipo_zona" : tipo_zona,
            "codigo_zona" : codigo_zona,
            "fecha_prediccion" : parseo["fecha_prediccion"],
            "fecha_elaboracion" : datetime.now(),
            "texto_original" : texto,
            "estado_cielo" : parseo["estado_cielo"],
            "tendencia_temp_general" : parseo["tendencia_temp_general"],
            "tendencia_temp_max" : parseo["tendencia_temp_max"],
            "tendencia_temp_min" : parseo["tendencia_temp_min"],
            "rachas_viento" : parseo["viento"],
            "precipitaciones" : parseo["precipitaciones"],
            "cotas_nieve" : parseo["cota_nieve"],
            "existencia_helada" : parseo["existencia_helada"],
            "zona_helada" : parseo["zona_helada"]
        }"""
        json_final = {}

        return json_final