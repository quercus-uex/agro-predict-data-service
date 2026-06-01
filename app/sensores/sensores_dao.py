from sqlalchemy import select, and_, inspect
from ..models import Sensores, MedicionesSensor
from datetime import date, datetime, time
from app.extensions import db
from datetime import timedelta

class SensoresDAO():
    @staticmethod
    def existe_sensor(
        eui : str
    ) -> bool:
        try:
            if not eui:
                return False

            sensor = db.session.query(Sensores.dispositivo_id).filter_by(
                dispositivo_id = eui
            ).first()

            return sensor is not None

        except Exception as e:
            print(f"Error comprobando la existencia del sensor por eui - {eui} : {e}")
            return False
        
    @staticmethod
    def existe_sensor_data(
        eui : str,
        fec_init,
        fec_fin,
        nombre_prediccion : str
    ) -> bool:
        try:
            if not eui:
                return False
            
            sensor_registrado = db.session.query(Sensores.id).filter(
                Sensores.dispositivo_id == eui
            ).first()

            if not sensor_registrado:
                return False

            datos = db.session.query(MedicionesSensor).filter(
                MedicionesSensor.sensor_id == sensor_registrado.id,
                MedicionesSensor.timestamp.between(fec_init, fec_fin),
                MedicionesSensor.campo == nombre_prediccion
            ).order_by(MedicionesSensor.id.desc()).first()

            datos.timestamp = datetime.fromisoformat(datos.timestamp)
            if datos.timestamp.date() != (fec_fin - timedelta(days = 1)): # Si consulto hasta el dia 20 en DTAgro me devuelve hasta el 19, por lo que aunque los datos estén bien almacenados, 19 != 20, hace la petición igual
                print(f"DEBUG: datos timestampo {datos.timestamp.date()}")
                print("entro")
                return datos.timestamp.date() + timedelta(days = 1) # Para que la siguiente fecha inicial sea la siguiente a la fecha del último dato ya registrado

            return datos is not None

        except Exception as e:
            print(f"Error comprobando la existencia de datos del sensor por eui - {eui} : {e}")
            return False

    @staticmethod
    def consultar_datos_sensores(
        eui : str,
        fecha_inicio : date,
        fecha_fin : date
    ):
        try:
            query = (
                select(
                    MedicionesSensor
                )
                .join(Sensores, Sensores.id == MedicionesSensor.sensor_id)
                .where(
                    and_(
                        Sensores.dispositivo_id == eui,
                        MedicionesSensor.timestamp.between(datetime.combine(fecha_inicio, time.min), datetime.combine(fecha_fin, time.max)) # Conversión de date a datetime
                    )
                )
            )

            resultado = db.session.execute(query).all()

            if not resultado:
                return None
            
            return [
                {
                    **{s.key: getattr(row.MedicionesSensor, s.key) for s in inspect(row.MedicionesSensor).mapper.column_attrs}
                }
                for row in resultado
            ]

        except Exception as e:
            print(f"Error consultando los datos de sensores por eui - {eui} : {e}")
            return None
