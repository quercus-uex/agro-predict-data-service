from dataclasses import dataclass

@dataclass
class EtapaFenologicaDTO:
    nombre : str
    orden : int

@dataclass
class CultivoDTO:
    nombre : str
    nombre_cientifico : str
    descripcion : str

@dataclass
class ModeloFrioDTO:
    nombre : str
    descripcion : str

@dataclass
class VariedadDTO:
    cultivo : CultivoDTO
    nombre : str
    horas_frio_min : int
    horas_frio_max : int
    modelo : ModeloFrioDTO

@dataclass
class UmbralesTemperatura:
    variedad : VariedadDTO
    etapa_fenologica : EtapaFenologicaDTO
    critico : float
    alto : float
    moderado : float
    bajo : float