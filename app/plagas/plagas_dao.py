from ..models import Plaga, CalendarioPlaga
from sqlalchemy import select, and_
from app import db
from ..globals.row2dict_converter import row2dict_converter
from typing import Optional

class PlagasDAO:

    @staticmethod
    def _get_plagas():
        try:
            # Query que obtiene todas las plagas de la bd
            query_plagas = (
                select(
                    Plaga
                )
                .order_by(
                    Plaga.public_id.desc()
                )
            )

            resultado_plagas = db.session.execute(query_plagas)

            return resultado_plagas.scalars().all()
        
        except Exception as e:
            print(f"Error leyendo datos de la bd sobre plagas: {e}")
            return None

    @staticmethod
    def _get_calendario_plagas():
        try:

            # Query que obtiene el calendario de la plaga asociada
            query_calendario_plagas = (
                select(
                    CalendarioPlaga
                )
                .join(Plaga)
                .where(
                    CalendarioPlaga.plaga_id == Plaga.public_id
                )
                .order_by(
                    CalendarioPlaga.plaga_id.desc()
                )
            )

            result_calendario = db.session.execute(query_calendario_plagas)

            return result_calendario.scalars().all()
        
        except Exception as e:
            print(f"Error leyendo datos del calendario de plagas: {e}")
            return None
