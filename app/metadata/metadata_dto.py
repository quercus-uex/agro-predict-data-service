from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional

class TipoMetadato(str, Enum):
    PARCELA = "parcela"
    SENSOR = "sensor"
    DISPOSITIVOS = "dispositivos"

@dataclass
class ParcelaDTO:
    public_id : str
    nombre : str
    geometria : dict

@dataclass
class DispositivoDTO:
    public_id : str
    dev_eui : str
    descripcion : str
    nombre : str
    creado : datetime
    actualizado : Optional[datetime]

@dataclass
class SensorDTO:
    eui : str
    dispositivo_id : str
    parcela_id : str
    geometria : dict

@dataclass
class MetadataPorTipoDTO:
    entidad_id : str
    clave : str
    valor : str
    fuente : Optional[str]
    fecha_creacion : Optional[datetime]

@dataclass
class MetadatosDTO:
    tipo : TipoMetadato
    entidad : ParcelaDTO | DispositivoDTO | SensorDTO
    metadatos : MetadataPorTipoDTO
