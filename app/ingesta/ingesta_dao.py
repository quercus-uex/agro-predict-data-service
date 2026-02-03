from sqlalchemy import and_, select, inspect, update, delete
from app.extensions import db
from ..models import IngestaStatus
from datetime import datetime
from typing import Optional

class IngestaDAO:
    @staticmethod
    def obtener_estado(
        dataset : str,
        tipo : str,
        year : int,
        month : int,
        day : int,
        zona : str
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
                        IngestaStatus.day == day,
                        IngestaStatus.zona == zona
                    )
                )
            )

            result = db.session.execute(query).scalar_one_or_none()

            print(f"Resultado : {result}")

            if not result:
                return None

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
        zona : str,
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
                zona = zona,
                started_at = started_at,
                finished_at = finished_at if finished_at else None,
                error_message = error_message if error_message else None
            )

            db.session.add(ingesta)
            db.session.commit()

        except Exception as e:
            print(f"Error creando un nuevo estado de ingesta : {e}")
            db.session.rollback()
            return None
        
    @staticmethod
    def actualizar_estado(
        status : str,
        dataset : str,
        tipo : str,
        year : int,
        month : int,
        day : int,
        zona : str,
        finish_time : Optional[datetime],
        error : Optional[str]
    ):
        try:
            print(f"Parametros {status}-{dataset}-{tipo}-{year}-{month}-{day}-{zona}")
            print("actualizo el estado", flush = True)
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
                        IngestaStatus.day == day,
                        IngestaStatus.zona == zona
                    )
                )
                .values(
                    status = status,
                    error_message = error if error else None,
                    finished_at = finish_time if finish_time else None
                )
            )

            result = db.session.execute(query)

            if result.rowcount == 0:
                print("No se actualizó ninguna fila (no encontrada)")

            db.session.commit()
            
        except Exception as e:
            print(f"Algo fue mal actualizando el estado de ingesta: {e}")
            db.session.rollback()
            return None
        
    @staticmethod
    def delete_estado(
        status : str,
        dataset : str,
        tipo : str,
        year : int,
        month : int,
        day : int,
        zona : str,
        error : Optional[str]
    ):
        try:
            query = (
                delete(
                    IngestaStatus
                )
                .where(
                    and_(
                        IngestaStatus.dataset == dataset,
                        IngestaStatus.tipo == tipo,
                        IngestaStatus.year == year,
                        IngestaStatus.month == month,
                        IngestaStatus.day == day,
                        IngestaStatus.zona == zona
                    )
                )
            )

            db.session.execute(query)
        except Exception as e:
            print(f"Algo fue mal eliminando el estado de ingesta: {e}")
            db.session.rollback()
            return None