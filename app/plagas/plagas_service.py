from .plagas_dao import PlagasDAO
from .plagas_dto import *
from typing import Optional
from helpers.ApiExceptions import APIException

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
                PlagaConCalendarioDTO(
                    public_id = p.get('public_id'),
                    nombre = p.get('nombre'),
                    agente_causante = p.get('agente_causante'),
                    momento_critico = p.get('momento_critico'),
                    observaciones = p.get('observaciones'),
                    mas_info = p.get('mas_info'),
                    tipo = p.get('tipo'),
                    grupo = p.get('grupo'),
                    calendario = calendarios_plaga
                )
            )

        return plagas
    
    @staticmethod
    def get_plagas(
        grupo : str,
        tipo : str,
        plaga_id : Optional[int]
    ):
        try:
            # Obtengo los datos de las plagas de la BD
            data_plagas = PlagasDAO._get_plagas(
                grupo = grupo,
                tipo = tipo,
                plaga_id = plaga_id if plaga_id else None
            )

            plagas_con_calendario = []
            for d in data_plagas:
                if d['calendario'] is not None:
                    plagas_con_calendario.append(d['calendario'])

            # Contruyo los DTOs de los calendarios
            calendarios = []
            if plagas_con_calendario is not []:
                calendarios = PlagasService._build_calendar(plagas_con_calendario)

            # Construyo los DTOs de las plagas
            plagas = PlagasService._build_plagas(
                data_plagas = data_plagas,
                data_calendario = calendarios
            )

            return plagas
        
        except Exception as e:
            raise APIException(
                status=500,
                message = f"Error interno al consultar datos sobre plagas : {e}",
                error="INTERNAL_ERROR"
            )
    
    @staticmethod
    def registrar_plaga(
        public_id: str,
        nombre: str,
        agente_causante: str,
        momento_critico: str,
        observaciones: Optional[str],
        mas_info: Optional[str],
        tipo: str,
        grupo: str,
        recursos: list
    ):
        if not all([public_id, nombre, agente_causante, momento_critico, tipo, recursos]):
            raise APIException(
                status=400,
                message="Datos obligatorios incompletos",
                error="BAD_REQUEST"
            )

        try:
            plaga = PlagasDAO.crear_plagas(
                public_id=public_id,
                nombre=nombre,
                agente_causante=agente_causante,
                momento_critico=momento_critico,
                observaciones=observaciones,
                mas_info=mas_info,
                tipo=tipo,
                grupo=grupo,
                recursos=recursos
            )

            if not plaga:
                raise APIException(
                    status=400,
                    message="La plaga ya existe",
                    error="DATA_ALREADY_EXISTS"
                )

            return plaga

        except ValueError as e:
            raise APIException(
                status=400,
                message=str(e),
                error="INVALID_DATA"
            )

        except Exception as e:
            raise APIException(
                status=500,
                message = f"Error interno al registrar la plaga : {e}",
                error="INTERNAL_ERROR"
            )