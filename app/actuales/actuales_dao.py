from sqlalchemy import select, and_
from models import Predicciones, Provincia, CCAA
from app import db

class ActualesDAO:
    # Variable global que obtiene todas las columnas de la tabla Predicciones
    # menos el texto completo de AEMET almacenado
    EXCLUIR = {"texto_original", "provincia_id", "ccaa_id"}
    columnas = [
        c for c in Predicciones.__table__.columns
        if c.name not in ActualesDAO.EXCLUIR
    ]

    @staticmethod
    def define_computing_current_ccaa(
        ccaa_id : int
    ) : 
        """
        Obtiene los datos climáticos actuales sobre la comunidad autónoma pasada
        por parámetros.
        """
        try:
            query = (
                select(
                    *ActualesDAO.columnas,
                    CCAA.codigo.label('ccaa') if ccaa_id else None
                )
                .where(
                    and_(
                        Predicciones.ccaa_id == ccaa_id,
                        Predicciones.tipo_prediccion == "actual",
                        Predicciones.tipo_zona == "ccaa"
                    )
                )
                .join(CCAA, Predicciones.ccaa)
                .order_by(Predicciones.fecha_prediccion.desc())
                .limit(1)
            )

            result = db.session.execute(query).fetchone()
            return {
                "valores_actuales" : result,
                "servicios_usados" : "AEMET"
            }

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
            return {
                "valores_actuales" : result,
                "servicios_usados" : "AEMET"
            }
        
        except Exception as e:
            print(f"Error obteniendo datos actuales nacionales : {e}")
            return None

    @staticmethod
    def define_computing_current_provincia(
        provincia_id : int
    ) : 
        """
        Obtiene los datos climáticos actuales sobre la provincia especificada
        por parámetros        
        """
        try:

            query = (
                select(
                    *ActualesDAO.columnas,
                    Provincia.codigo.label("provincia") if provincia_id else None
                )
                .where(
                    and_(
                        Predicciones.provincia_id == provincia_id,
                        Predicciones.tipo_prediccion == "actual",
                        Predicciones.tipo_zona == "provincial"
                    )
                )
                .join(Provincia, Predicciones.provincia)
                .order_by(Predicciones.fecha_prediccion.desc())
                .limit(1)
            )

            result = db.session.execute(query).fetchone()
            return {
                "valores_actuales" : result,
                "servicios_usados" : "AEMET"
            }
        
        except Exception as e:
            print(f"Error obteniendo datos actuales sobre la provincia {provincia_id} : {e}")
            return None