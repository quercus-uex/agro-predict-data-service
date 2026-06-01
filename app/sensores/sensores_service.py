from .sensores_dao import SensoresDAO
from .sensores_dto import SensoresDTO, GloablSensorDTO
from typing import Optional
from datetime import date
from helpers.ApiExceptions import APIException
from ..ingesta.ingesta_service import IngestionService

class SensoresService():

    @staticmethod
    def _build_sensores_dto(data: list) -> Optional[list]:
        if not data:
            return None

        agrupado = {}  # {eui: GloablSensorDTO}

        for d in data:
            for sensor in d:
                eui = sensor['sensor_id']
                resultado = SensoresDTO(
                    timestamp=sensor.get('timestamp'),
                    campo=sensor.get('campo'),
                    valor=sensor.get('valor'),
                )

                if eui not in agrupado:
                    agrupado[eui] = GloablSensorDTO(eui=eui, resultados=[])
                
                agrupado[eui].resultados.append(resultado)

        return list(agrupado.values())[0] if len(agrupado) == 1 else list(agrupado.values())

    @staticmethod
    def get_sensor_data(
        euis : list[str],
        fecha_inicio : date,
        fecha_fin : date,
        nombre_dtagro : str,
        nombre_predictor : str,
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
                fec_fin = fecha_fin,
                nombre_prediccion = nombre_predictor
            )

            """
            Si yo quiero obtener datos desde el 2026-04-03 hasta el 2026-05-20 y en la BD
            estos sensores solo tienen registrados hasta el 2026-04-20, me van a devolver 
            hasta ahí y los que le siguen hasta el 2026-05-20 no existen por lo que no lo 
            devuelven. En estos casos es necesario hacer una ingesta sobre estos datos 
            faltantes
            """
            fechas_iniciales = []
            if isinstance(existe_sensor_data, date): # Datos faltantes
                fechas_iniciales.append(existe_sensor_data)
                sensores_sin_datos_almacenados.append(eui)
            elif existe_sensor_data:
                contador_verificaciones += 1
            else:
                sensores_sin_datos_almacenados.append(eui)

        if sensores_existentes == []:
            raise APIException(
                status = 404,
                message = f"No existe ningún sensor registrado con eui '{eui}'",
                error = "Data Not Found"
            )

        print(f"DEBUG: fechas iniciales: {fechas_iniciales}")
        if contador_verificaciones != len(euis):
            print("entro a la ingesta")
        # Almaceno los datos de los sensores en DB
            IngestionService.ingesta_sensores_data(
                euis = sensores_sin_datos_almacenados,
                fecha_inicio = fechas_iniciales if fechas_iniciales != [] else fecha_inicio,
                fecha_fin = fecha_fin,
                nombre_dtagro = nombre_dtagro,
                nombre_predictor = nombre_predictor,
            )

        # Obtengo los datos de los sensores sobre DTAgro
        datos_resultantes = []
        for eui in euis:
            datos = SensoresDAO.consultar_datos_sensores(eui, fecha_inicio, fecha_fin)
            datos_resultantes.append(datos)


        if datos_resultantes == []:
            raise APIException(
                status = 404,
                message = "No se han encontrado datos del sensor en DTAgro para los parámetros indicados",
                error = "Data Not Found"
            )

        dto_cargado = SensoresService._build_sensores_dto(
            data = datos_resultantes
        )

        return dto_cargado