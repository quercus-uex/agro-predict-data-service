from historico_dao import HistoricDAO
from datetime import datetime, timedelta
from models import MedicionClimatica
from historico_dto import TipoHistorico, HistHorasDTO, HistDiasDTO, HistSemanasDTO, HistMesesDTO
from typing import Optional, List, Match
from collections import defaultdict

class HistoricService:

    @staticmethod
    def _get_mediciones_maxmin(datos) : 
        resultado = defaultdict(dict)

        resultado['medicion_temperatura_max'] = max(datos, key = lambda d : d.temperatura) # Coge la tupla completa, si no usara la lambda, pierdo valor de atributos necesarios
        resultado['medicion_temperatura_min'] = min(datos, key = lambda d : d.temperatura)
        resultado['medicion_humedad_max'] = max(datos, key = lambda d : d.humedad)
        resultado['medicion_humedad_min'] = min(datos, key = lambda d : d.humedad)

        return resultado

    @staticmethod
    def _build_historico_hora(mediciones : Optional[List[MedicionClimatica]]):
        """Construye una lista de DTO por datos agrupados de timestamp horario"""
        grupos = defaultdict(list) # Definición del agrupador de datos

        for m in mediciones: # Recorremos las mediciones obtenidas
            clave = m.timestamp.replace(minute=0, second=0, microsercond=0) # Normalización del timestamp
            # Si tenemos datos 12:23:44 - 12:11:10, reemplaza los timestamp por 12:00:00 - 12:00:00, y entran en el mismo grupo
            
            grupos[clave].append(m) # Agrupo datos

        historico = []

        for hora, datos in grupos.items(): # Creo un DTO por cada medición agrupada
            historico.append(
                HistHorasDTO(
                    horaMin = hora.hora,
                    tempMedia = sum(d.temperatura for d in datos) / len(datos),
                    humedadMedia = sum(d.humedad for d in datos) / len(datos),
                    velViento = sum(d.velViento for d in datos) / len(datos),
                    precipitacion = sum(d.precipitacion for d in datos) / len(datos),
                    estacion = datos[0].estacion.codigo,
                    fecha = hora
                )
            )
        return historico
    
    @staticmethod
    def _build_historico_dia(mediciones : Optional[List[MedicionClimatica]]):
        """Constuye una lista de DTO por datos agrupados de timestamp diario"""
        grupos = defaultdict(list)

        for m in mediciones:
            clave = m.timestamp.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
            grupos[clave].append(m)
        
        historico = []
        for dia, datos in grupos.items():

            mediciones_maxmin = HistoricService._get_mediciones_maxmin(datos)

            historico.append(
                HistDiasDTO(
                    tempMedia = sum(d.temperatura for d in datos) / len(datos),
                    tempMax = mediciones_maxmin.get('medicion_temperatura_max').temperatura,
                    horMinTempMax = mediciones_maxmin.get('mediciones_maxmin').timestamp.hour,
                    tempMin = mediciones_maxmin.get('medicion_temperatura_min').temperatura,
                    horMinTempMin = mediciones_maxmin.get('medicion_temperatura_min').timestamp.hour,
                    humedadMedia = sum(d.humedad for d in datos) / len(datos),
                    humedadMax = mediciones_maxmin.get('medicion_humedad_max').temperatura,
                    horMinHumMax = mediciones_maxmin.get('medicion_humedad_max').timestamp.hour,
                    humedadMin = mediciones_maxmin.get('medicion_humedad_min').temperatura,
                    horMinHumMin = mediciones_maxmin.get('medicion_humedad_min').timestamp.hour,
                    velViento = sum(d.velViento for d in datos) / len(datos),
                    velVientoMax = max(d.velViento for d in datos),
                    precipitacion = sum(d.precipitacion for d in datos) / len(datos),
                    etpMon = sum(d.etpMon for d in datos) / len(datos),
                    pepMon = sum(d.pepMon for d in datos) / len(datos),
                    fecha = dia
                )
            )
        return historico
    
    @staticmethod
    def _build_historico_semana(medicion : Optional[List[MedicionClimatica]]):
        """Construye una lista DTO por datos agrupados de timestamp semanal"""
        grupos = defaultdict(list)
        for m in medicion:
            clave = m.semana # Agrupo las mediciones por la semana 
            grupos[clave].append(m)

        historico = []
        for semana, datos in grupos.items():
            
            mediciones_minmax = HistoricService._get_mediciones_maxmin(datos)
            
            historico.append(
                HistSemanasDTO(
                    anio = sum(d.anio for d in datos) / len(datos),
                    semana = semana,
                    tempMedia = sum(d.temperatura for d in datos) / len(datos),
                    tempMax = mediciones_minmax.get('medicion_temperatura_max').temperatura,
                    tempMin = mediciones_minmax.get('mediciones_temperatura_min').temperatura,
                    diaHoraTempMax = mediciones_minmax.get('medicion_temperatura_max').timestamp.day,
                    diaHoraTempMin = mediciones_minmax.get('medicion_temperatura_max').timestamp.day,
                    humedadMedia = sum(d.humedad for d in datos) / len(datos),
                    humedadMax = mediciones_minmax.get('medicion_humedad_max').humedad,
                    humedadMin = mediciones_minmax.get('medicion_humedad_min').humedad,
                    diaHoraHumMax = mediciones_minmax.get('medicion_humedad_max').timestamp.day,
                    diaHoraHumMin = mediciones_minmax.get('medicion_humedad_min').timestamp.day,
                    velViento = sum(d.velViento for d in datos) / len(datos),
                    velVientoMax = max(d.velViento for d in datos),
                    precipitacion = sum(d.precipitacion for d in datos) / len(datos),
                    etpMon = sum(d.etpMon for d in datos) / len(datos),
                    pepMon = sum(d.pepMon for d in datos) / len(datos)
                )
            )
        return historico
    
    @staticmethod
    def _build_historico_mes(medicion : Optional[List[MedicionClimatica]]):
        """Construye una lista DTO por datos agrupados mensuales"""
        grupos = defaultdict(list)

        for m in medicion:
            clave = m.timestamp.replace(day = 0, hour = 0, minute = 0, second = 0, microsecond = 0)
            grupos[clave].append(m)

        historico = []
        for mes, datos in grupos.items():
            
            mediciones_minmax = HistoricService._get_mediciones_maxmin(datos)

            historico.append(
                HistMesesDTO(
                    anio = sum(d.anio for d in datos) / len(datos),
                    mes = mes,
                    numDias = 31 if mes % 2 == 0 else 30,
                    tempMedia = sum(d.temperatura for d in datos) / len(datos),
                    tempMax = mediciones_minmax.get('medicion_temperatura_max').temperatura,
                    diaHoraMinTempMax = mediciones_minmax.get('medicion_temperatura_max').timestamp.day,
                    tempMin = mediciones_minmax.get('medicion_temperatura_min').temperatura,
                    diaHoraMinTempMin = mediciones_minmax.get('medicion_temperatura_min').timestamp.day,
                    humedadMedia = sum(d.humedad for d in datos) / len(datos),
                    humedadMax = mediciones_minmax.get('medicion_humedad_max').humedad,
                    diaHoraHumMax = mediciones_minmax.get('medicion_humedad_max').timestamp.humedad,
                    humedadMin = mediciones_minmax.get('medicion_humedad_min').humedad,
                    diaHoraHumMin = mediciones_minmax.get('medicion_humedad_min').timestamp.day,
                    velViento = sum(d.velViento for d in datos) / len(datos),
                    precipitacion = sum(d.precipitacion for d in datos) / len(datos),
                    etpMon = sum(d.etpMon for d in datos) / len(datos),
                    pepMon = sum(d.pepMon for d in datos) / len(datos)
                )
            )
        return historico

    
    @staticmethod
    def get_historico(
        tipo : TipoHistorico,
        fec_init : datetime,
        fec_fin : datetime,
        provincia_id : Optional[int] = None,
        estacion_id : Optional[int] = None
    ):
        if estacion_id:
            mediciones = HistoricDAO.find_historic_metrics_from_estacion_id(
                estacion_id, 
                fec_init, 
                fec_fin
            )
        
        elif provincia_id:
            mediciones = HistoricDAO.find_historic_metrics_from_provincia_id(
                provincia_id,
                fec_init,
                fec_fin
            )
        else:
            raise ValueError("Debe indicarse la estación o provincia")
        
        match tipo:
            case TipoHistorico.HORA:
                return HistoricService._build_historico_hora(mediciones)
            case TipoHistorico.DIA:
                return HistoricService._build_historico_dia(mediciones)
            case TipoHistorico.SEMANA:
                return HistoricService._build_historico_semana(mediciones)
            case TipoHistorico.MES:
                return HistoricService._build_historico_mes(mediciones)
        
        raise NotImplementedError(f"Tipo {tipo} no implementado")    