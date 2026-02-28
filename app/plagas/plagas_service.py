from .plagas_dao import PlagasDAO
from .plagas_dto import *
from typing import Optional

class PlagasService:

    @staticmethod
    def _build_calendar(
        data
    ) -> List[CalendarioDTO] : 
        """
        Construye los DTO del calendario sobre cada plaga
        
        :param data: Datos obtenidos de la base de datos
        """

        calendarios = []

        for c in data:
            calendarios.append(
                CalendarioDTO(
                    cultivo_id = c.get('cultivo_id'),
                    plaga_id = c.get('plaga_id'),
                    grupo = c.get('grupo'),
                    semana = c.get('semana'),
                    nivel_alerta = c.get('nivel_alerta')
                )
            )
        
        return calendarios
    
    @staticmethod
    def _build_plagas(
        data_plagas,
        data_calendario
    ) -> List[PlagaDTO] :
        """
        Construye los DTO de cada plaga obtenida
        
        :param data_plagas: Datos de las plagas obtenidos por la bd
        :param data_calendario: Lista d eCalendarioDTO
        """

        plagas = []

        for p in data_plagas:
            
            # Filtro los datos de los calendarios por el específico de la plaga
            calendarios_plaga = [
                cal for cal in data_calendario
                if cal.plaga_id == p.get('id')
            ]

            plagas.append(
                PlagaDTO(
                    public_id = p.get('public_id'),
                    nombre = p.get('nombre'),
                    agente_causante = p.get('agente_causante'),
                    momento_critico = p.get('momento_critico'),
                    observaciones = p.get('observaciones'),
                    mas_info = p.get('mas_info'),
                    tipo = p.get('tipo'),
                    calendario = calendarios_plaga
                )
            )

        return plagas
    
    @staticmethod
    def get_plagas(
        tipo : str,
        plaga_id : Optional[int]
    ):

        # Obtengo los datos de las plagas de la BD
        data_plagas = PlagasDAO._get_plagas(
            tipo = tipo,
            plaga_id = plaga_id if plaga_id else None
        )

        print(f"Datos de la plaga : {data_plagas}")

        # Obtengo los datos de los calendarios de la BD
        data_calendarios = PlagasDAO._get_calendario_plagas(
            plaga_id = plaga_id if plaga_id else None
        )

        # Contruyo los DTOs de los calendarios
        calendarios = PlagasService._build_calendar(data_calendarios)

        # Construyo los DTOs de las plagas
        plagas = PlagasService._build_plagas(
            data_plagas = data_plagas,
            data_calendario = calendarios
        )

        return plagas