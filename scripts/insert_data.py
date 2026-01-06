import schedule
import time
from datetime import date
from app.external_services.ingesta_service import IngestionService
from app.historicos.historico_dto import TipoHistorico

def job():
    """Carga de datos en la base de datos con los datos SiAR"""
    # Carga de estaciones
    IngestionService.ingest_info(
        estaciones = True
    )

    # Carga de provincias
    IngestionService.ingest_info(
        estaciones = False
    )

    # Carga de datos diarios sobre Cáceres
    IngestionService.ingest_data(
        codigo_estacion_id = None,
        codigo_provincia_id = "CC",
        tipo = TipoHistorico.DIA,
        fec_init = date(2024,01,01),
        fec_fin = date(2024,01,01)
    )