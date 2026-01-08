from enum import Enum
from typing import List, Generic, TypeVar, Optional
from dataclasses import dataclass
from pydantic import ConfigDict
from datetime import datetime

T = TypeVar("T")

class TipoHistorico(str, Enum):
    HORA = "Hora"
    DIA = "Dia"
    SEMANA = "Semana"
    MES = "Mes"

@dataclass
class HistHorasDTO:
    horaMin: int
    tempMedia: float
    humedadMedia: float
    velViento: float
    precipitacion: float
    estacion: str
    fecha: datetime 

@dataclass
class HistDiasDTO:
    tempMedia: float
    tempMax: float
    horMinTempMax: Optional[int]
    tempMin: float
    horMinTempMin: Optional[int]
    humedadMedia: float
    humedadMax: float
    horMinHumMax: Optional[int]
    humedadMin: float
    horMinHumMin: Optional[int]
    velViento: float
    velVientoMax: Optional[float]
    precipitacion: int
    etpMon: float
    pepMon: float
    estacion: str
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)

@dataclass
class HistSemanasDTO:
    anio: int
    semana: int
    tempMedia: float
    tempMax: float
    tempMin: float
    diaHoraTempMax: datetime
    diaHoraTempMin: datetime
    humedadMedia: float
    humedadMax: float
    humedadMin: float
    diaHoraHumMax: datetime
    diaHoraHumMin: datetime
    velViento: float
    velVientoMax: Optional[float]
    precipitacion: float
    etpMon: float
    pepMon: float
    estacion: str    

@dataclass
class HistMesesDTO:
    anio: int
    mes: int
    numDias: int
    tempMedia: float
    tempMax: float
    diaHoraMinTempMax: datetime
    tempMin: float
    diaHoraMinTempMin: datetime
    humedadMedia: float
    humedadMax: float
    diaHoraHumMax: datetime
    humedadMin: float
    diaHoraHumMin: datetime
    velViento: float
    precipitacion: float
    etpMon: float
    pepMon: float
    estacion: str   
    
######### GENERICO PROVINCIAS #########
@dataclass
class ProvinciaHistDTO(Generic[T]):
    type: TipoHistorico
    datos: List[T]
    
######### GENERICO ESTACIONES #########
@dataclass
class EstacionHistDTO(Generic[T]):
    type: TipoHistorico
    datos: List[T]

