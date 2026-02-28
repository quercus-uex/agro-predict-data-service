
from .cultivos_dao import CultivosDAO
from ..plagas.plagas_dao import PlagasDAO
from ..models import Cultivo
class CultivoPlagaService():

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
            raise ValueError(f'Error, no hay registros de calendarios sobre el grupo del cultivo : {grupo_cultivo_creado}')
        
        CultivosDAO.crear_relacion_cultivo_plaga(
            nombre_cultivo = cultivo.nombre
        )



