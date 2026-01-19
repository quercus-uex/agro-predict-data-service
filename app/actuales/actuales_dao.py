from sqlalchemy import select, and_
from models import Predicciones
from app import db

class ActualesDAO:
    # Variable global que obtiene todas las columnas de la tabla Predicciones
    # menos el texto completo de AEMET almacenado
    columnas = [
        c for c in Predicciones.__table__.columns
        if c.name != "texto_original"
    ]

    @staticmethod
    def define_computing_current_ccaa(
        ccaa_id : str
    ) : 
        """
        Obtiene los datos climáticos actuales sobre la comunidad autónoma pasada
        por parámetros.
        """
        try:
            query = (
                select(
                    *ActualesDAO.columnas
                )
                .where(
                    and_(
                        Predicciones.ccaa_id == ccaa_id,
                        Predicciones.tipo_prediccion == "actual",
                        Predicciones.tipo_zona == "ccaa"
                    )
                )
                .order_by(Predicciones.fecha_prediccion.desc())
                .limit(1)
            )

            result = db.session.execute(query).fetchone()
            return result

        except Exception as e:
            print(f"Error obteniendo datos actuales de {ccaa_id} : {e}")
            return None
    
    @staticmethod
    def define_computing_current_nacional():
        """
        Obtiene los datos climáticos actuales nacionales.
        """
        try:
            query = (
                select(
                    *ActualesDAO.columnas
                )
                .where(
                    and_(
                        Predicciones.tipo_prediccion == "actual",
                        Predicciones.tipo_zona == "nacional"
                    )
                )
                .order_by(Predicciones.fecha_prediccion.desc())
                .limit(1)
            )

            result = db.session.execute(query).fetchone()
            return result
        
        except Exception as e:
            print(f"Error obteniendo datos actuales nacionales : {e}")
            return None

    @staticmethod
    def define_computing_current_provincia(
        provincia_id : str
    ) : 
        """
        Obtiene los datos climáticos actuales sobre la provincia especificada
        por parámetros        
        """
        try:

            query = (
                select(
                    *ActualesDAO.columnas
                )
                .where(
                    and_(
                        Predicciones.provincia_id == provincia_id,
                        Predicciones.tipo_prediccion == "actual",
                        Predicciones.tipo_zona == "provincial"
                    )
                )
                .order_by(Predicciones.fecha_prediccion.desc())
                .limit(1)
            )

            result = db.session.execute(query).fetchone()
            return result
        
        except Exception as e:
            print(f"Error obteniendo datos actuales sobre la provincia {provincia_id} : {e}")
            return None