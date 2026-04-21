from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SensoresDTO():
    humedad_foliar : Optional[float]
    temperatura_DS18B20 : Optional[int]
    temperatura_hojas : Optional[float]
    timestamp : datetime
    temperatura_suelo : Optional[float]
    humedad_suelo : Optional[float]
    temperatura_minima : Optional[float]
    temperatura_maxima : Optional[float]

@dataclass
class GloablSensorDTO():
    eui : str
    resultados : Optional[list[SensoresDTO]]