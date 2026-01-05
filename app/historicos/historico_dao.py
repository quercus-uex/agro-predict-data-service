from models import MedicionClimatica
from typing import List, Optional
from datetime import datetime
from sqlalchemy import and_, select, func, or_
from app import db

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
                    func.date_trunc('hour', MedicionClimatica.timestamp).label('hora'),
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

            result = db.session.execute(query).first() if result else None

        horas_pico = {
            "hora_temp_max": HistoricDAO.obtener_horas_criticas(
                "temperatura"
            ),
            "hora_temp_min": HistoricDAO.obtener_horas_criticas(
                "temperatura", 
                asc = True
            ),
            "hora_humedad_max": HistoricDAO.obtener_horas_criticas(
                "humedad"
            ),
            "hora_humedad_min": HistoricDAO.obtener_horas_criticas(
                "humedad", 
                asc = True
            )
        }

        return horas_pico

    @staticmethod
    def define_computing_data_dia(
        estacion_id: Optional[int],
        provincia_id: Optional[int],
        fec_init: datetime,
        fec_fin: datetime
    ):
        """Obtiene los datos computados necesarios para cargar un DTO diario"""
        try:
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
                    MedicionClimatica.estacion.label('estacion'),
                    func.date_trunc("day", MedicionClimatica.timestamp).label("fecha")
                )
                .where(
                    or_(
                        MedicionClimatica.estacion_id == estacion_id,
                        MedicionClimatica.provincia_id == provincia_id
                    ),
                    MedicionClimatica.timestamp.between(fec_init, fec_fin)
                )
                .group_by("fecha")
                .order_by("fecha")
            )

            valores_globales = db.session.execute(queryGlobal).all()

            return {
                "valores_diarios": [dict(row._mapping) for row in valores_globales],
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
            queryGlobal = (
                select(
                    func.date_trunc("year", MedicionClimatica.timestamp).label('anio'),
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
                    func.avg(MedicionClimatica.pep_mon).label('pep_mon')
                )
                .where(
                    or_(
                        MedicionClimatica.estacion_id == estacion_id,
                        MedicionClimatica.provincia_id == provincia_id
                    ),
                    MedicionClimatica.timestamp.between(fec_init, fec_fin)
                )
                .group_by("anio", MedicionClimatica.semana)
                .order_by("anio", MedicionClimatica.semana)
            )

            valores_globales = db.session.execute(queryGlobal).all()
            
            return {
                "valores_diarios": [dict(row._mapping) for row in valores_globales],
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
                    func.date_trunc("year", MedicionClimatica.timestamp).label('anio'),
                    func.data_trunc("month", MedicionClimatica.timestamp).label('mes'),
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
                    or_(
                        MedicionClimatica.estacion_id == estacion_id,
                        MedicionClimatica.provincia_id == provincia_id
                    ),
                    MedicionClimatica.timestamp.between(fec_init, fec_fin)
                )
                .group_by(MedicionClimatica.mes, MedicionClimatica.anio)
                .order_by(MedicionClimatica.mes, MedicionClimatica.anio)
            )
            
            valores_globales = db.session.execute(queryGlobal).all()
            
            return {
                "valores_diarios": [dict(row._mapping) for row in valores_globales],
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
