from .sensores_dao import SensoresDAO
from .sensores_dto import SensoresDTO
from typing import Optional
from datetime import date


class SensoresService():

    @staticmethod
    def _build_sensores_dto(
        data : dict
    ) -> Optional[list[SensoresDTO]]:
        """
        Carga los DTO definidos de Sensores en base a los datos que llegan de 
        la base de datos
        """
        # Guarda
        if not data:
            return
        
        lista_sensores_dto = []

        for d in data:
            lista_sensores_dto.append(
                SensoresDTO(
                    eui = d['eui'],
                    humedad_foliar = d['humedad_foliar'],
                    temperatura_DS18B20 = d['temperatura_DS18B20'],
                    temperatura_hojas = d['temperatura_hojas']
                )
            )
        
        return lista_sensores_dto

    @staticmethod
    def get_sensor_data(
        eui : str,
        fecha_inicio : date,
        fecha_fin : date
    ):
        """
        Obtiene los datos de sensor almacenados en la base de datos
        en base a los valores de parámetros pasados

        :param eui: Identificador público del sensor que obtiene los datos
        :type eui: str
        :param fecha_inicio: Fecha comienzo de recogida de datos
        :type fecha_inicio: date
        :param 
        """
        if not all([eui, fecha_inicio, fecha_fin]):
            raise ValueError("Error, se deben especificar todos los parámetros para obtener datos de sensores (eui, fecha_inicio, fecha_fin)")
        
        datos = SensoresDAO.consultar_datos_sensores(
            eui = eui,
            fecha_inicio = fecha_inicio,
            fecha_fin = fecha_fin
        )

        if not datos:
            raise ValueError("Error, no se han obtenido datos de sensores desde SensoresService")
        
        dto_cargado = SensoresService._build_sensores_dto(
            data = datos
        )

        return dto_cargado
        
