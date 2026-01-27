from dataclasses import dataclass
from typing import List
from enum import Enum

class GrupoPlaga(Enum):
    CEREALES = "cereales"
    LEGUMINOSAS = "leguminosas"

@dataclass
class CalendarioDTO:
    cultivo_id : int
    plaga_id : int
    grupo : str
    semana : int
    nivel_alerta : int

@dataclass
class PlagaDTO:
    public_id : str
    nombre : str
    agente_causante : str
    momento_critico : str
    observaciones  : str
    mas_info : str
    tipo : str

    calendario : List[CalendarioDTO]