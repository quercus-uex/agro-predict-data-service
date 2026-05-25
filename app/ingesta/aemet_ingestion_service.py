from app.extensions import db
from typing import Optional
from datetime import datetime
from ..ingesta.ingesta_dao import IngestaDAO
from ..external_services.aemet_service import AemetService
import logging

logger = logging.getLogger(__name__)


class AemetIngestionService:

    @staticmethod
    def ingest_aemet_data(tipo_zona, tipo_prediccion, codigo_zona: Optional[str], fecha):
        try:
            IngestaDAO.actualizar_estado(
                status      = 'LOADING',
                dataset     = 'actual_futuro',
                tipo        = tipo_prediccion.value,
                year        = fecha.year,
                month       = fecha.month,
                day         = fecha.day,
                zona        = tipo_zona.value,
                finish_time = None,
                error       = None,
                codigo      = codigo_zona if codigo_zona else "",
            )

            data_predicciones, data_localidades = AemetService.get_aemet_data(
                tipo_prediccion = tipo_prediccion,
                tipo_zona       = tipo_zona,
                codigo_zona     = codigo_zona,
                fecha           = fecha
            )

            prediccion_insertada = IngestaDAO.crear_predicciones(
                codigo_zona = codigo_zona,
                data        = data_predicciones
            )

            for localidad, datos in data_localidades.get('temperaturas_localidades', {}).items():
                IngestaDAO.crear_localidades_climaticas(
                    prediccion_id = prediccion_insertada.id,
                    loc           = localidad,
                    temp_max      = datos.get('temp_max'),
                    temp_min      = datos.get('temp_min')
                )

            db.session.commit()

            IngestaDAO.actualizar_estado(
                status      = 'READY',
                dataset     = 'actual_futuro',
                tipo        = tipo_prediccion.value,
                year        = fecha.year,
                month       = fecha.month,
                day         = fecha.day,
                finish_time = datetime.now(),
                zona        = tipo_zona.value,
                error       = None,
                codigo      = codigo_zona if codigo_zona else "",
            )
            db.session.commit()

        except Exception as e:
            IngestaDAO.actualizar_estado(
                status      = 'FAILED',
                dataset     = 'actual_futuro',
                tipo        = tipo_prediccion.value,
                year        = fecha.year,
                month       = fecha.month,
                day         = fecha.day,
                finish_time = datetime.now(),
                zona        = tipo_zona.value,
                error       = str(e),
                codigo      = codigo_zona if codigo_zona else "",
            )