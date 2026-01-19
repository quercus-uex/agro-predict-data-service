from dataclasses import dataclass
from enum import Enum
from datetime import date, datetime
from typing import Optional

class TipoZona(str, Enum):
    CCAA = "ccaa"
    NACIONAL = "nacional"
    PROVINCIAL = "provincial"

class TipoPrediccion(str, Enum):
    TOMORROW = "tomorrow"
    AFTERTOMORROW = "aftertomorrow"

@dataclass
class ActualesFuturosDTO:
    tipoPrediccion : TipoPrediccion
    tipoZona : TipoZona
    codigoZona : str
    fechaPrediccion : date
    fechaElaboracion : datetime
    estadoCielo : Optional[str]
    tendenciaTempGeneral : Optional[str]
    tendenciaTempMax : Optional[str]
    tendenciaTempMin : Optional[str]
    rachasViento : Optional[str]
    precipitaciones : Optional[str]
    cotasNieve : Optional[str]
    existenciaHeladas : Optional[bool]
    zonaHeladas : Optional[str]
    aparicionNieblas : Optional[str]
