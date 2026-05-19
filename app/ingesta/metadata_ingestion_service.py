from app.extensions import db
from typing import Optional
from ..ingesta.ingesta_dao import IngestaDAO
from ..metadata.metadata_dao import MetadataDAO
from ..models import Cultivo
from helpers.ApiExceptions import APIException
from ..cultivos.services.cultivo_plaga_service import CultivoPlagaService
import pandas as pd
import json
import os
import logging

logger = logging.getLogger(__name__)


class MetadataIngestionService:

    @staticmethod
    def ingesta_asociacion_cultivo_plaga(grupo_plaga: str):
        cultivos = db.session.query(Cultivo).filter_by(grupo=grupo_plaga).all()
        if not cultivos:
            raise APIException(
                message = "No se han encontrado cultivos asociados a la plaga",
                status  = 404,
                error   = 'DATA_NOT_FOUND'
            )
        for cultivo in cultivos:
            CultivoPlagaService.crear_cultivo_asociado_plaga(cultivo)

    @staticmethod
    def ingesta_recursos_globales_plagas():
        try:
            BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(BASE_DIR, "..", "data", "datos_recursos_plagas_glob.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            IngestaDAO.crear_tipos_datos(datos)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error insertando tipos de datos: {e}")

    @staticmethod
    def ingesta_metadata(
        modelo,
        campos_unicos: list[str],
        nombre_fichero: str,
        mapeo_columnas: dict,
        ruta_fichero: str,
        transformaciones: Optional[dict] = None
    ):
        try:
            df = pd.read_csv(ruta_fichero / nombre_fichero)
            df = df.rename(columns=mapeo_columnas)[list(mapeo_columnas.values())]

            if 'geometria' in df.columns and modelo.__name__.lower() == 'sensores':
                def extraer_dev_eui(x):
                    if not isinstance(x, str):
                        return None
                    dev_eui = json.loads(x).get('properties', {}).get('dev_eui')
                    return None if not dev_eui or dev_eui.strip() in ('-', '', 'null', 'None') else dev_eui
                df['dispositivo_id'] = df['geometria'].apply(extraer_dev_eui)

            if transformaciones:
                for campo, fn in transformaciones.items():
                    if campo in df.columns:
                        df[campo] = df[campo].apply(fn)

            if 'geometria' in df.columns:
                df['geometria'] = df['geometria'].apply(
                    lambda x: x.get('geometry', {}).get('coordinates') if isinstance(x, dict) else x
                )

            contenido = [
                {k: (None if isinstance(v, float) and pd.isna(v) else v) for k, v in r.items()}
                for r in df.to_dict(orient="records")
            ]

            insertados = sum(
                1 for r in contenido
                if MetadataDAO.crear_registro(modelo=modelo, datos=r, campos_unicos=campos_unicos)
            )
            logger.info(f"Ingesta {modelo.__name__}: {insertados} registros insertados")
        except Exception as e:
            logger.error(f"Error ingestando {modelo.__name__}: {e}")

    @staticmethod
    def ingest_localidad_data():
        try:
            BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(BASE_DIR, "..", "data", "location_altitudes.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            for d in datos:
                IngestaDAO.crear_localidades(
                    nombre             = d['nombre'],
                    nombre_normalizado = d['nombre_normalizado'],
                    altitud            = d['altitud'],
                    longitud           = d['longitud'],
                    latitud            = d['latitud'],
                    provincia          = d['provincia']
                )
            db.session.commit()
        except Exception as e:
            logger.error(f"Error insertando localidades: {e}")