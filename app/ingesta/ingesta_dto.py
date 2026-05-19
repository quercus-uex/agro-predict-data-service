from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ProcesoIngestaDTO():
    status : str
    datos_solicitados : str
    started_at : datetime
    finished_at : datetime
    error: Optional[str]