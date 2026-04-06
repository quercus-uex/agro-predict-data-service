from typing import Optional
from ..cultivo_parcela_dao import CultivoParcelaDAO
from ..cultivos_dto import CultivoDTO, ParcelaDTO, CultivoParcelaDTO

class CultivoParcelaService:

    @staticmethod
    def _build_asociacion_cultivo_plaga_dto(
        cultivo, 
        parcela,
        fec_init,
        fec_fin
    ):
        cultivo = CultivoDTO(
            nombre = cultivo.nombre,
            nombre_cientifico = cultivo.nombre_cientifico,
            descripcion = cultivo.descripcion,
            grupo = cultivo.grupo
        )

        parcela = ParcelaDTO(
            public_id = parcela.public_id,
            nombre = parcela.nombre
        )

        asociaciones = CultivoParcelaDTO(
            cultivo = cultivo,
            parcela = parcela,
            fecha_inicio = fec_init,
            fecha_fin = fec_fin
        )

        return asociaciones

    @staticmethod
    def registrar_asociacion_parcela_cultivo(
        cultivo,
        nombre_parcela : Optional[str]
    ):
        
        if not cultivo:
            raise ValueError("Error, no se han indicado valores de parámetros necesarios para registrar la asociación")
        
        datos = CultivoParcelaDAO.crear_cultivos_asociados_a_parcelas(
            cultivo = cultivo,
            nombre_parcela = nombre_parcela
        )

        if not datos:
            raise ValueError(f"Error al obtener datos de cultivo {cultivo.nombre} asociados a parcela {nombre_parcela}")
        
    @staticmethod
    def obtener_asociacion_parcela_cultivo(
        nombre_cultivo : Optional[str],
        nombre_parcelas : Optional[str]
    ):
        if not nombre_cultivo and not nombre_parcelas:
            raise ValueError("Error, se debe indical al menos el nombre del cultivo o de la parcela")
        
        datos = CultivoParcelaDAO.obtener_asociaciones_cultivo_parcela(
            nombre_cultivo = nombre_cultivo,
            nombre_parcelas = nombre_parcelas
        )

        if not datos:
            raise ValueError("Error, no se registran en el sistema asociaciones cultivo-parcela sobre los valores de parámetro indicados")

        return [
            dto 
            for cultivo, parcela, fec_init, fec_fin in datos
            if (dto := CultivoParcelaService._build_asociacion_cultivo_plaga_dto(cultivo, parcela, fec_init, fec_fin))
        ]