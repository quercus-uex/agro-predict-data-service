from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class GrupoPlaga(Enum):
    CEREALES = "cereales"
    LEGUMINOSAS = "leguminosas"

@dataclass
class CalendarioDTO:
    plaga_id : int
    grupo : str
    semana : int
    nivel_alerta : int

@dataclass
class CondicionesDTO:
    tipo : str
    value : any
    operador : str

@dataclass
class PlagaDTO:
    public_id : str
    nombre : str
    agente_causante : str
    momento_critico : str
    observaciones : str
    mas_info : str
    tipo : str
    grupo : str
    condiciones_evaluables : Optional[list[CondicionesDTO]]


@dataclass
class PlagaConCalendarioDTO(PlagaDTO):
    calendario : List[CalendarioDTO]