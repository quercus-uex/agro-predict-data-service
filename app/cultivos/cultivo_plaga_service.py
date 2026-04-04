from .cultivos_dao import CultivosDAO
from ..plagas.plagas_dao import PlagasDAO
from .cultivos_dto import (
    CultivoPlagaDTO, 
    CultivoDTO, 
    CalendarioDTO, 
    PlagaConCalendarioDTO
)
from typing import Optional
from ..models import Cultivo
import logging 

logger = logging.getLogger(__name__)

class CultivoPlagaService():


    @staticmethod
    def _build_cultivo_plaga_dto(
        datos : list[dict]
    ) -> Optional[list[CultivoPlagaDTO]]:
        """
        Carga objetos CultivoPlagaDTO sobre los datos pasados por parámetro

        :param datos: Lista de diccionarios de datos pasado por parámetros
        :type datos: list[dict]
        :return: Lista de DTOs cargados
        :rtype: Optional[list[CultivoPlagaDTO]]
        """
        try:
            if not datos:
                return None
            
            cultivos_plagas = []

            for dato in datos:

                datos_cultivo = dato['cultivo']
                datos_plagas = dato['plagas']


                cultivo_plaga_dto = CultivoPlagaDTO(
                    cultivo = CultivoDTO(
                        nombre = datos_cultivo.nombre,
                        nombre_cientifico = datos_cultivo.nombre_cientifico,
                        descripcion = datos_cultivo.descripcion,
                        grupo = datos_cultivo.grupo,
                        sensor = datos_cultivo.sensor_id
                    ),
                    plaga = [
                        PlagaConCalendarioDTO(
                            public_id = p['plaga'].public_id,
                            nombre = p['plaga'].nombre,
                            agente_causante = p['plaga'].agente_causante,
                            momento_critico = p['plaga'].momento_critico,
                            observaciones = p['plaga'].observaciones,
                            mas_info = p['plaga'].mas_info,
                            tipo = p['plaga'].tipo,
                            calendario = [
                                CalendarioDTO(
                                    plaga_id = cal.plaga_id,
                                    grupo = cal.grupo,
                                    semana = cal.semana,
                                    nivel_alerta = cal.nivel_alerta
                                )
                                for cal in p['calendario']
                            ]
                        )
                        for p in datos_plagas
                    ]
                )

                if not cultivo_plaga_dto:
                    return None
                
                cultivos_plagas.append(cultivo_plaga_dto)

            return cultivos_plagas
        
        except Exception as e:
            print(f"Error al crear DTOs de cultivo_plaga : {e}")
            return None

    @staticmethod
    def crear_cultivo_asociado_plaga(
        cultivo : Cultivo
    ):
        """
        Registra en la base de datos la asociación del cultivo creado con sus potenciales plagas

        :param cultivo: Objeto de cultivo creado
        :type cultivo: Cultivo
        """

        # Compruebo que el grupo del cultivo coincide con los registrados en calendario cultivo
        grupo_cultivo_creado = cultivo.grupo
        
        grupos_calendarios = PlagasDAO._get_grupos_calendario()

        if grupo_cultivo_creado not in grupos_calendarios:
            logger.warn(f'No hay registros de calendarios sobre el grupo del cultivo : {grupo_cultivo_creado}')
        
        CultivosDAO.crear_relacion_cultivo_plaga(
            nombre_cultivo = cultivo.nombre
        )

    @staticmethod
    def obtener_cultivo_plaga_asociado(
        nombres_cultivo : list[str]
    ):
        """
        Obtiene información del cultivo con información de posibles plagas y enfermedades asociada

        :param nombre_cultivo: Nombre del cultivo a obtener la información
        :type nombre_cultivo: str
        """
        datos : list[dict] = CultivosDAO.obtener_info_cultivo_plaga(
            nombres_cultivo = nombres_cultivo
        )

        dto_cargado  = CultivoPlagaService._build_cultivo_plaga_dto(
            datos = datos
        )
        
        if not dto_cargado:
            return
        
        return dto_cargado


