import schedule
import time
from datetime import date

import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import db

from app.external_services.ingesta_service import IngestionService
from app.historicos.historico_dto import TipoHistorico
from app.forecast.forecast_dto import TipoPrediccion, TipoZona

from app.models import *

def eliminar_datos_tablas(app):
    # Elimino datos de tablas (para desarrollo)
    db.session.execute(db.text('SET FOREIGN_KEY_CHECKS = 0'))
        
    # Eliminar todas en cualquier orden
    for modelo in [MedicionClimatica, Sector, Estacion, 
                    CalendarioCultivo, Cultivo, Provincia, CCAA]:
        count = modelo.query.delete()
        print(f"  - {modelo.__tablename__}: {count} registros eliminados")
    
    db.session.execute(db.text('SET FOREIGN_KEY_CHECKS = 1'))
    db.session.commit()

    print("Eliminado datos de las tablas en la base de datos")


def job(app):
    """Carga de datos en la base de datos con los datos SiAR"""
    # Carga de estaciones
    """IngestionService.ingest_info(
        estaciones = False
    )"""

    # Carga de provincias
    """IngestionService.ingest_info(
        estaciones = True
    )"""

    # Carga de datos diarios sobre Cáceres
    """IngestionService.ingest_data(
        codigo_estacion_id = None,
        codigo_provincia_id = "CC",
        tipo = TipoHistorico.DIA,
        fec_init = date(2024,1,8),
        fec_fin = date(2024,1,8)
    )"""

    # Carga masiva de datos
    """IngestionService.ingest_range(
        codigo_estacion_id = "CC01",
        codigo_provincia_id = None,
        tipo = TipoHistorico.HORA,
        fec_init = date(2024, 2, 2),
        fec_fin = date(2024, 2, 17)
    )"""

    # Cargar datos de AEMET
    ## Cargar datos predictivos de hoy para extremadura
    IngestionService.ingest_aemet_data(
        tipo_zona = TipoZona.CCAA,
        tipo_prediccion = TipoPrediccion.TOMORROW,
        codigo_zona = "ext",
        fecha = date(2026,1,17)
    )