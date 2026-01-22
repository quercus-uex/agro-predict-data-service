from ..clients.aemet_client import AemetClient
from app.forecast.forecast_dto import TipoZona, TipoPrediccion
from helpers.aemet_parser import AemetParser
from app import create_app
from typing import Optional
from datetime import date, datetime
from ..external_communication.rabbitmq_send import RabbitMQPublisher
from ..external_communication.rabbitmq_config import RabbitMQConfig
from ..external_communication.rabbitmq_receive import RabbitMQConsumer
import logging
import json as json_module
import ast

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
        
        logger.info("========== RABBITMQ COMMUNICATION ==========")
        # Configuramos la conexion con el broker
        conexion_salida = RabbitMQConfig.init_config()
        conexion_entrada = RabbitMQConfig.init_config()
        print("Conexion con el broker establecida", flush = True)
        # Creamos la publicacion en la cola
        RabbitMQPublisher.create_publish(conexion_salida, texto)
        print("Se ha enviado el texto de aemet por la cola del broker", flush = True)
        # Obtenemos la respuesta de la cola
        print("Esperando a obtener respuestas por la otra cola")
        json = RabbitMQConsumer.receive_content(conexion_entrada)
        if json:
            # Compruebo si recibo los datos en string
            # Si es así los cambio por diccionario
            if isinstance(json, str):
                json = ast.literal_eval(json) 

        # Obtenemos datos parseados obtenidos del texto de respuesta por Aemet
        ## Esto será un respaldo por si no obtengo datos del broker
        parseo = AemetParser.parse(texto = texto, respuesta_queue = bool(json))

        json_final = {
            "tipo_prediccion" : tipo_prediccion,
            "tipo_zona" : tipo_zona,
            "codigo_zona" : codigo_zona,
            "fecha_prediccion" : parseo["fecha_prediccion"],
            "fecha_elaboracion" : datetime.now(),
            "texto_original" : texto,
            "estado_cielo" : json.get("estado_del_cielo") if json else parseo.get("estado_cielo"),
            "tendencia_temp_general" : json.get("tendencias_de_temperatura_general") if json else parseo.get("tendencia_temp_general"),
            "tendencia_temp_max" : json.get("tendencia_de_temperaturas_maximas") if json else parseo.get("tendencia_temp_max"),
            "tendencia_temp_min" : json.get("tendencias_de_temperaturas_minimas") if json else parseo.get("tendencia_temp_min"),
            "rachas_viento" : json.get("rachas_de_viento") if json else parseo.get("viento"),
            "precipitaciones" : json.get("precipitaciones") if json else parseo.get("precipitaciones"),
            "cotas_nieve" : json.get("cotas_de_nieve") if json else parseo.get("cota_nieve"),
            "existencia_helada" : json.get("existencias_de_heladas") if json else parseo.get("existencia_helada"),
            "zona_helada" : json.get("zonas_de_heladas") if json else parseo.get("zona_helada"),
            "aparicion_nieblas" : json.get("aparicion_de_nieblas")
        }

        print(f"Json final: {json_final}")

        return json_final