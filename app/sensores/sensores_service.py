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
            for sensor in d:
                eui = sensor['id']
                lista_dtos.append(
                    GloablSensorDTO(
                        eui = eui,
                        resultados = [
                            SensoresDTO(
                                humedad_foliar = sensor.get('humedad_foliar', 0.0),
                                temperatura_DS18B20 = sensor.get('temperatura_DS18B20', 0),
                                temperatura_hojas = sensor.get('temperatura_hojas', 0.0),
                                timestamp = sensor.get('timestamp'),
                                temperatura_suelo = sensor.get('temperatura_suelo', 0.0),
                                humedad_suelo = sensor.get('humedad_suelo', 0.0),
                                temperatura_minima = sensor.get('temperatura_minima', 0.0),
                                temperatura_maxima = sensor.get('temperatura_maxima', 0.0)
                            )
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
        contador_verificaciones = 0 
        sensores_sin_datos_almacenados = []
        for eui in euis:
            existe_sensor = SensoresDAO.existe_sensor(
                eui = eui
            )
            if existe_sensor:
                sensores_existentes.append(eui)

            existe_sensor_data = SensoresDAO.existe_sensor_data(
                eui = eui,
                fec_init = fecha_inicio,
                fec_fin = fecha_fin
            )

            if existe_sensor_data:
                contador_verificaciones += 1
            else:
                sensores_sin_datos_almacenados.append(eui)

        if sensores_existentes is []:
            raise APIException(
                status = 404,
                message = f"No existe ningún sensor registrado con eui '{eui}'",
                error = "Data Not Found"
            )


        if contador_verificaciones != len(euis):
        # Almaceno los datos de los sensores en DB
            IngestionService.ingesta_sensores_data(
                euis = sensores_sin_datos_almacenados,
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
        # 'a' añade contenido al final, 'w' sobrescribe el archivo
        with open('registro.txt', 'a') as f:                
            print(datos_resultantes, file=f)

        dto_cargado = SensoresService._build_sensores_dto(
            data = datos_resultantes
        )

        return dto_cargado