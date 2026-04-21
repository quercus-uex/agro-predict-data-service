from .sensores_dao import SensoresDAO
from .sensores_dto import SensoresDTO, GloablSensorDTO
from typing import Optional
from datetime import date
from helpers.ApiExceptions import APIException
from ..external_services.dtagro_service import DTAgroService
from ..ingesta.ingesta_service import IngestionService

class SensoresService():

    @staticmethod
    def _build_sensores_dto(
        data
    ) -> Optional[list[SensoresDTO]]:
        """
        Carga los DTO definidos de Sensores en base a los datos que llegan de 
        la base de datos
        """
        # Guarda
        if not data:
            return
        
        lista_dtos = []
        # Me llega una lista
        for d in data:
            eui = d['eui']
            resultados = d.get('resultados', None)

            lista_dtos.append(
                GloablSensorDTO(
                    eui = eui,
                    resultados = [
                        SensoresDTO(
                            humedad_foliar = r.get('humedad_foliar', 0.0),
                            temperatura_DS18B20 = r.get('temperatura_DS18B20', 0),
                            temperatura_hojas = r.get('temperatura_hojas', 0.0),
                            timestamp = r.get('timestamp'),
                            temperatura_suelo = r.get('temperatura_suelo', 0.0),
                            humedad_suelo = r.get('humedad_suelo', 0.0),
                            temperatura_minima = r.get('temperatura_minima', 0.0),
                            temperatura_maxima = r.get('temperatura_maxima', 0.0)
                        )
                        for r in resultados
                    ]
                )
            )

        return lista_dtos

    @staticmethod
    def get_sensor_data(
        euis : list[str],
        fecha_inicio : date,
        fecha_fin : date
    ):
        """
        Obtiene los datos de sensor almacenados en la base de datos
        en base a los valores de parámetros pasados

        :param eui: Lista de identificadores Identificadores público del sensor que obtiene los datos
        :type eui: list[str]
        :param fecha_inicio: Fecha comienzo de recogida de datos
        :type fecha_inicio: date
        :param fecha_fin: Fecha fin de recogida de datos
        :type fecha_fin: date
        """
        sensores_existentes = []
        for eui in euis:
            existe_sensor = SensoresDAO.existe_sensor(
                eui = eui
            )
            if existe_sensor:
                sensores_existentes.append(eui)

        if sensores_existentes is []:
            raise APIException(
                status = 404,
                message = f"No existe ningún sensor registrado con eui '{eui}'",
                error = "Data Not Found"
            )

        # Almaceno los datos de los sensores en DB
        IngestionService.ingesta_sensores_data(
            euis = euis,
            fecha_inicio = fecha_inicio,
            fecha_fin = fecha_fin
        )

        # Obtengo los datos de los sensores sobre DTAgro
        datos_resultantes = []
        for eui in euis:
            datos = SensoresDAO.consultar_datos_sensores(eui, fecha_inicio, fecha_fin)
            datos_resultantes.append(datos)


        if datos_resultantes is []:
            raise APIException(
                status = 404,
                message = "No se han encontrado datos del sensor en DTAgro para los parámetros indicados",
                error = "Data Not Found"
            )

        dto_cargado = SensoresService._build_sensores_dto(
            data = datos_resultantes
        )

        return dto_cargado