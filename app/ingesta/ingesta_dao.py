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
    MedicionesSensor,
    TipoDato
)
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class IngestaDAO:

    # -------------------------------------------------------------------------
    # Helper privado
    # -------------------------------------------------------------------------

    @staticmethod
    def _filtro_ingesta(dataset: str, tipo: str, year: int, month: int, day: int, zona: str, codigo: str):
        """
        Devuelve la cláusula AND compartida por obtener_estado, actualizar_estado y delete_estado.
        Centraliza el filtro para evitar repetición y posibles inconsistencias.
        """
        return and_(
            IngestaStatus.dataset == dataset,
            IngestaStatus.tipo    == tipo,
            IngestaStatus.year    == year,
            IngestaStatus.month   == month,
            IngestaStatus.day     == day,
            IngestaStatus.zona    == zona,
            IngestaStatus.codigo  == codigo,
        )

    # -------------------------------------------------------------------------
    # CRUD de IngestaStatus
    # -------------------------------------------------------------------------

    @staticmethod
    def obtener_estado(
        dataset: str,
        tipo: str,
        year: int,
        month: int,
        day: int,
        zona: str,
        codigo: str,
        error: Optional[str]
    ):
        try:
            query = (
                select(IngestaStatus)
                .where(IngestaDAO._filtro_ingesta(dataset, tipo, year, month, day, zona, codigo))
            )

            if error:
                query = query.where(IngestaStatus.error_message == error)

            result = db.session.execute(query).scalar_one_or_none()
            if not result:
                return None

            return {
                s.key: getattr(result, s.key)
                for s in inspect(result).mapper.column_attrs
            }
        except Exception as e:
            logger.error(f"Error leyendo estado de ingesta: {e}")
            return None

    @staticmethod
    def create(
        status: str,
        dataset: str,
        tipo: str,
        year: int,
        month: int,
        day: int,
        zona: str,
        started_at: datetime,
        codigo: str,
        finished_at: Optional[datetime],
        error_message: Optional[str]
    ):
        try:
            ingesta = IngestaStatus(
                dataset       = dataset,
                tipo          = tipo,
                year          = year,
                month         = month,
                day           = day,
                status        = status,
                zona          = zona,
                started_at    = started_at,
                finished_at   = finished_at,
                error_message = error_message,
                codigo        = codigo
            )
            db.session.add(ingesta)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error creando estado de ingesta: {e}")
            db.session.rollback()

    @staticmethod
    def actualizar_estado(
        status: str,
        dataset: str,
        tipo: str,
        year: int,
        month: int,
        day: int,
        zona: str,
        codigo : str,
        finish_time: Optional[datetime],
        error: Optional[str]
    ):
        try:
            query = (
                update(IngestaStatus)
                .where(IngestaDAO._filtro_ingesta(dataset, tipo, year, month, day, zona, codigo))
                .values(
                    status        = status,
                    error_message = error,
                    finished_at   = finish_time
                )
            )
            result = db.session.execute(query)

            if result.rowcount == 0:
                logger.warning("actualizar_estado: no se encontró ninguna fila para actualizar")

            db.session.commit()
        except Exception as e:
            logger.error(f"Error actualizando estado de ingesta: {e}")
            db.session.rollback()

    @staticmethod
    def delete_estado(
        dataset: str,
        tipo: str,
        year: int,
        month: int,
        day: int,
        zona: str,
        codigo: str
    ):
        try:
            query = (
                delete(IngestaStatus)
                .where(IngestaDAO._filtro_ingesta(dataset, tipo, year, month, day, zona, codigo))
            )
            db.session.execute(query)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error eliminando estado de ingesta: {e}")
            db.session.rollback()

    # -------------------------------------------------------------------------
    # Inserción de datos de dominio
    # -------------------------------------------------------------------------

    @staticmethod
    def crear_datos_sensores(
        eui: str,
        humedad_foliar: float,
        temperatura_sensor: int,
        temperatura_hojas: float,
        timestamp: datetime,
        temperatura_suelo: float,
        humedad_suelo: float,
        temperatura_minima: float,
        temperatura_maxima: float
    ):
        """
        Inserta una medición de sensor, creando el sensor si no existe.

        :param eui: Identificador público del sensor
        :param humedad_foliar: Agua presente en la superficie de la hoja
        :param temperatura_sensor: Temperatura leída por el sensor DS18B20
        :param temperatura_hojas: Temperatura registrada por la hoja
        """
        try:
            existe_sensor = db.session.query(Sensores.id).filter(
                Sensores.dispositivo_id == eui
            ).first()

            if not existe_sensor:
                sensor = Sensores(eui=eui)
                db.session.add(sensor)
                db.session.flush()
            else:
                sensor = existe_sensor

            medicion = MedicionesSensor(
                humedad_foliar      = humedad_foliar,
                temperatura_DS18B20 = temperatura_sensor,
                temperatura_hojas   = temperatura_hojas,
                timestamp           = timestamp,
                temperatura_suelo   = temperatura_suelo,
                humedad_suelo       = humedad_suelo,
                temperatura_minima  = temperatura_minima,
                temperatura_maxima  = temperatura_maxima,
                sensor_id           = sensor.id
            )
            db.session.add(medicion)
        except Exception as e:
            logger.error(f"Error creando dato de sensor: {e}")
            db.session.rollback()

    @staticmethod
    def crear_predicciones(codigo_zona: Optional[str], data) -> Predicciones:
        """
        Crea una Prediccion si no existe ya para esa zona/fecha/tipo.

        :param codigo_zona: Código de la zona sobre la que se hace la consulta
        :param data: Datos obtenidos de la IA
        """
        try:
            ccaa     = CCAA.query.filter_by(codigo=codigo_zona).first()
            provincia = Provincia.query.filter_by(codigo=codigo_zona).first()

            prediccion = Predicciones(
                ccaa_id     = ccaa.id if ccaa else None,
                provincia_id = provincia.id if provincia else None,
                **data
            )

            existe = Predicciones.query.filter_by(
                tipo_prediccion  = prediccion.tipo_prediccion,
                tipo_zona        = prediccion.tipo_zona,
                codigo_zona      = prediccion.codigo_zona,
                fecha_prediccion = prediccion.fecha_prediccion
            ).first()

            if existe:
                return existe

            db.session.add(prediccion)
            db.session.flush()
            return prediccion
        except Exception as e:
            logger.error(f"Error insertando prediccion: {e}")
            db.session.rollback()

    @staticmethod
    def crear_localidades_climaticas(
        prediccion_id: int,
        loc: str,
        temp_max: int,
        temp_min: int
    ):
        """
        Crea una LocalidadClimatica si no existe ya para esa prediccion.

        :param prediccion_id: FK de la prediccion asociada
        :param loc: Nombre de la localidad
        :param temp_max: Temperatura máxima
        :param temp_min: Temperatura mínima
        """
        try:
            query = (
                select(Localidades.id)
                .where(Localidades.nombre_normalizado == loc.lower().replace(" ", "_"))
            )
            localidad = db.session.execute(query).first()

            localidad_climatica = LocalidadesClimaticas(
                prediccion_id    = prediccion_id,
                localidad_id     = localidad[0],
                nombre           = loc,
                temperatura_maxima = temp_max,
                temperatura_minima = temp_min
            )

            existe = db.session.query(LocalidadesClimaticas.id).filter_by(
                nombre        = localidad_climatica.nombre,
                prediccion_id = prediccion_id
            ).first()

            if existe:
                return existe

            db.session.add(localidad_climatica)
        except Exception as e:
            logger.error(f"Error insertando localidad climatica: {e}")
            db.session.rollback()

    @staticmethod
    def crear_localidades(
        nombre: str,
        nombre_normalizado: str,
        altitud: int,
        longitud: float,
        latitud: float,
        provincia: str
    ):
        try:
            query = select(Provincia.id).where(Provincia.codigo == provincia)
            prov  = db.session.execute(query).fetchone()

            localidad = Localidades(
                nombre             = nombre,
                nombre_normalizado = nombre_normalizado,
                altitud            = altitud,
                latitud            = latitud,
                longitud           = longitud,
                provincia_id       = prov.id
            )
            db.session.add(localidad)
        except Exception as e:
            logger.error(f"Error insertando localidad: {e}")
            db.session.rollback()

    @staticmethod
    def crear_tipos_datos(datos):
        try:
            for d in datos:
                existe = db.session.query(TipoDato).filter(
                    TipoDato.nombre == d['nombre']
                ).first()

                if existe:
                    continue

                db.session.add(TipoDato(
                    nombre     = d['nombre'],
                    descripcion = d.get('descripcion')
                ))
        except Exception as e:
            logger.error(f"Error insertando tipos de datos: {e}")
            db.session.rollback()