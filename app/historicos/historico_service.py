from historico_dao import HistoricDAO
from datetime import datetime, timedelta
from models import MedicionClimatica
from historico_dto import TipoHistorico, HistHorasDTO, HistDiasDTO, HistSemanasDTO, HistMesesDTO
from typing import Optional, List, Match
from collections import defaultdict
import calendar

class HistoricService:

    @staticmethod
    def _get_mediciones_maxmin(datos) : 
        resultado = {}

        resultado['medicion_temperatura_max'] = max(datos, key = lambda d : d.temperatura) # Coge la tupla completa, si no usara la lambda, pierdo valor de atributos necesarios
        resultado['medicion_temperatura_min'] = min(datos, key = lambda d : d.temperatura)
        resultado['medicion_humedad_max'] = max(datos, key = lambda d : d.humedad)
        resultado['medicion_humedad_min'] = min(datos, key = lambda d : d.humedad)

        return resultado

    @staticmethod
    def _build_historico_hora(data : dict):
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
                    fecha = v.get("fecha")
                )
            )

        return historicos
    
    @staticmethod
    def _build_historico_dia(data : dict):
        """Constuye una lista de DTO por datos agrupados de timestamp diario"""
        historicos = []
        valores = data.get("valores_diarios")
        horas_pico = data.get("horas_pico")

        for v in valores:
            historicos.append(
                HistDiasDTO(
                    tempMedia = v.get("temp_media"),
                    tempMax = v.get("temp_max"),
                    horMinTempMax = horas_pico.get("hora_temp_max").hour if horas_pico.get("hora_temp_max") else None,
                    tempMin = v.get("temp_min"),
                    horMinTempMin = horas_pico.get("hora_temp_min").hour if horas_pico.get("hora_temp_min") else None,
                    humedadMedia = v.get("humedad_media"),
                    humedadMax = v.get("humedad_max"),
                    horMinHumMax = horas_pico.get("hora_humedad_max").hour if horas_pico.get("hora_humedad_max") else None,
                    humedadMin = v.get("humedad_min"),
                    horMinHumMin = horas_pico.get("hora_humedad_min").hour if horas_pico.get("horas_humedad_min") else None,
                    velViento = v.get("vel_viento"),
                    velVientoMax = v.get("vel_viento_max"),
                    precipitacion = v.get("precipitacion"),
                    etpMon = v.get("etp_mon"),
                    pepMon = v.get("pep_mon"),
                    estacion = v.get("estacion"),
                    fecha = v.get("fecha")   
                )
            )

        return historicos
    
    @staticmethod
    def _build_historico_semana(data : dict):
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
                    diaHoraTempMax = horas_pico.get("hora_temp_max").hour if horas_pico.get("hora_temp_max") else None,
                    diaHoraTempMin = horas_pico.get("hora_temp_min").hour if horas_pico.get("hora_temp_min") else None,
                    humedadMedia = v.get("humedad_media"),
                    humedadMax = v.get("humedad_max"),
                    humedadMin = v.get("humedad_min"),
                    diaHoraHumMax = horas_pico.get("hora_humedad_max").hour if horas_pico.get("hora_humedad_max") else None,
                    diaHoraHumMin = horas_pico.get("hora_humedad_min").hour if horas_pico.get("hora_humedad_min") else None,
                    velViento = v.get("vel_viento"),
                    velVientoMax = v.get("vel_viento_max"),
                    etpMon = v.get("etp_mon"),
                    pepMon = v.get("pep_mon"), 
                )
            )
        
        return historicos
    
    @staticmethod
    def _build_historico_mes(data : dict):
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
                    diaHoraMinTempMax = horas_pico.get("hora_temp_max").day if horas_pico.get("hora_temp_max") else None,
                    tempMin = v.get("temp_min"),
                    diaHoraMinTempMin = horas_pico.get("hora_temp_min").day if horas_pico.get("hora_temp_min") else None,
                    humedadMedia = v.get("humedad_media"),
                    humedadMax = v.get("humedad_max"),
                    diaHoraHumMax = horas_pico.get("hora_humedad_max").day if horas_pico.get("hora_humedad_max") else None,
                    diaHoraHumMin = horas_pico.get("hora_humedad_min").day if horas_pico.get("hora_humedad_min") else None,
                    velViento = v.get("vel_viento"),
                    precipitacion = v.get("precipitacion"),
                    etpMon = v.get("etp_mon"),
                    pepMon = v.get("pep_mon"),
                    estacion = v.get('estacion') 
                )
            )

        return historicos

    @staticmethod
    def get_historico(
        tipo : TipoHistorico,
        fec_init : datetime,
        fec_fin : datetime,
        provincia_id : Optional[int] = None,
        estacion_id : Optional[int] = None
    ):
        
        if not (estacion_id or provincia_id):
            raise ValueError("Debe indicarse la estación o provincia")
        
        match tipo:
            case TipoHistorico.HORA:
                data = HistoricDAO.define_computing_data_hora(estacion_id, provincia_id, fec_init, fec_fin)
                return HistoricService._build_historico_hora(data)
            case TipoHistorico.DIA:
                data = HistoricDAO.define_computing_data_dia(estacion_id, provincia_id, fec_init, fec_fin)
                return HistoricService._build_historico_dia(data)
            case TipoHistorico.SEMANA:
                data = HistoricDAO.define_computing_data_semana(estacion_id, provincia_id, fec_init, fec_fin)
                return HistoricService._build_historico_semana(data)
            case TipoHistorico.MES:
                data = HistoricDAO.define_compution_data_mes(estacion_id, provincia_id, fec_init, fec_fin)
                return HistoricService._build_historico_mes(data)
        
        raise NotImplementedError(f"Tipo {tipo} no implementado")    