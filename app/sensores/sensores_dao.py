from sqlalchemy import select, and_, inspect
from ..models import Sensores
from datetime import date, datetime, time
from app.extensions import db
from ..globals.row2dict_converter import row2dict_converter


class SensoresDAO():
    @staticmethod
    def consultar_datos_sensores(
        eui : str,
        fecha_inicio : date,
        fecha_fin : date
    ):
        try:
            query = (
                select(
                    Sensores
                )
                .where(
                    and_(
                        Sensores.eui == eui,
                        Sensores.timestamp.between(datetime.combine(fecha_inicio, time.min), datetime.combine(fecha_fin, time.min)) # Conversión de date a datetime
                    )
                )
            )

            resultado = db.session.execute(query).scalars().all()

            if not resultado:
                return None
            
            return [
                {
                    s.key : getattr(p, s.key)
                    for s in inspect(p).mapper.column_attrs
                }
                for p in resultado
            ]

        except Exception as e:
            print(f"Error consultando los datos de sensores por eui - {eui} : {e}")
            return None
