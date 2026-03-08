from dataclasses import dataclass
from ..plagas.plagas_dto import PlagaDTO, CalendarioDTO

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
    sensor : str

@dataclass
class ModeloFrioDTO:
    nombre : str
    codigo : str
    descripcion : str

@dataclass
class VariedadDTO:
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
    plaga : list[PlagaDTO]
