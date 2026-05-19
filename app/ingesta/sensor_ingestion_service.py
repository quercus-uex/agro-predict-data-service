from app.extensions import db
from datetime import date
from ..ingesta.ingesta_dao import IngestaDAO
from ..external_services.dtagro_service import DTAgroService
import logging

logger = logging.getLogger(__name__)


class SensorIngestionService:

    @staticmethod
    def ingesta_sensores_data(euis: list[str], fecha_inicio: date, fecha_fin: date):
        try:
            datos = DTAgroService.get_dtagro_datos(
                euis         = euis,
                fecha_inicio = fecha_inicio,
                fecha_fin    = fecha_fin
            )

            for medicion in datos:
                if medicion is None:
                    continue
                for resultado in medicion['resultados']:
                    IngestaDAO.crear_datos_sensores(
                        eui                = medicion['eui'],
                        humedad_foliar     = resultado['humedad_foliar'],
                        temperatura_sensor = resultado['temp_DS18B20'],
                        temperatura_hojas  = resultado['temperatura_hoja'],
                        timestamp          = resultado['timestamp'],
                        temperatura_suelo  = resultado['temperatura_suelo'],
                        humedad_suelo      = resultado['humedad_suelo'],
                        temperatura_minima = resultado['temperatura_minima'],
                        temperatura_maxima = resultado['temperatura_maxima']
                    )

            db.session.commit()
        except Exception as e:
            logger.error(f"Error cargando datos de sensores: {e}")