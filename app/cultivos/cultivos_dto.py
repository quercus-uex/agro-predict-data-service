from dataclasses import dataclass
from ..plagas.plagas_dto import PlagaConCalendarioDTO, CalendarioDTO
from datetime import datetime

@dataclass
class EtapaFenologicaDTO:
    nombre : str
    codigo : str
    orden : int

@dataclass
class CultivoDTO:
    nombre : str
    nombre_cientifico : str
    descripcion : str
    grupo : str

@dataclass
class ModeloFrioDTO:
    nombre : str
    codigo : str
    descripcion : str

@dataclass
class ParcelaDTO:
    public_id : str
    nombre : str
    geometria : dict

@dataclass
class VariedadDTO:
    nombre_cultivo : str
    nombre : str
    horas_frio_min : int
    horas_frio_max : int
    modelo : ModeloFrioDTO

@dataclass
class UmbralesTemperaturaDTO:
    nombre_variedad : str
    etapa_fenologica : EtapaFenologicaDTO
    critico : float
    alto : float
    moderado : float
    bajo : float

@dataclass
class CultivoPlagaDTO:
    cultivo : CultivoDTO
    plaga : list[PlagaConCalendarioDTO]

@dataclass
class CultivoParcelaDTO:
    cultivo : CultivoDTO
    parcela : ParcelaDTO
    fecha_inicio : datetime
    fecha_fin : datetime
