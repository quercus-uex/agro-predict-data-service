from ..models import MedicionClimatica, Estacion
from typing import List, Optional
from datetime import datetime
from sqlalchemy import and_, select, func, or_
from app import db
from ..globals.row2dict_converter import row2dict_converter, row2dict_list

class HistoricDAO:

    @staticmethod
    def find_historic_metrics_from_estacion_id(
        estacion_id : int, 
        fec_init : datetime, 
        fec_fin: datetime
    ) -> Optional[List[MedicionClimatica]]: 
        """Obtener datos de mediciones climaticas sobre datos historicos de una estacion"""
        try:
            query = (
                select(MedicionClimatica)
                .where(
                    and_(
                        MedicionClimatica.estacion_id == estacion_id,
                        MedicionClimatica.timestamp > fec_init,
                        MedicionClimatica.timestamp > fec_fin 
                    )
                )
                .order_by(MedicionClimatica.timestamp)
            )

            result = db.session.execute(query)
            return result.scalars().all() # Devuelve una lista de objectos de tipo MedicionClimatica
        
        except Exception as e:
            print(f"Error buscando la estacion {estacion_id} : {e}")
            return []
        
    @staticmethod
    def find_historic_metrics_from_provincia_id(
        provincia_id : int,
        fec_init: datetime,
        fec_fin: datetime
    ) -> Optional[List[MedicionClimatica]]:
        """Obtiene mediciones climáticas sobre datos históricos de una provincia"""
        try:
            query = (
                select(MedicionClimatica)
                .where(
                    and_(
                        MedicionClimatica.provincia_id == provincia_id,
                        MedicionClimatica.timestamp > fec_init,
                        MedicionClimatica.timestamp > fec_fin
                    )
                )
                .order_by(MedicionClimatica.timestamp)
            )

            result = db.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            print(f"Error buscando la provincia {provincia_id} : {e}")
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
                    MedicionClimatica.timestamp
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
                    MedicionClimatica.estacion.label('estacion'),
                    MedicionClimatica.timestamp.label('fecha')
                )
                .where(
                    or_(
                        MedicionClimatica.estacion_id == estacion_id,
                        MedicionClimatica.provincia_id == provincia_id
                    ),
                    MedicionClimatica.timestamp.between(fec_init, fec_fin)
                )
                .group_by(
                    "hora"
                )
                .order_by(
                    "hora"
                )
            )

            valores_globales = db.session.execute(query).all()

            return {
                "valores_diarios": [dict(row._mapping) for row in valores_globales]
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
            fecha_truncada = func.date(MedicionClimatica.timestamp).label("fecha")
            
            queryGlobal = (
                select(
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
                    MedicionClimatica.estacion_id.label('estacion'),
                    fecha_truncada
                )
                .where(
                    MedicionClimatica.timestamp.between(fec_init, fec_fin)
                )
            )

            print(f"Dia de comienzo y fin: {fec_init} - {fec_fin}")

            if estacion_id:
                queryGlobal = queryGlobal.where(MedicionClimatica.estacion_id == estacion_id)
            elif provincia_id:
                queryGlobal = queryGlobal.where(Estacion.provincia_id == provincia_id)
            
            queryGlobal = (
                queryGlobal
                .group_by(fecha_truncada)
                .order_by(fecha_truncada)
            )

            valores_globales = db.session.execute(queryGlobal).all()
            print(f"Valores globales dia: {valores_globales}", flush = True)
 
            valores_diarios = row2dict_converter(valores_globales)

            return {
                "valores_diarios": valores_diarios,
                "horas_pico": HistoricDAO.define_horas_pico(
                    estacion_id,
                    provincia_id,
                    fec_init,
                    fec_fin
                )
            }
            
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
                    func.avg(MedicionClimatica.vel_viento).label('vel_viento'),
                    func.max(MedicionClimatica.vel_viento).label('vel_viento_max'),
                    func.sum(MedicionClimatica.precipitacion).label('precipitacion'),
                    func.avg(MedicionClimatica.etp_mon).label('etp_mon'),
                    func.avg(MedicionClimatica.pep_mon).label('pep_mon'),
                    MedicionClimatica.estacion_id.label('estacion')
                )
                .where(
                    MedicionClimatica.timestamp.between(fec_init, fec_fin)
                )
            )

            if estacion_id:
                queryGlobal = queryGlobal.where(MedicionClimatica.estacion_id == estacion_id)
            elif provincia_id:
                queryGlobal = queryGlobal.where(Estacion.provincia_id == provincia_id)

            queryGlobal = (
                queryGlobal
                .group_by(anio_truncado, MedicionClimatica.semana)
                .order_by(anio_truncado, MedicionClimatica.semana)
            )

            valores_globales = db.session.execute(queryGlobal).all()
            valores_semanales = row2dict_converter(valores_globales)

            return {
                "valores_diarios": valores_semanales,
                "horas_pico": HistoricDAO.define_horas_pico(
                    estacion_id,
                    provincia_id,
                    fec_init,
                    fec_fin
                )
            }
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
                    MedicionClimatica.estacion.label('estacion')
                )
                .where(
                    MedicionClimatica.timestamp.between(fec_init, fec_fin)
                )
            )
            
            if estacion_id:
                queryGlobal = queryGlobal.where(MedicionClimatica.estacion_id == estacion_id)
            elif provincia_id:
                queryGlobal = queryGlobal.where(Estacion.provincia_id == provincia_id)

            queryGlobal = (
                queryGlobal
                .group_by(MedicionClimatica.mes, MedicionClimatica.anio)
                .order_by(MedicionClimatica.mes, MedicionClimatica.anio)
            )

            valores_globales = db.session.execute(queryGlobal).all()
            valores_meses = row2dict_converter(valores_globales)
            
            return {
                "valores_diarios": valores_meses,
                "horas_pico": HistoricDAO.define_horas_pico(
                    estacion_id,
                    provincia_id,
                    fec_init,
                    fec_fin
                )
            }
        except Exception as e:
            print(f"Error computando los datos mensuales: {e}")
            return []
