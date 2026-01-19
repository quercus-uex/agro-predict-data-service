from dataclasses import dataclass
from globals.actuales_futuros_dto import ActualesFuturosDTO

# Hereda del DTO global, está pensado para que la serialización sea en base al nombre específico del DTO, así se puede diferenciar en la lógica del proyecto
@dataclass
class ActualesDTO(ActualesFuturosDTO):
    pass