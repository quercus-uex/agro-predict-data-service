import schedule
import time
from datetime import date

import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.extensions import db

from app.ingesta.ingesta_service import IngestionService

from app.models import *

def eliminar_datos_tablas(app):
    # Elimino datos de tablas (para desarrollo)
    db.session.execute(db.text('SET FOREIGN_KEY_CHECKS = 0'))
        
    # Eliminar todas en cualquier orden
    for modelo in [MedicionClimatica, Estacion, 
                    Plaga, CalendarioPlaga, Provincia, CCAA]:
        count = modelo.query.delete()
        print(f"  - {modelo.__tablename__}: {count} registros eliminados")
    
    db.session.execute(db.text('SET FOREIGN_KEY_CHECKS = 1'))
    db.session.commit()

    print("Eliminado datos de las tablas en la base de datos")


def job(app):
    """Carga de datos en la base de datos con los datos SiAR"""
    # Carga de estaciones
    IngestionService.ingest_info(
        estaciones = True
    )

    # Carga de provincias
    IngestionService.ingest_info(
        estaciones = True
    )

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
    """IngestionService.ingest_aemet_data(
        tipo_zona = TipoZona.CCAA,
        tipo_prediccion = TipoPrediccion.TOMORROW,
        codigo_zona = "ext",
        fecha = date(2026,1,17)
    )"""

    # Cargar datos de ITACyL
    IngestionService.ingest_itacyl_data(
        cultivo = 1,
        grupo = "cereales"
    )
    
    # Cargar datos de Localidades
    IngestionService.ingest_localidad_data()