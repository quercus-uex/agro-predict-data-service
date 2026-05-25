from typing import Optional
from datetime import date, datetime, timedelta
from .forecast_dto import (
    ForecastDTO, 
    TipoPrediccion, 
    TipoZona, 
    CccaaActualFuturoDTO, 
    ProvinciaActualFuturoDTO, 
    NacionActualFuturoDTO,
    TemperaturaLocalidadDTO,
    LocalidadDTO
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
        data_prediccion,
        data_localidad,
        ccaa_id : Optional[str],
        provincia_id : Optional[str]
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
            tipo_prediccion = data_prediccion.get("tipo_prediccion"),
            tipo_zona = data_prediccion.get("tipo_zona"),
            codigo_zona = data_prediccion.get("codigo_zona"),
            fecha_prediccion = data_prediccion.get("fecha_prediccion"),
            fecha_elaboracion = data_prediccion.get("fecha_elaboracion"),
            estado_cielo = data_prediccion.get("estado_cielo"),
            tendencia_temp_general = data_prediccion.get("tendencia_temp_general"),
            tendencia_temp_max = data_prediccion.get("tendencia_temp_max"),
            tendencia_temp_min = data_prediccion.get("tendencia_temp_min"),
            rachas_viento = data_prediccion.get("rachas_viento"),
            precipitaciones = data_prediccion.get("precipitaciones"),
            cotas_nieve = data_prediccion.get("cotas_nieve"),
            existencia_heladas = data_prediccion.get("existencias_heladas"),
            zona_heladas = data_prediccion.get("zona_helada"),
            aparicion_nieblas = data_prediccion.get("aparicion_nieblas"),
            provincia = data_prediccion.get("provincia") if provincia_id else None,
            ccaa = data_prediccion.get("ccaa") if ccaa_id else None,
            temperatura_localidades = data_localidad
        )
    
    @staticmethod
    def _build_localidades(
        data_localidades
    ) -> LocalidadDTO:
        """
        Crea LocalidadDTO sobre los datos pasados por parámetros
        
        :param data_localidades: Todas las localidades almacenadas en la DB
        :return: LocalidadDTO
        """
        
        localidades_dto = []
        for l in data_localidades:
            localidades_dto.append(
                LocalidadDTO(
                    nombre = l['nombre'],
                    nombre_normalizado = l['nombre_normalizado'],
                    altitud = l['altitud'],
                    latitud = l.get('latitud', None),
                    longitud = l.get('longitud', None),
                    provincia = l['codigo']
                )
            )

        return localidades_dto



    @staticmethod
    def _build_data_for_dto(
        ccaa_id : Optional[str],
        provincia_id : Optional[str],
        tipo_zona : str,
        tipo_prediccion : str,
        fecha_prediccion : date
    ):
        if ccaa_id:
            data_prediccion = ForecastDAO._get_predicciones(
                tipo_prediccion = tipo_prediccion,
                tipo_zona = tipo_zona,
                zona_id = ccaa_id,
                fecha_prediccion = fecha_prediccion
            )

            data_localidad = ForecastDAO._get_localidades_climaticas(
                prediccion_id = data_prediccion.get('id')
            )

            localidades_dto = []
            for d in data_localidad:
                localidades_dto.append(
                    TemperaturaLocalidadDTO(
                        nombre = d['nombre'],
                        temperatura_maxima = d['temperatura_maxima'],
                        temperatura_minima = d['temperatura_minima']
                    )
                )

            items = ForecastService._build_forecast(
                data_prediccion = data_prediccion,
                data_localidad = localidades_dto,
                ccaa_id = ccaa_id,
                provincia_id = None
            )

        elif provincia_id:
            data_prediccion = ForecastDAO._get_predicciones(
                tipo_prediccion = tipo_prediccion,
                tipo_zona = tipo_zona,
                zona_id = provincia_id,
                fecha_prediccion = fecha_prediccion
            )

            data_localidad = ForecastDAO._get_localidades_climaticas(
                prediccion_id = data_prediccion.get('id')
            )

            localidades_dto = []

            for d in data_localidad:
                localidades_dto.append(
                    TemperaturaLocalidadDTO(
                        nombre = d['nombre'],
                        temperatura_maxima = d['temperatura_maxima'],
                        temperatura_minima = d['temperatura_minima']
                    )
                )

            items = ForecastService._build_forecast(
                data_prediccion = data_prediccion,
                data_localidad = localidades_dto,
                ccaa_id = None,
                provincia_id = provincia_id
            )

        else:
            data_prediccion = ForecastDAO._get_predicciones(
                tipo_prediccion = tipo_prediccion,
                tipo_zona = tipo_zona,
                zona_id = None,
                fecha_prediccion = fecha_prediccion
            )

            data_localidad = ForecastDAO._get_localidades_climaticas(
                prediccion_id = data_prediccion.get('id')
            )

            localidades_dto = []
            for d in data_localidad:
                localidades_dto.append(
                    TemperaturaLocalidadDTO(
                        nombre = d['nombre'],
                        temperatura_maxima = d['temperatura_maxima'],
                        temperatura_minima = d['temperatura_minima']
                    )
                )
            
            items = ForecastService._build_forecast(
                data_prediccion = data_prediccion,
                data_localidad = localidades_dto,
                ccaa_id = None,
                provincia_id = None
            )

        return items

    @staticmethod
    def get_localidades():
        """
        Obtiene todas las localidades almacenadas en la DB y las retorna en formato
        JSON, construyendo sus DTO
        """
        localidades_db = ForecastDAO._get_localidades()

        return ForecastService._build_localidades(
            localidades_db
        )

    @staticmethod
    def get_forecast(
        app,
        ccaa_id : Optional[str],
        provincia_id : Optional[str],
        tipo_prediccion : TipoPrediccion,
        tipo_zona : TipoZona
    ) -> (
        ProcesoIngestaDTO
        | CccaaActualFuturoDTO
        | ProvinciaActualFuturoDTO
        | NacionActualFuturoDTO
    ):
        # Descomentar solo si se quieren actualizar las localidades que hay en la base de datos
        #IngestionService.ingest_localidad_data()
        
        # Caso base de comprobación de parámetros
        if (ccaa_id and provincia_id) : 
            raise ValueError("Debe indicarse como máximo uno de los dos identificadores de zonas permitidos : `provincia_id`, `ccaa_id`")
        
        #-------------- DESCOMENTAR CUANDO FUNCIONE AEMET
        # Obtengo la fecha de hoy, que es la fecha en la que se consultan los datos
        hoy = date.today() if tipo_prediccion.value == "actual" else date.today() - timedelta(days = 1)

        #fecha_valida_str = "27-04-2026"
        #fecha_valida_date = datetime.strptime(fecha_valida_str, "%d-%m-%Y").date()
        
        # Obtenemos el estado de ingesta buscado
        estado : IngestaStatus = IngestaDAO.obtener_estado(
            dataset = "actual_futuro",
            tipo = tipo_prediccion.value,
            year = hoy.year,
            month = hoy.month,
            day = hoy.day,
            #year = fecha_valida_date.year,
            #month = fecha_valida_date.month,
            #day = fecha_valida_date.day,
            zona = tipo_zona.value,
            error = None,
            codigo = provincia_id if provincia_id else "",
        )

        if estado:
            # Si no se encuentran los datos solicitados en la BD informamos al cliente
            if estado['status'] in ('PENDING', 'LOADING'):

                return ProcesoIngestaDTO(
                    status = estado['status'],
                    datos_solicitados = tipo_prediccion.value,
                    started_at = datetime.now(),
                    finished_at = None,
                    error = None
                )
            # Los datos ya se encuentran en la BD
            elif estado['status'] == 'READY':

                items = ForecastService._build_data_for_dto(
                    ccaa_id = ccaa_id,
                    provincia_id = provincia_id,
                    tipo_zona = tipo_zona.value,
                    tipo_prediccion = tipo_prediccion.value,
                    fecha_prediccion = hoy
                    #fecha_prediccion = fecha_valida_date
                )

                if ccaa_id:

                    return CccaaActualFuturoDTO(
                        type_prediction = tipo_prediccion,
                        type_zone = tipo_zona,
                        datos = items
                    )

                elif provincia_id:
            
                    return ProvinciaActualFuturoDTO(
                        type_prediction = tipo_prediccion,
                        type_zone = tipo_zona,
                        datos = items  
                    )
                
                else:

                    return NacionActualFuturoDTO(
                        type_prediction = tipo_prediccion,
                        type_zone = tipo_zona,
                        datos = items
                    )
            else:
                return ProcesoIngestaDTO(
                    status            = estado.get('status'),
                    datos_solicitados = (
                        f"{tipo_prediccion.value} - {estado.get('zona')} "
                        f"- Fecha: {estado.get('day')}-{estado.get('month')}-{estado.get('year')}"
                    ),
                    started_at  = estado.get('started_at'),
                    finished_at = datetime.now(),
                    error       = estado.get('error_message')
                )
                
        elif ForecastDAO._get_predicciones(
                tipo_prediccion = tipo_prediccion.value, 
                tipo_zona = tipo_zona.value, 
                zona_id = ccaa_id if ccaa_id else provincia_id,
                fecha_prediccion = hoy
                #fecha_prediccion = fecha_valida_date
            ) is not None:

            IngestaDAO.create(
                status = 'READY',
                dataset = 'actual_futuro',
                tipo = tipo_prediccion.value,
                year = hoy.year,
                month = hoy.month,
                day = hoy.day,
                #year = fecha_valida_date.year,
                #month = fecha_valida_date.month,
                #day = fecha_valida_date.day,
                zona = tipo_zona.value,
                started_at = datetime.now(),
                finished_at = datetime.now(),
                error_message = None,
                codigo = provincia_id if provincia_id else "",
            )
             
             # Retornamos READY para que el usuario sepa que tiene que refrescar
            return ProcesoIngestaDTO(
                status = 'READY',
                datos_solicitados = tipo_prediccion.value,
                started_at = datetime.now(),
                finished_at = datetime.now(),
                error = None
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
                #year = fecha_valida_date.year,
                #month = fecha_valida_date.month,
                #day = fecha_valida_date.day,
                zona = tipo_zona.value,
                started_at = datetime.now(),
                finished_at = None,
                error_message = None,
                codigo = provincia_id if provincia_id else "",
            )
            # Hilo independiente al main que inserta datos
            lanzar_ingesta_background(
                app,
                IngestionService.ingest_aemet_data,
                tipo_zona,
                tipo_prediccion,
                ccaa_id if ccaa_id else provincia_id,
                hoy
                #fecha_valida_date
            )

            # Se informa al usuario mientras el hilo va insertando datos
            return ProcesoIngestaDTO(
                status = 'PENDING',
                datos_solicitados = tipo_prediccion.value,
                started_at = datetime.now(),
                finished_at = None,
                error = None
            )