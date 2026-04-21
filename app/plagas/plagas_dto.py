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
class VentanaTemporalDTO:
    modos : str
    temperatura_base : Optional[float]
    gdd_objetivo : Optional[float]
    dias_ventana : Optional[int]
    condiciones_evaluables_override: Optional[list[CondicionesDTO]]
    fecha_inicio_acumulacion: str
    dias_consecutivos : Optional[int]
    nivel_si_cumple : str

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
    ventana_temporal : Optional[list[VentanaTemporalDTO]]


@dataclass
class PlagaConCalendarioDTO(PlagaDTO):
    calendario : List[CalendarioDTO]