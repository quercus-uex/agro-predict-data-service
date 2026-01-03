from dataclasses import dataclass
from typing import List

@dataclass
class CalendarioDTO:
    nivelAlerta: int
    semana: int

@dataclass
class CalendarioCultivoDTO:
    cultivoId: int
    grupo: str
    calendario: List[CalendarioDTO]

@dataclass
class PlagasDTO:
    id: int
    name: str
    causalAgent: str
    criticalMoment: str
    observaciones: str
    calendarioCultivo: List[CalendarioCultivoDTO]

