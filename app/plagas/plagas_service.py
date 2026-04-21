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
                    condiciones_evaluables = None,
                    calendario = calendarios_plaga
                )
            )

        return plagas
    
    @staticmethod
    def _validar_condiciones_evaluables(condiciones : list):
        """
        Valida que las condiciones a evaluar especificadas 
        formen parte de los recursos registrados en el sistema.
        """
        if not isinstance(condiciones, list):
            raise ValueError("condiciones_evaluables debe de ser una lista")

        # Obtengo los recursos del sistema y valido
        recursos_disponibles = PlagasDAO._get_recursos_disponibles()       
        for idx, cond in enumerate(condiciones):
            if not isinstance(cond, dict):
                raise ValueError(f"Condicion {idx} debe de ser un objeto")
            
            if "tipo" not in condiciones:
                raise ValueError(f"Condición {idx} debe contener un 'tipo'")

            if cond['tipo'] not in recursos_disponibles:
                raise ValueError(
                    f"Tipo de condición '{cond['tipo']}' no permitido."
                    f"Tipos válidos: {recursos_disponibles}"
                )
            
            if 'valor' not in cond:
                raise ValueError(f'Condición {idx} debe contener valor')
            
    @staticmethod
    def _parsear_momento_critico(texto: str) -> list:
        """
        Parsea el texto del momento_critico para generar condiciones evaluables básicas
        como fallback cuando no se envían explícitamente
        """
        import re
        condiciones = []
        
        # Patrones de parseo
        patrones = [
            (r'temperaturas?\s+medias?\s+superiores?\s+a\s+(\d+(?:\.\d+)?)\s*°C', 
             "temperatura_media", ">="),
            (r'temperaturas?\s+máximas?\s+superiores?\s+a\s+(\d+(?:\.\d+)?)\s*°C', 
             "temperatura_max", ">="),
            (r'temperaturas?\s+mínimas?\s+inferiores?\s+a\s+(\d+(?:\.\d+)?)\s*°C', 
             "temperatura_min", "<="),
            (r'lluvias?\s+superiores?\s+a\s+(\d+(?:\.\d+)?)\s*mm', 
             "precipitacion", ">="),
            (r'humedad\s+foliar\s+superior\s+a\s+(\d+(?:\.\d+)?)\s*%', 
             "humedad_hoja", ">="),
        ]
        
        for patron, tipo, operador in patrones:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                condiciones.append({
                    "tipo": tipo,
                    "valor": float(match.group(1)) if '.' in match.group(1) else int(match.group(1)),
                    "operador": operador
                })
        
        # Detectar estación
        if re.search(r'primavera', texto, re.IGNORECASE):
            condiciones.append({"tipo": "estacion", "valor": "primavera"})
        elif re.search(r'verano', texto, re.IGNORECASE):
            condiciones.append({"tipo": "estacion", "valor": "verano"})
        elif re.search(r'otoño', texto, re.IGNORECASE):
            condiciones.append({"tipo": "estacion", "valor": "otoño"})
        elif re.search(r'invierno', texto, re.IGNORECASE):
            condiciones.append({"tipo": "estacion", "valor": "invierno"})
        
        # Detectar estado fenológico
        fenologias = ['brotación', 'floración', 'cuajado', 'envero', 'maduración']
        for fenologia in fenologias:
            if re.search(fenologia, texto, re.IGNORECASE):
                condiciones.append({"tipo": "estado_fenologico", "valor": fenologia})
                break
        
        return condiciones
    
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
        recursos: list,
        condiciones_evaluables: Optional[list] = None,
        ventana_temporal: Optional[list] = None
    ):
        if not all([public_id, nombre, agente_causante, momento_critico, tipo, recursos]):
            raise APIException(
                status=400,
                message="Datos obligatorios incompletos",
                error="BAD_REQUEST"
            )
        try:

            if not condiciones_evaluables:
                condiciones_evaluables = PlagasService._parsear_momento_critico(momento_critico)

            plaga = PlagasDAO.crear_plagas(
                public_id=public_id,
                nombre=nombre,
                agente_causante=agente_causante,
                momento_critico=momento_critico,
                observaciones=observaciones,
                mas_info=mas_info,
                tipo=tipo,
                grupo=grupo,
                recursos=recursos,
                condiciones_evaluables = condiciones_evaluables,
                ventana_temporal = ventana_temporal,
            )

            if not plaga:
                raise APIException(
                    status=400,
                    message="La plaga ya existe",
                    error="DATA_ALREADY_EXISTS"
                )
            
            # De forma paralela se actualizan las asociaciones con los cultivos del mismo grupo
            from ..ingesta.ingesta_service import IngestionService
            IngestionService.ingesta_asociacion_cultivo_plaga(plaga.grupo)

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