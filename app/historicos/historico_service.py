from .historico_dao import HistoricDAO
from datetime import datetime
from ..models import IngestaStatus
from .historico_dto import *
from ..ingesta.ingesta_dto import ProcesoIngestaDTO
from ..ingesta.ingesta_dao import IngestaDAO
from ..ingesta.ingesta_service import IngestionService
from ..ingesta.ingesta_thread import lanzar_ingesta_background
import threading
import calendar

class HistoricService:

    @staticmethod
    def _build_historico_hora(
        data,
        estacion_id
    ):
        """Construye DTOs diarios usando los datos del DAO"""
        historicos = []
        valores = data.get("valores_diarios")

        for v in valores:
            historicos.append(
                HistHorasDTO(
                    horaMin = v.get("hora"),
                    tempMedia = v.get("temp_media"),
                    humedadMedia = v.get("humedad_media"),
                    velViento = v.get("vel_viento"),
                    precipitacion = v.get("precipitacion"),
                    estacion = v.get("estacion"),
                    estaciones = data.get("estaciones_usadas") if estacion_id is None else None,
                    fecha = v.get("fecha")
                )
            )

        return historicos
    
    @staticmethod
    def _build_historico_dia(
        data,
        estacion_id
    ):
        """Constuye una lista de DTO por datos agrupados de timestamp diario"""
        historicos = []
        valores = data.get("valores_diarios")
        horas_pico = data.get("horas_pico")
        for v in valores:
            dto_kwargs = {
                "tempMedia": v.get("temp_media"),
                "tempMax": v.get("temp_max"),
                "horMinTempMax": horas_pico.get("hora_temp_max") if horas_pico.get("hora_temp_max") else None,
                "tempMin": v.get("temp_min"),
                "horMinTempMin": horas_pico.get("hora_temp_min") if horas_pico.get("hora_temp_min") else None,
                "humedadMedia": v.get("humedad_media"),
                "humedadMax": v.get("humedad_max"),
                "horMinHumMax": horas_pico.get("hora_humedad_max") if horas_pico.get("hora_humedad_max") else None,
                "humedadMin": v.get("humedad_min"),
                "horMinHumMin": horas_pico.get("hora_humedad_min") if horas_pico.get("hora_humedad_min") else None,
                "velViento": v.get("vel_viento"),
                "velVientoMax": v.get("vel_viento_max"),
                "precipitacion": v.get("precipitacion"),
                "etpMon": v.get("etp_mon"),
                "pepMon": v.get("pep_mon"),
                "estacion": v.get("estacion"),
                "provincia": v.get("provincia"),
                "fecha": v.get("fecha")
            }

            if estacion_id is None:
                dto_kwargs["estaciones"] = data.get("estaciones_usadas")
            else:
                dto_kwargs["estaciones"] = None

            historicos.append(HistDiasDTO(**dto_kwargs))

        return historicos
    
    @staticmethod
    def _build_historico_semana(
        data,
        estacion_id
    ):
        """Construye una lista DTO por datos agrupados de timestamp semanal"""
        historicos = []
        valores = data.get("valores_diarios")
        horas_pico = data.get("horas_pico")

        for v in valores:
            historicos.append(
                HistSemanasDTO(
                    anio = v.get("anio"),
                    semana = v.get("semana"),
                    tempMedia = v.get("temp_media"),
                    tempMax = v.get("temp_max"),
                    tempMin = v.get("temp_min"),
                    diaHoraTempMax = horas_pico.get("hora_temp_max") if horas_pico.get("hora_temp_max") else None,
                    diaHoraTempMin = horas_pico.get("hora_temp_min") if horas_pico.get("hora_temp_min") else None,
                    humedadMedia = v.get("humedad_media"),
                    humedadMax = v.get("humedad_max"),
                    humedadMin = v.get("humedad_min"),
                    diaHoraHumMax = horas_pico.get("hora_humedad_max") if horas_pico.get("hora_humedad_max") else None,
                    diaHoraHumMin = horas_pico.get("hora_humedad_min") if horas_pico.get("hora_humedad_min") else None,
                    velViento = v.get("vel_viento"),
                    velVientoMax = v.get("vel_viento_max"),
                    precipitacion = v.get("precipitacion"),
                    etpMon = v.get("etp_mon"),
                    pepMon = v.get("pep_mon"), 
                    estacion = v.get("estacion"),
                    estaciones = data.get("estaciones_usadas") if estacion_id is None else None,
                    provincia = v.get("provincia")
                )
            )
        
        return historicos
    
    @staticmethod
    def _build_historico_mes(
        data,
        estacion_id
    ):
        """Construye una lista DTO por datos agrupados mensuales"""
        historicos = []
        valores = data.get("valores_diarios")
        horas_pico = data.get("horas_pico")

        for v in valores:
            historicos.append(
                HistMesesDTO(
                    anio = v.get("anio"),
                    mes = v.get("mes"),
                    numDias = calendar.monthrange(v.get("anio"), v.get("mes"))[1],
                    tempMedia = v.get("temp_media"),
                    tempMax = v.get("temp_max"),
                    diaHoraMinTempMax = horas_pico.get("hora_temp_max") if horas_pico.get("hora_temp_max") else None,
                    tempMin = v.get("temp_min"),
                    diaHoraMinTempMin = horas_pico.get("hora_temp_min") if horas_pico.get("hora_temp_min") else None,
                    humedadMedia = v.get("humedad_media"),
                    humedadMax = v.get("humedad_max"),
                    diaHoraHumMax = horas_pico.get("hora_humedad_max") if horas_pico.get("hora_humedad_max") else None,
                    diaHoraHumMin = horas_pico.get("hora_humedad_min") if horas_pico.get("hora_humedad_min") else None,
                    velViento = v.get("vel_viento"),
                    precipitacion = v.get("precipitacion"),
                    etpMon = v.get("etp_mon"),
                    pepMon = v.get("pep_mon"),
                    estacion = v.get("estacion"),
                    estaciones = data.get("estaciones_usadas") if estacion_id is None else None,
                    provincia = v.get("provincia") 
                )
            )

        return historicos

    @staticmethod
    def get_historico(
        app,
        tipo : TipoHistorico,
        fec_init : datetime,
        fec_fin : datetime,
        provincia_id : Optional[str] = None,
        estacion_id : Optional[int] = None
    ):
        print(f"Thread running: {threading.current_thread().name}")
        if not (estacion_id or provincia_id):
            raise ValueError("Debe indicarse la estación o provincia")
        
        # Obtenemos el estado de ingesta buscado
        estado : IngestaStatus = IngestaDAO.obtener_estado(
            dataset = 'historico',
            tipo = tipo.value,
            year = fec_init.year,
            month = fec_init.month,
            day = fec_init.day,
            zona = "provincia" if provincia_id else "estacion"
        )

        if estado:
            # Si no se encuentran los datos solicitados en la BD informamos al cliente
            if estado['status'] in ('PENDING', 'LOADING'):
                return ProcesoIngestaDTO(
                    status = estado['status'],
                    datos_solicitados = tipo.value,
                    started_at = datetime.now(),
                    finished_at = None
                )
            # Datos ya se encuentran en la BD
            elif estado['status'] == 'READY':
                provincia_id = HistoricDAO.obtener_id_provincia_por_str(provincia_id = provincia_id)

                match tipo:
                    case TipoHistorico.HORA:
                        data = HistoricDAO.define_computing_data_hora(estacion_id, provincia_id, fec_init, fec_fin)
                        items =  HistoricService._build_historico_hora(data, estacion_id)

                        return HistoricService.comprobar_devolucion(
                            estacion_id = estacion_id,
                            provincia_id = provincia_id,
                            tipo = tipo,
                            datos = items
                        )

                    case TipoHistorico.DIA:
                        data = HistoricDAO.define_computing_data_dia(estacion_id, provincia_id, fec_init, fec_fin)    
                        items = HistoricService._build_historico_dia(data, estacion_id)

                        return HistoricService.comprobar_devolucion(
                            estacion_id = estacion_id,
                            provincia_id = provincia_id,
                            tipo = tipo,
                            datos = items
                        )
                    
                    case TipoHistorico.SEMANA:
                        data = HistoricDAO.define_computing_data_semana(estacion_id, provincia_id, fec_init, fec_fin)
                        items = HistoricService._build_historico_semana(data, estacion_id)

                        return HistoricService.comprobar_devolucion(
                            estacion_id = estacion_id,
                            provincia_id = provincia_id,
                            tipo = tipo,
                            datos = items
                        )
                    
                    case TipoHistorico.MES:
                        data = HistoricDAO.define_compution_data_mes(estacion_id, provincia_id, fec_init, fec_fin)
                        items = HistoricService._build_historico_mes(data, estacion_id)

                        return HistoricService.comprobar_devolucion(
                            estacion_id = estacion_id,
                            provincia_id = provincia_id,
                            tipo = tipo,
                            datos = items
                        )
                    case _:
                        raise NotImplementedError(f"Tipo {tipo} no implementado")
        # Si existen datos ya registrados, incluimos su estado a ready    
        elif HistoricDAO.define_computing_general(estacion_id,provincia_id,fec_init,fec_fin) is not None or []:
            IngestaDAO.create(
                status = 'READY',
                dataset = 'historico',
                tipo = tipo.value,
                year = fec_init.year,
                month = fec_init.month,
                day = fec_init.day,
                zona = "provincia" if provincia_id else "estacion",
                started_at = datetime.now(),
                finished_at = datetime.now(),
                error_message = None
            )

            # Retornamos READY para que el usuario sepa que tiene que refrescar
            return ProcesoIngestaDTO(
                status = 'READY',
                datos_solicitados = tipo.value,
                started_at = datetime.now(),
                finished_at = datetime.now()
            )
        # Si no se ha comenzado con el proceso de incluir datos nuevos solicitados en la BD se comienza
        else:
            IngestaDAO.create(
                status = 'PENDING',
                dataset = 'historico',
                tipo = tipo.value,
                year = fec_init.year,
                month = fec_init.month,
                day = fec_init.day,
                zona = "provincia" if provincia_id else "estacion",
                started_at = datetime.now(),
                finished_at = None,
                error_message = None
            )

            # Hilo independiente al main que inserta datos
            lanzar_ingesta_background(
                app,
                IngestionService.ingest_siar_data,
                estacion_id,
                provincia_id,
                tipo,
                fec_init,
                fec_fin 
            )

            # Se informa al usuario mientras el hilo va insertando datos
            return ProcesoIngestaDTO(
                status = 'PENDING',
                datos_solicitados = tipo.value,
                started_at = datetime.now(),
                finished_at = None
            )
    
    @staticmethod
    def comprobar_devolucion(
        estacion_id : Optional[int],
        provincia_id : Optional[int],
        tipo : TipoHistorico,
        datos
    ) -> ProvinciaHistDTO | EstacionHistDTO:
        
        if provincia_id:
            return ProvinciaHistDTO(type = tipo, datos = datos)
        elif estacion_id:
            return EstacionHistDTO(type = tipo, datos = datos)
        else:
            raise ValueError("Se debe proporcionar el valor de estacion_id o de provincia_id, no pueden estar los dos a null")
