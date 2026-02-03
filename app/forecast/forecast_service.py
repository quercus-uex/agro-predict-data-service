from typing import Optional
from datetime import date, datetime, timedelta
from .forecast_dto import (
    ForecastDTO, 
    TipoPrediccion, 
    TipoZona, 
    CccaaActualFuturoDTO, 
    ProvinciaActualFuturoDTO, 
    NacionActualFuturoDTO
)
from ..ingesta.ingesta_dto import ProcesoIngestaDTO
from ..models import IngestaStatus
from ..ingesta.ingesta_dao import IngestaDAO
from ..ingesta.ingesta_thread import lanzar_ingesta_background
from .forecast_dao import ForecastDAO
from ..ingesta.ingesta_service import IngestionService

class ForecastService:

    @staticmethod
    def _build_forecast(
        data,
        ccaa_id : Optional[int],
        provincia_id : Optional[int]
    ) : 
        """
        Construye DTOs de pronósticos climáticos en base a los datos proporcionados
        
        :param data: Datos obtenidos de la base de datos
        :param ccaa_id: Identificador de la comunidad autónoma que estamos consultando
        :type ccaa_id: Optional[int]
        :param provincia_id: Identificador de la provincia que estamos consultando
        :type provincia_id: Optional[int]
        """

        # Como `data` solo va a tener un objeto json, 
        # no es necesario implementar estructuras de datos complejas 
        # ni bucles for
        return ForecastDTO(
            tipo_prediccion = data.get("tipo_prediccion"),
            tipo_zona = data.get("tipo_zona"),
            codigo_zona = data.get("codigo_zona"),
            fecha_prediccion = data.get("fecha_prediccion"),
            fecha_elaboracion = data.get("fecha_elaboracion"),
            estado_cielo = data.get("estado_cielo"),
            tendencia_temp_general = data.get("tendencia_temp_general"),
            tendencia_temp_max = data.get("tendencia_temp_max"),
            tendencia_temp_min = data.get("tendencia_temp_min"),
            rachas_viento = data.get("rachas_viento"),
            precipitaciones = data.get("precipitaciones"),
            cotas_nieve = data.get("cotas_nieve"),
            existencia_heladas = data.get("existencias_heladas"),
            zona_heladas = data.get("zona_helada"),
            aparicion_nieblas = data.get("aparicion_nieblas"),
            provincia = data.get("provincia") if provincia_id else None,
            ccaa = data.get("ccaa") if ccaa_id else None
        )
    
    @staticmethod
    def get_forecast(
        app,
        ccaa_id : Optional[int],
        provincia_id : Optional[int],
        tipo_prediccion : TipoPrediccion,
        tipo_zona : TipoZona
    ) :
        # Caso base de comprobación de parámetros
        if (ccaa_id and provincia_id) : 
            raise ValueError("Debe indicarse como máximo uno de los dos identificadores de zonas permitidos : `provincia_id`, `ccaa_id`")
        
        # Obtengo la fecha de hoy, que es la fecha en la que se consultan los datos
        hoy = date.today() if tipo_prediccion.value is "actual" else date.today() - timedelta(days = 1)
        
        # Obtenemos el estado de ingesta buscado
        estado : IngestaStatus = IngestaDAO.obtener_estado(
            dataset = "actual_futuro",
            tipo = tipo_prediccion.value,
            year = hoy.year,
            month = hoy.month,
            day = hoy.day,
            zona = tipo_zona.value
        )

        print(f"Estado - {estado}", flush = True)

        if estado:
            # Si no se encuentran los datos solicitados en la BD informamos al cliente
            if estado['status'] in ('PENDING', 'LOADING'):
                return ProcesoIngestaDTO(
                    status = estado['status'],
                    datos_solicitados = tipo_prediccion.value,
                    started_at = datetime.now(),
                    finished_at = None
                )
            # Los datos ya se encuentran en la BD
            elif estado['status'] == 'READY':
                if ccaa_id:
                    data = ForecastDAO._get_predicciones(
                        tipo_prediccion = tipo_prediccion.value,
                        tipo_zona = tipo_zona.value,
                        zona_id = ccaa_id
                    )

                    items = ForecastService._build_forecast(
                        data = data,
                        ccaa_id = ccaa_id,
                        provincia_id = None
                    )

                    return CccaaActualFuturoDTO(
                        type_prediction = tipo_prediccion,
                        type_zone = tipo_zona,
                        datos = items
                    )

                elif provincia_id:
                    data = ForecastDAO._get_predicciones(
                        tipo_prediccion = tipo_prediccion.value,
                        tipo_zona = tipo_zona.value,
                        zona_id = provincia_id
                    )

                    items = ForecastService._build_forecast(
                        data = data,
                        ccaa_id = None,
                        provincia_id = provincia_id
                    )

                    return ProvinciaActualFuturoDTO(
                        type_prediction = tipo_prediccion,
                        type_zone = tipo_zona,
                        datos = items  
                    )
                
                else:
                    data = ForecastDAO._get_predicciones(
                        tipo_prediccion = tipo_prediccion.value,
                        tipo_zona = tipo_zona.value,
                        zona_id = None
                    )

                    items = ForecastService._build_forecast(
                        data = data,
                        ccaa_id = None,
                        provincia_id = None
                    )

                    return NacionActualFuturoDTO(
                        type_prediction = tipo_prediccion,
                        type_zone = tipo_zona,
                        datos = items
                    )
        elif ForecastDAO._get_predicciones(
            tipo_prediccion = tipo_prediccion.value, 
            tipo_zona = tipo_zona.value, 
            zona_id = ccaa_id if ccaa_id else provincia_id
            ) is not None:

            IngestaDAO.create(
                status = 'READY',
                dataset = 'actual_futuro',
                tipo = tipo_prediccion.value,
                year = hoy.year,
                month = hoy.month,
                day = hoy.day,
                zona = tipo_zona.value,
                started_at = datetime.now(),
                finished_at = datetime.now(),
                error_message = None
            )
             
             # Retornamos READY para que el usuario sepa que tiene que refrescar
            return ProcesoIngestaDTO(
                status = 'READY',
                datos_solicitados = tipo_prediccion.value,
                started_at = datetime.now(),
                finished_at = datetime.now()
            )
        # Si no se ha comenzado con el proceso de incluir datos nuevos solicitados en la BD se comienza
        else:
            IngestaDAO.create(
                status = 'PENDING',
                dataset = 'actual_futuro',
                tipo = tipo_prediccion.value,
                year = hoy.year,
                month = hoy.month,
                day = hoy.day,
                zona = tipo_zona.value,
                started_at = datetime.now(),
                finished_at = None,
                error_message = None
            )

            # Hilo independiente al main que inserta datos
            lanzar_ingesta_background(
                app,
                IngestionService.ingest_aemet_data,
                tipo_zona,
                tipo_prediccion,
                ccaa_id if ccaa_id else provincia_id,
                hoy
            )

            # Se informa al usuario mientras el hilo va insertando datos
            return ProcesoIngestaDTO(
                status = 'PENDING',
                datos_solicitados = tipo_prediccion.value,
                started_at = datetime.now(),
                finished_at = None
            )