from dataclasses import dataclass
from datetime import datetime

@dataclass
class SensoresDTO():
    humedad_foliar : float
    temperatura_DS18B20 : int
    temperatura_hojas : float
    timestamp : datetime