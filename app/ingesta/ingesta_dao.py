from sqlalchemy import and_, select, inspect, update, delete
from app.extensions import db
from ..models import (
    IngestaStatus, 
    Localidades, 
    CCAA, 
    Predicciones, 
    Provincia, 
    LocalidadesClimaticas, 
    Sensores,
    MedicionesSensor
)
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
    
    @staticmethod
    def crear_datos_sensores(
        eui : str,
        humedad_foliar : float,
        temperatura_sensor : int,
        temperatura_hojas : float,
        timestamp : datetime
    ):
        """
        Crea un objeto de tipo Sensor sobre los valores 
        pasados por parámetro y lo inserta en la base de datos.

        :param eui: Identificador público del sensor
        :type eui: str
        :param humedad_foliar: Agua presente en la superficie de la hoja
        :type humedad_foliar: float
        :param temperatura_sensor: Temperatura que lee el sensor DS18B20
        :type temperatura_sensor: int,
        :param temperatura_hojas: Temperatura registrada por la hoja
        :type temperatura_hojas: float 
        """

        try:

            existe_sensor = db.session.query(Sensores).filter_by(
                eui = eui
            ).first()


            if not existe_sensor:
                sensor = Sensores(
                    eui = eui
                )
                # Lo incluyo antes del commit en la db para poder crear sus mediciones asociadas
                db.session.add(sensor)
                db.session.flush()
            else:
                sensor = existe_sensor

            # Comprobar que esa medicion a insertar no existe ya en la DB
            existe_medicion = db.session.query(MedicionesSensor.id).filter_by(
                timestamp = timestamp,
                sensor_id = sensor.id
            ).first()

            if existe_medicion:
                return
            
            mediciones = MedicionesSensor(
                humedad_foliar = humedad_foliar,
                temperatura_DS18B20 = temperatura_sensor,
                temperatura_hojas = temperatura_hojas,
                timestamp = timestamp,
                sensor_id = sensor.id
            )
            
            # Inserto la medicion
            db.session.add(mediciones)
            
        
        except Exception as e:
            print(f"Ha ocurrido un error intentando crear un nuevo dato de sensor : {e}")
            db.session.rollback()

    @staticmethod
    def crear_predicciones(
        codigo_zona : Optional[str],
        data
    ):
        try:
            """
            Crea un objeto de tipo Prediccion sobre los valores pasados y 
            lo inserta en la base de datos si no existe
            
            :param codigo_zona: Código de la zona sobre la que se hace la consulta
            :type codigo_zona: Optional[str]
            :param data: Datos obtenidos de la IA
            """
            ccaa : CCAA = CCAA.query.filter_by(codigo=codigo_zona).first()
            provincia : Provincia = Provincia.query.filter_by(codigo=codigo_zona).first()
            # Solo vamos a obtener un datos porque solo se realiza la peticion sobre un factor
            predicciones = Predicciones(
                ccaa_id = ccaa.id if ccaa else None,
                provincia_id = provincia.id if provincia else None,
                **data
            )

            existe = Predicciones.query.filter_by(
                tipo_prediccion = predicciones.tipo_prediccion,
                tipo_zona = predicciones.tipo_zona,
                codigo_zona = predicciones.codigo_zona,
                fecha_prediccion = predicciones.fecha_prediccion
            ).first()

            if existe:
                return existe
            
            #[✔]Tiene que ser los datos que reciba del broker
            db.session.add(predicciones)
            db.session.flush()
            return predicciones

        except Exception as e:
            print(f"Algo fue mal insertando predicciones a la BD : {e}")
            db.session.rollback()

    @staticmethod
    def crear_localidades_climaticas(
        prediccion_id : int,
        loc : str,
        temp_max : int,
        temp_min : int
    ) : 
        """
        Crea un objeto de tipo Localidad y lo inserta en la BD si no existe
        
        :param prediccion_id: Clave foránea que hace referencia a la prediccion
        :type prediccion_id: int
        :param loc: Nombre de la localidad a insertar
        :type loc: str
        :param temp_max: Temperatura maxima registrada por la localidad a insertar
        :type temp_max: int
        :param temp_min: Temperatura minima registrada por la localidad a insertar
        :type temp_min: int
        """
        try:
            print(f"localidad : {loc}")
            # Obtener la referencia a la localidad
            query = (
                select(
                    Localidades.id
                )
                .where(
                    Localidades.nombre_normalizado == loc.lower().replace(" ", "_") # Por si acaso
                )
            )

            localidad = db.session.execute(query).first()

            localidad_climatica = LocalidadesClimaticas(
                prediccion_id = prediccion_id,
                localidad_id = localidad[0],
                nombre = loc,
                temperatura_maxima = temp_max,
                temperatura_minima = temp_min
            )

            existe = db.session.query(LocalidadesClimaticas.id).filter_by(
                nombre = localidad_climatica.nombre,
                prediccion_id = prediccion_id
            ).first()

            if existe:
                print(f"Localidad : {localidad} ya existe")
                return existe
            
            db.session.add(localidad_climatica)

        except Exception as e:
            print(f"Algo fue mal insertando localidades_climaticas a la BD: {e}")
            db.session.rollback()

    @staticmethod
    def crear_localidades(
        nombre : str,
        nombre_normalizado : str,
        altitud : int,
        longitud : float,
        latitud : float,
        provincia : str
    ):
        try:
            # Obtengo la provincia relacionada con la localidad a insertar
            query = (
                select (
                    Provincia.id
                )
                .where(
                    Provincia.codigo == provincia
                )
            )

            provincia : Provincia = db.session.execute(query).fetchone()

            localidad = Localidades(
                nombre = nombre,
                nombre_normalizado = nombre_normalizado,
                altitud = altitud,
                latitud = latitud,
                longitud = longitud,
                provincia_id = provincia.id
            )

            db.session.add(localidad)
        
        except Exception as e:
            print(f"Algo ha salido mal insertando una nueva localidad en la BD : {e}")
            db.session.rollback()
