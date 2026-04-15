from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SensoresDTO():
    humedad_foliar : float
    temperatura_DS18B20 : int
    temperatura_hojas : float
    timestamp : datetime

@dataclass
class GloablSensorDTO():
    eui : str
    resultados : Optional[list[SensoresDTO]]