from config.config import Config
from typing import Optional
from .metadata_dao import MetadataDAO
from ..models import Parcelas, Dispositivos, Sensores
import os
import json
import pandas as pd


class MetadataService:

    MODELOS_DISPONIBLES = {
        'parcelas' : Parcelas,
        'sensores' : Sensores,
        'dispositivos' : Dispositivos
    }

    CAMPOS_UNICOS_MODELO = {
        'parcelas' : ['public_id'],
        'dispositivos' : ['public_id', 'dev_eui'],
        'sensores' : ['eui', 'dispositivo_id', 'parcela_id']
    }

    TRANSFORMACIONES_MODELO = {
        'parcelas' : {'geometria' : lambda x: json.loads(x)['geometry']['coordinates'] if isinstance(x, str) else x},
        'sensores' : {'geometria' : lambda x: json.loads(x)['geometry']['coordinates'] if isinstance(x, str) else x},
        'dispositivos' : {'creado' : lambda x: pd.to_datetime(x).tz_localize(None), "actualizado" : lambda x: pd.to_datetime(x).tz_localize(None)}
    }

    MAPEO_COLUMNAS_FICHERO = {
        'parcelas' : {
            'id' : 'public_id',
            'name' : 'nombre',
            'geojson' : 'geometria'
        },
        'sensores' : {
            'id' : 'eui',
            'geojson' : 'geometria',
        },
        'dispositivos' : {
            'id' : 'public_id',
            'dev_eui' : 'dev_eui',
            'description' : 'descripcion',
            'name' : 'nombre',
            'created_at' : 'creado',
            'updated_at' : 'actualizado'
        }
    }

    @staticmethod
    def comprobar_existencia_fichero(
        tipo : str,
        nombre_fichero : str
    ) -> bool:
        ruta = Config.obtener_ruta_contenido_metadatos(tipo)
        elementos = os.listdir(str(ruta))

        for elemento in elementos:
            if nombre_fichero == elemento:
                return True
        
        return False
    
    @staticmethod
    def obtener_ruta_metadatos(
        tipo : str
    ):
        try:
            return Config.obtener_ruta_contenido_metadatos(tipo)
        except Exception as e:
            print(f"Error al obtener la ruta donde se va a almacenar el fichero de metadatos : {e}")
            return None

        
    
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
        nombre_fichero : str,
    ):
        from ..ingesta.ingesta_service import IngestionService
        try:

            if not MetadataService.MODELOS_DISPONIBLES.get(tipo.lower()):
                raise ValueError(f"Tipo de modelo no reconocido: {tipo}")
            
            # Obtengo los campos únicos basados en el tipo de modelo pasado por parámetros
            campos_unicos : list[str] = MetadataService.CAMPOS_UNICOS_MODELO.get(tipo.lower())
            modelo = MetadataService.MODELOS_DISPONIBLES.get(tipo.lower())
            mapeo_columnas = MetadataService.MAPEO_COLUMNAS_FICHERO.get(tipo.lower())
            transformaciones = MetadataService.TRANSFORMACIONES_MODELO.get(tipo.lower())

            ruta_metadatos = MetadataService.obtener_ruta_metadatos(tipo)

            IngestionService.ingesta_metadata(
                modelo = modelo,
                campos_unicos = campos_unicos,
                nombre_fichero = nombre_fichero,
                mapeo_columnas = mapeo_columnas,
                transformaciones = transformaciones,
                ruta_fichero = ruta_metadatos
            )

        except Exception as e:
            print(f"Error al registrar el fichero {nombre_fichero} : {e}")