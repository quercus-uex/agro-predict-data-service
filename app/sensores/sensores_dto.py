from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SensoresDTO():
    timestamp : datetime
    campo : str
    valor : float
@dataclass
class GloablSensorDTO():
    eui : str
    resultados : Optional[list[SensoresDTO]]