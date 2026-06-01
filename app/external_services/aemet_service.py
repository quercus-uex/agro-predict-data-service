from helpers.aemet_parser import AemetParser
from flask import current_app
from typing import Optional
from datetime import date, datetime
from ..external_communication.rabbitmq_send import RabbitMQPublisher
from ..external_communication.rabbitmq_config import RabbitMQConfig
from ..external_communication.rabbitmq_receive import RabbitMQConsumer
from ..globals.normalizar_json import normalizar_json
import logging

logger = logging.getLogger(__name__)

class AemetService:
    _cliente = None

    @classmethod
    def _get_cliente(cls):
        """Lazy initialization: crea el cliente solo cuando se necesita"""
        if cls._cliente is None:
            from ..clients.aemet_client import AemetClient
            cls._cliente = AemetClient(app=current_app)
        return cls._cliente

    @classmethod
    def get_aemet_data(
        cls,
        tipo_zona,
        tipo_prediccion : Optional[str],
        codigo_zona : Optional[str],
        fecha : Optional[date]
    ):
        try:
            texto = None

            # Mapeo de código de la zona a int relacionado con los parámetros de AEMET
            if codigo_zona == "CC":
                codigo_zona_id = 10
            elif codigo_zona == "BD":
                codigo_zona_id = 6

            # Llamada a AemetClient 
            ## Obtener datos predictivos
            cliente = cls._get_cliente()
            if tipo_prediccion.value in ["tomorrow", "aftertomorrow"]:
                texto = cliente.get_future_data_by_zone(
                    tipo_prediccion = tipo_prediccion,
                    tipo_zone = tipo_zona,
                    ccaa_code = codigo_zona.lower() if tipo_zona.value == "ccaa" else None,
                    provincia_code = codigo_zona_id if tipo_zona.value == "provincial" else None,
                    fecha = fecha
                ) 
            else: ## Obtener datos de hoy
                texto = cliente.get_current_data_by_zone(
                    tipo = tipo_zona,
                    ccaa_code = codigo_zona.lower() if tipo_zona.value == "ccaa" else None,
                    provincia_code = codigo_zona_id if tipo_zona.value == "provincial" else None
                )
            
            print(f"Texto de aemet : {texto}", flush = True)
            if texto is None:
                logger.warning(f"No se ha obtenido datos de AEMET sobre los parámetros indicados - [ {tipo_zona} - {tipo_prediccion} - {codigo_zona} - {fecha}]")
                return None
            
            # Obtenemos datos parseados obtenidos del texto de respuesta por Aemet
            # Esto será un respaldo por si no obtengo datos del broker
            #parseo = AemetParser.parse(texto = texto)
            
            
            """logger.info("========== RABBITMQ COMMUNICATION ==========")
            # Configuramos la conexion con el broker
            conn, channel, queues = RabbitMQConfig.init_config()
            print("Conexion con el broker establecida", flush = True)
            # Creamos la publicacion en la cola
            RabbitMQPublisher.create_publish(
                channel,
                queues["raw"], 
                texto
            )
            print(f"Se ha enviado el texto de aemet por la cola del broker {queues["raw"]}", flush = True)
            # Obtenemos la respuesta de la cola
            print("Esperando a obtener respuestas por la otra cola")
            json = RabbitMQConsumer.receive_content(
                channel,
                queues["processed"]
            )

            if json:
                # Compruebo si recibo los datos en string
                # Si es así los cambio por diccionario
                normalizar_json(payload = json)
            
            conn.close()
            print(f"JSON recibido : {json}")
            # Obtenemos datos parseados obtenidos del texto de respuesta por Aemet
            ## Esto será un respaldo por si no obtengo datos del broker
            parseo = AemetParser.parse(texto = texto, respuesta_queue = bool(json))"""
            parseo = AemetParser.parse(texto = texto, respuesta_queue = False)

            
            json_predicciones = {
                "tipo_prediccion" : tipo_prediccion.value,
                "tipo_zona" : tipo_zona.value,
                "codigo_zona" : codigo_zona,
                "fecha_prediccion" : parseo["fecha_prediccion"],
                "fecha_elaboracion" : datetime.now(),
                "texto_original" : texto,
                "estado_cielo" : parseo.get("estado_del_cielo"),
                "tendencia_temp_general" : parseo.get("tendencias_de_temperatura_general"),
                "tendencia_temp_max" : parseo.get("tendencia_de_temperaturas_maximas"),
                "tendencia_temp_min" : parseo.get("tendencias_de_temperaturas_minimas"),
                "rachas_viento" : parseo.get("rachas_de_viento"),
                "precipitaciones" : parseo.get("precipitaciones"),
                "cotas_nieve" : parseo.get("cotas_de_nieve"),
                "existencia_helada" : parseo.get("existencias_de_heladas"),
                "zona_helada" : parseo.get("zonas_de_heladas"),
                "aparicion_nieblas" : parseo.get("aparicion_de_nieblas"),
            }

            json_localidades = {
                "temperaturas_localidades" : parseo.get("temperaturas_localidades")
            }

            return json_predicciones, json_localidades
        
        except Exception as e:
            print(f"Ha ocurrido un error en AemetService : {e}")
            return None