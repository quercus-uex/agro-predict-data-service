from models import Estacion, MedicionClimatica
from typing import List, Optional
from datetime import date
from sqlalchemy import and_
from app import db

class HistoricDAO:

    @staticmethod
    def find_historic_metrics_from_estacion_id(
        estacion_id : int, 
        fec_init : date, 
        fec_fin: date
    ) -> Optional[List[MedicionClimatica]]: 
        """Obtener datos de mediciones climaticas sobre datos historicos de una estacion"""
        try:
            query = (
                db.select(MedicionClimatica)
                .where(
                    and_(
                        MedicionClimatica.estacion_id == estacion_id,
                        MedicionClimatica.timestamp > fec_init,
                        MedicionClimatica.timestamp > fec_fin 
                    )
                )
                .order_by(MedicionClimatica.timestamp)
            )

            result = db.session.execute(query)
            return result.scalars().all() # Devuelve una lista de objectos de tipo MedicionClimatica
        
        except Exception as e:
            print(f"Error buscando la estacion {estacion_id} : {e}")
            return []
        
    @staticmethod
    def find_historic_metrics_from_provincia_id(
        provincia_id : int,
        fec_init: date,
        fec_fin: date
    ) -> Optional[List[MedicionClimatica]]:
        """Obtiene mediciones climáticas sobre datos históricos de una provincia"""
        try:
            query = (
                db.select(MedicionClimatica)
                .where(
                    and_(
                        MedicionClimatica.provincia_id == provincia_id,
                        MedicionClimatica.timestamp > fec_init,
                        MedicionClimatica.timestamp > fec_fin
                    )
                )
                .order_by(MedicionClimatica.timestamp)
            )

            result = db.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            print(f"Error buscando la provincia {provincia_id} : {e}")
            return []