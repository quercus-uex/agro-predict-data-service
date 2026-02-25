from dataclasses import dataclass

@dataclass
class SensoresDTO():
    eui : str
    humedad_foliar : float
    temperatura_DS18B20 : int
    temperatura_hojas : float