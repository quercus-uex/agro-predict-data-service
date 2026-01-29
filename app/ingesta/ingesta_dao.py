from sqlalchemy import and_, select, inspect, update
from app.extensions import db
from ..models import IngestaStatus
from datetime import datetime
from typing import Optional

class IngestaDAO:
    @staticmethod
    def obtener_estado(
        dataset = str,
        tipo = str,
        year = int,
        month = int,
        day = int
    ):
        try:
            query = (
                select(
                    IngestaStatus
                )
                .where(
                    and_(
                        IngestaStatus.dataset == dataset,
                        IngestaStatus.tipo == tipo,
                        IngestaStatus.year == year,
                        IngestaStatus.month == month,
                        IngestaStatus.day == day
                    )
                )
            )

            result = (
                db.session.execute(query)
                .scalar()
                .unique()
            )

            status = {
                s.key : getattr(result, s.key)
                for s in inspect(result).mapper.column_attrs
            }

            return status
        
        except Exception as e:
            print(f"Error leyendo datos de estados de ingesta: {e}")
            return None
    
    @staticmethod
    def create(
        status : str,
        dataset : str,
        tipo : str,
        year : int,
        month : int,
        day : int,
        started_at : datetime,
        finished_at : Optional[datetime],
        error_message : Optional[str]
    ):
        try:
            ingesta = IngestaStatus(
                dataset = dataset,
                tipo = tipo,
                year = year,
                month = month,
                day = day,
                status = status,
                started_at = started_at,
                finished_at = finished_at if finished_at else None,
                error_message = error_message if error_message else None
            )

            db.session.add(ingesta)
            db.session.commit()

        except Exception as e:
            print(f"Error creando un nuevo estado de ingesta : {e}")
            return None
        
    @staticmethod
    def actualizar_estado(
        status : str,
        dataset = str,
        tipo = str,
        year = int,
        month = int,
        day = int,
        error = Optional[str]
    ):
        query = (
            update(
                IngestaStatus
            )
            .where(
                and_(
                    IngestaStatus.dataset == dataset,
                    IngestaStatus.tipo == tipo,
                    IngestaStatus.year == year,
                    IngestaStatus.month == month,
                    IngestaStatus.day == day
                )
            )
            .values(
                status = status,
                error_message = error if error else None
            )
        )

        db.session.execute(query)