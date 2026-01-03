from dataclasses import dataclass
from datetime import datetime, date

@dataclass
class CcAaActualDTO:
    provider: str
    ccaa: str
    emision: str
    diaValido: datetime
    fenomeno: str
    pronostico: str

@dataclass
class NacionalActualDTO:
    provider: str
    alcance: str
    emision: datetime
    fechaPrediccion: date
    fenomeno: str
    pronostico: str

@dataclass
class ProvinciaActualDTO:
    # TODO
    pass
