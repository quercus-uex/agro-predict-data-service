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
class ForecastDTO:
    tipo_prediccion : TipoPrediccion
    tipo_zona : TipoZona
    codigo_zona : str
    fecha_prediccion : date
    fecha_elaboracion : datetime
    estado_cielo : Optional[str]
    tendencia_temp_general : Optional[str]
    tendencia_temp_max : Optional[str]
    tendencia_temp_min : Optional[str]
    rachas_viento : Optional[str]
    precipitaciones : Optional[str]
    cotas_nieve : Optional[str]
    existencia_heladas : Optional[bool]
    zona_heladas : Optional[str]
    aparicion_nieblas : Optional[str]
    provincia : Optional[str]
    ccaa : Optional[str]

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