from ..models import MedicionClimatica, Estacion, Provincia
from typing import List, Optional
from datetime import datetime
from sqlalchemy import and_, select, func, or_
from app.extensions import db
from ..globals.row2dict_converter import row2dict_converter

class HistoricDAO:

    @staticmethod
    def obtener_id_provincia_por_str(
        provincia_id : str
    ) : 
        """
        Obtiene el id de la provincia almacenada en la BD sobre el código de provincia recibido por parámetro
        
        :param provincia_id: Código de la provincia
        :type provincia_id: str
        """
        try:
            query = (
                select(
                    Provincia.id
                ).where(
                    Provincia.codigo == provincia_id
                )
            )

            return db.session.execute(query).scalar()
        
        except Exception as e:
            print(f"Error obteniendo el id de la provincia: {e}")
            return []
    
    @staticmethod
    def define_horas_pico(
        estacion_id: Optional[int],
        provincia_id: Optional[int],
        fec_init: datetime,
        fec_fin: datetime
    ) :
        """Obtener los datos computados necesarios para componer las horas críticas de los DTO"""
        
        #Función anidada para obtener las horas críticas
        def obtener_horas_criticas(
            campo,
            asc = False
        ):
            """ Obtiene las horas críticas sobre valores de temperatura y humedad"""
            query = (
                select(
                    MedicionClimatica.timestamp,
                    MedicionClimatica.estacion_id
                )
                .where(
                    or_(
                        MedicionClimatica.estacion_id == estacion_id,
                        MedicionClimatica.provincia_id == provincia_id
                    ),
                    MedicionClimatica.timestamp.between(fec_init, fec_fin)
                )
                .order_by(getattr(MedicionClimatica, campo).asc() if asc else getattr(MedicionClimatica, campo).desc())
                .limit(1)
            )

            result = db.session.execute(query).first() 
            
            return result if result else None

        horas_pico = {
            "hora_temp_max": obtener_horas_criticas(
                "temperatura"
            ),
            "hora_temp_min": obtener_horas_criticas(
                "temperatura", 
                asc = True
            ),
            "hora_humedad_max": obtener_horas_criticas(
                "humedad"
            ),
            "hora_humedad_min": obtener_horas_criticas(
                "humedad", 
                asc = True
            )
        }

        return horas_pico
    
    @staticmethod
    def obtener_estaciones_usadas(
        provincia_id : int,
        fec_init : datetime,
        fec_fin : datetime
    ):
        try:
            query = (
                select(
                    Estacion.codigo
                )
                .join(MedicionClimatica)
                .where(
                    MedicionClimatica.timestamp.between(fec_init, fec_fin),
                    Estacion.provincia_id == provincia_id
                )
                .distinct()
            )
            estaciones_usadas = db.session.execute(query).scalars().all()
            
            return estaciones_usadas
        
        except Exception as e:
            print(f"Error computando las estaciones usadas: {e}")
            return []

    @staticmethod
    def define_computing_fechas(
        fec_init : datetime,
        fec_fin : datetime
    ):
        """
        Obtiene temperaturas de mediciones_climaticas dentro del rango de fechas pasado por parametros
        :param fec_init: Fecha inicial de consulta sobre datos
        :type fec_init: datetime
        :param fec_fin: Fecha final de consulta sobre datos
        :type fec_fin: datetime
        """
        try:
            query = (
                select(
                    MedicionClimatica.temperatura
                )
                .where(
                    MedicionClimatica.timestamp.between(fec_init, fec_fin)
                )
            )

            result = db.session.execute(query).all()

            if not result:
                return None
            
            return row2dict_converter(result)
        
        except Exception as e:
            print(f"Error consultando temperaturas sobre las fechas {fec_init} - {fec_fin} : {e}")
            return None

    @staticmethod
    def define_computing_general(
        estacion_id : Optional[int],
        provincia_id : Optional[int],
        fec_init : datetime,
        fec_fin : datetime
    ):
        """
        Obtener datos de la BD que coincidan con los parámetros de la función
        
        :param estacion_id: Identificador de la estacion
        :type estacion_id: Optional[int]
        :param provincia_id: Identificador de la provincia
        :type provincia_id: Optional[int]
        :param fec_init: Fecha de inicio de los datos
        :type fec_init: datetime
        :param fec_fin: Fecha de finalizacion de los datos
        :type fec_fin: datetime
        """
        try:
            query = (
                select(
                    MedicionClimatica.id
                )
                .where(
                    MedicionClimatica.timestamp.between(fec_init, fec_fin)
                )
            )

            result = db.session.execute(query).first()

            if not result:
                return None
            
            return result
        
        except Exception as e:
            print(f"Error computando los datos generales historicos: {e}")
            return []

    @staticmethod
    def define_computing_data_hora(
        estacion_id: Optional[int],
        provincia_id: Optional[int],
        fec_init: datetime,
        fec_fin: datetime
    ):
        """Obtiene los datos computados necesarios para cargar un DTO horario"""
        try:
            query = (
                select(
                    func.date_format(MedicionClimatica.timestamp, '%H:00:00').label('hora'),
                    func.avg(MedicionClimatica.temperatura).label('temp_media'),
                    func.avg(MedicionClimatica.humedad).label('humedad_media'),
                    func.avg(MedicionClimatica.vel_viento).label('vel_viento'),
                    func.sum(MedicionClimatica.precipitacion).label('precipitacion'),
                    Estacion.codigo.label('estacion'),
                    MedicionClimatica.timestamp.label('fecha')
                )
                .where(
                    MedicionClimatica.timestamp.between(fec_init, fec_fin)
                )
                .join(Estacion, MedicionClimatica.estacion)
                .group_by(
                    "hora"
                )
                .order_by(
                    "hora"
                )
            )

            if estacion_id:
                queryGlobal = queryGlobal.where(MedicionClimatica.estacion_id == estacion_id)
            elif provincia_id:
                queryGlobal = queryGlobal.where(Estacion.provincia_id == provincia_id)
                estaciones_usadas = HistoricDAO.obtener_estaciones_usadas(
                    provincia_id = provincia_id,
                    fec_init = fec_init,
                    fec_fin = fec_fin
                )

            valores_globales = db.session.execute(query).all()
            valores_horarios = row2dict_converter(valores_globales)

            return {
                "valores_diarios": valores_horarios,
                "estaciones_usadas":  estaciones_usadas if estacion_id is None else None
            }
        
        except Exception as e:
            print(f"Error computando los datos horarios: {e}")
            return []

    @staticmethod
    def define_computing_data_dia(
        estacion_id: Optional[int],
        provincia_id: Optional[int],
        fec_init: datetime,
        fec_fin: datetime
    ):
        """Obtiene los datos computados necesarios para cargar un DTO diario"""
        try:
            print(f"{fec_init} - {fec_fin}")
            diccionario_datos = {}

            fecha_truncada = func.date(MedicionClimatica.timestamp).label("fecha")

            columnas = [
                func.avg(MedicionClimatica.temperatura).label('temp_media'),
                func.max(MedicionClimatica.temperatura).label('temp_max'),
                func.min(MedicionClimatica.temperatura).label('temp_min'),
                func.avg(MedicionClimatica.humedad).label("humedad_media"),
                func.max(MedicionClimatica.humedad).label('humedad_max'),
                func.min(MedicionClimatica.humedad).label('humedad_min'),
                func.avg(MedicionClimatica.vel_viento).label("vel_viento"),
                func.max(MedicionClimatica.vel_viento).label("vel_viento_max"),
                func.sum(MedicionClimatica.precipitacion).label("precipitacion"),
                func.avg(MedicionClimatica.etp_mon).label("etp_mon"),
                func.avg(MedicionClimatica.pep_mon).label("pep_mon"),
                Provincia.codigo.label('provincia'),
                fecha_truncada
            ]

            if estacion_id:
                columnas.append(                
                    Estacion.codigo.label('estacion') # Si trabajo en el ambito provincial, no voy a mostrar que los datos se han obtenido de una sola estacion
                )
            
            queryGlobal = (
                select(
                    *columnas
                )
                .where(
                    MedicionClimatica.timestamp.between(fec_init, fec_fin)
                )
                .join(Estacion, MedicionClimatica.estacion)
            )

            if provincia_id:
                queryGlobal = queryGlobal.join(Provincia, MedicionClimatica.provincia)

            if estacion_id:
                queryGlobal = queryGlobal.where(MedicionClimatica.estacion_id == estacion_id)
            elif provincia_id:
                print(f"Provincia id : {provincia_id}")
                queryGlobal = queryGlobal.where(Estacion.provincia_id == provincia_id)
                estaciones_usadas = HistoricDAO.obtener_estaciones_usadas(
                    provincia_id = provincia_id,
                    fec_init = fec_init,
                    fec_fin = fec_fin
                )
                diccionario_datos["estaciones_usadas"] = estaciones_usadas
                print(diccionario_datos["estaciones_usadas"])
            
            queryGlobal = (
                queryGlobal
                .group_by(fecha_truncada)
                .order_by(fecha_truncada)
            )

            valores_globales = db.session.execute(queryGlobal).all()
            print(f"Valores globales : {valores_globales}")
            valores_diarios = row2dict_converter(valores_globales)

            diccionario_datos["valores_diarios"] = valores_diarios
            diccionario_datos["horas_pico"] = HistoricDAO.define_horas_pico(
                    estacion_id,
                    provincia_id,
                    fec_init,
                    fec_fin
                )
            return diccionario_datos
            
        except Exception as e:
            print(f"Error computando los datos diarios: {e}")
            return []
        
    @staticmethod
    def define_computing_data_semana(
        estacion_id: Optional[int],
        provincia_id: Optional[int],
        fec_init: datetime,
        fec_fin: datetime
    ):
        """Obtiene los datos computados necesarios para cargar un DTO semanal"""
        try:
            diccionario_datos = {}
            anio_truncado = func.date_format(MedicionClimatica.timestamp, '%Y').label('anio')

            queryGlobal = (
                select(
                    anio_truncado,
                    MedicionClimatica.semana.label('semana'),
                    func.avg(MedicionClimatica.temperatura).label('temp_media'),
                    func.max(MedicionClimatica.temperatura).label('temp_max'),
                    func.min(MedicionClimatica.temperatura).label('temp_min'),
                    func.avg(MedicionClimatica.humedad).label('humedad_media'),
                    func.max(MedicionClimatica.humedad).label('humedad_max'),
                    func.min(MedicionClimatica.humedad).label('humedad_min'),
                    func.avg(MedicionClimatica.vel_viento).label('vel_viento'),
                    func.max(MedicionClimatica.vel_viento).label('vel_viento_max'),
                    func.sum(MedicionClimatica.precipitacion).label('precipitacion'),
                    func.avg(MedicionClimatica.etp_mon).label('etp_mon'),
                    func.avg(MedicionClimatica.pep_mon).label('pep_mon'),
                    Estacion.codigo.label('estacion') if estacion_id is not None else None,
                    Provincia.codigo.label('provincia')
                )
                .where(
                    MedicionClimatica.timestamp.between(fec_init, fec_fin)
                )
                .join(Estacion, MedicionClimatica.estacion)
                .join(Provincia, MedicionClimatica.provincia)
            )

            if estacion_id:
                queryGlobal = queryGlobal.where(MedicionClimatica.estacion_id == estacion_id)
            elif provincia_id:
                queryGlobal = queryGlobal.where(Estacion.provincia_id == provincia_id)
                estaciones_usadas = HistoricDAO.obtener_estaciones_usadas(
                    provincia_id = provincia_id,
                    fec_init = fec_init,
                    fec_fin = fec_fin
                )
                diccionario_datos["estaciones_usadas"] = estaciones_usadas

            queryGlobal = (
                queryGlobal
                .group_by(anio_truncado, MedicionClimatica.semana)
                .order_by(anio_truncado, MedicionClimatica.semana)
            )

            valores_globales = db.session.execute(queryGlobal).all()
            valores_semanales = row2dict_converter(valores_globales)

            diccionario_datos["valores_diarios"] = valores_semanales
            diccionario_datos["horas_pico"] = HistoricDAO.define_horas_pico(
                    estacion_id,
                    provincia_id,
                    fec_init,
                    fec_fin
                )               

            return diccionario_datos
        
        except Exception as e:
            print(f"Erro computando los datos semanales: {e}")
            return []

    @staticmethod
    def define_compution_data_mes(
        estacion_id: Optional[int],
        provincia_id: Optional[int],
        fec_init: datetime,
        fec_fin: datetime
    ):
        """Obtiene los datos computados necesarios para cargar un DTO mensual"""
        try:
            diccionario_datos = {}

            queryGlobal = (
                select (
                    func.date_format(MedicionClimatica.timestamp, '%Y').label('anio'),
                    func.data_format(MedicionClimatica.timestamp, '%m').label('mes'),
                    func.avg(MedicionClimatica.temperatura).label('temp_media'),
                    func.max(MedicionClimatica.temperatura).label('temp_max'),
                    func.min(MedicionClimatica.temperatura).label('temp_min'),
                    func.avg(MedicionClimatica.humedad).label('humedad_media'),
                    func.max(MedicionClimatica.humedad).label('humedad_max'),
                    func.min(MedicionClimatica.humedad).label('humedad_min'),
                    func.avg(MedicionClimatica.vel_viento).label('vel_viento'),
                    func.sum(MedicionClimatica.precipitacion).label('precipitacion'),
                    func.avg(MedicionClimatica.etp_mon).label('etp_mon'),
                    func.avg(MedicionClimatica.pep_mon).label('pep_mon'),
                    Estacion.codigo.label('estacion') if estacion_id is not None else None,
                    Provincia.codigo.label('provincia')
                )
                .where(
                    MedicionClimatica.timestamp.between(fec_init, fec_fin)
                )
                .join(Estacion, MedicionClimatica.estacion)
                .join(Provincia, MedicionClimatica.provincia)
            )
            
            if estacion_id:
                queryGlobal = queryGlobal.where(MedicionClimatica.estacion_id == estacion_id)
            elif provincia_id:
                queryGlobal = queryGlobal.where(Estacion.provincia_id == provincia_id)
                estaciones_usadas = HistoricDAO.obtener_estaciones_usadas(
                    provincia_id = provincia_id,
                    fec_init = fec_init,
                    fec_fin = fec_fin
                )
                diccionario_datos["estaciones_usadas"] = estaciones_usadas

            queryGlobal = (
                queryGlobal
                .group_by(MedicionClimatica.mes, MedicionClimatica.anio)
                .order_by(MedicionClimatica.mes, MedicionClimatica.anio)
            )

            valores_globales = db.session.execute(queryGlobal).all()
            valores_meses = row2dict_converter(valores_globales)
            
            diccionario_datos["valores_diarios"] = valores_meses
            diccionario_datos["horas_pico"] = HistoricDAO.define_horas_pico(
                    estacion_id,
                    provincia_id,
                    fec_init,
                    fec_fin
                )

            return diccionario_datos
        
        except Exception as e:
            print(f"Error computando los datos mensuales: {e}")
            return []
