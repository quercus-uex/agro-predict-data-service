from config.config import Config
from typing import Optional
from metadata_dao import MetadataDAO
from models import Parcelas, Dispositivo, Sensores
import os


class MetadataService:

    MODELOS_DISPONIBLES = {
        'parcelas' : Parcelas,
        'sensores' : Sensores,
        'dispositvos' : Dispositivo
    }

    @staticmethod
    def comprobar_existencia_fichero(
        tipo : str,
        nombre_fichero : str
    ) -> bool:
        ruta = Config.obtener_ruta_contenido_metadatos(tipo)
        elementos = os.listdir(ruta)

        for elemento in elementos:
            if nombre_fichero == elemento:
                return True
        
        return False
    
    @staticmethod
    def _build_metadatos_dto(
        datos,
        tipo
    ):
        if not datos:
            return

        modelo = MetadataService.MODELOS_DISPONIBLES.get(tipo.lower())

        return modelo(*datos)



    @staticmethod
    def obtener_metadatos(
        tipo : str,
        filtros : Optional[dict] = None
    ):
        try:

            modelo = MetadataService.MODELOS_DISPONIBLES.get(tipo.lower())

            if not modelo:
                raise ValueError(f"Tipo de metadato no reconocido : {tipo}")

            datos = MetadataDAO.consultar_registro(
                modelo = modelo,
                filtros = filtros
            )

            if not datos:
                raise ValueError(f"Error, no se han obtenido metadatos para el tipo indicado {tipo}")

            return [
                dto 
                for resultado in datos
                if (dto := MetadataService._build_metadatos_dto(resultado, tipo)) is not None
            ]
        
        except Exception as e:
            print(f"Error al obtener metadatos del tipo {tipo} : {e}")
            return None
        
    
    @staticmethod
    def registrar_modelo(
        tipo : str,
        campos_unicos : list[str],
        nombre_fichero : str,
        mapeo_columnas : dict,

    ):
        pass