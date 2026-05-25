from dataclasses import dataclass
from enum import Enum
from datetime import date, datetime
from typing import Optional, TypeVar, Generic, List

T = TypeVar("T")

class TipoZona(str, Enum):
    CCAA = "ccaa"
    NACIONAL = "nacional"
    PROVINCIAL = "provincial"

class TipoPrediccion(str, Enum):
    ACTUAL = "actual"
    TOMORROW = "tomorrow"
    AFTERTOMORROW = "aftertomorrow"

@dataclass
class TemperaturaLocalidadDTO:
    nombre : str
    temperatura_maxima : int
    temperatura_minima : int

@dataclass
class LocalidadDTO:
    nombre : str
    nombre_normalizado : str
    altitud : int
    latitud : float
    longitud : float
    provincia : str

@dataclass
class ForecastDTO:
    tipo_prediccion : TipoPrediccion
    tipo_zona : TipoZona
    codigo_zona : str
    fecha_prediccion : date
    fecha_elaboracion : datetime
    estado_cielo : Optional[str] = None
    tendencia_temp_general : Optional[str] = None
    tendencia_temp_max : Optional[str] = None
    tendencia_temp_min : Optional[str] = None
    rachas_viento : Optional[str] = None
    precipitaciones : Optional[str] = None
    cotas_nieve : Optional[str] = None
    existencia_heladas : Optional[bool] = None
    zona_heladas : Optional[str] = None
    aparicion_nieblas : Optional[str] = None
    provincia : Optional[str] = None
    ccaa : Optional[str] = None
    temperatura_localidades : Optional[List[TemperaturaLocalidadDTO]] = None

##### GENERICO CCAA #####
@dataclass
class CccaaActualFuturoDTO(Generic[T]):
    type_prediction : TipoPrediccion
    type_zone : TipoZona
    datos : List[T]

##### GENERICO PROVINCIA #####
@dataclass
class ProvinciaActualFuturoDTO(Generic[T]):
    type_prediction : TipoPrediccion
    type_zone : TipoZona
    datos : List[T]

##### GENERICO NACION ######
@dataclass
class NacionActualFuturoDTO(Generic[T]):
    type_prediction : TipoPrediccion
    type_zone : TipoZona
    datos : List[T]