from app.extensions import db
from datetime import date
from ..ingesta.ingesta_dao import IngestaDAO
from ..external_services.dtagro_service import DTAgroService
import logging

logger = logging.getLogger(__name__)


class SensorIngestionService:

    @staticmethod
    def ingesta_sensores_data(euis: list[str], fecha_inicio: list[date] | date, fecha_fin: date, nombre_dtagro : str, nombre_predictor : str):
        try:
            print(f"DEBUG: fec_ini fec_fin ingest: {fecha_inicio} - {fecha_fin}")
            datos = DTAgroService.get_dtagro_datos(
                euis             = euis,
                fecha_inicio     = fecha_inicio,
                fecha_fin        = fecha_fin,
                nombre_dtagro    = nombre_dtagro,
                nombre_predictor = nombre_predictor
            )

            for medicion in datos:
                if medicion is None:
                    continue
                for resultado in medicion['resultados']:
                    IngestaDAO.crear_datos_sensores(
                        eui                = medicion['eui'],
                        timestamp          = resultado['timestamp'],
                        campo              = nombre_predictor,
                        valor              = resultado[f'{nombre_predictor}'],
                    )

            db.session.commit()
        except Exception as e:
            logger.error(f"Error cargando datos de sensores: {e}")