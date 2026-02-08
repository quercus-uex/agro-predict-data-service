# Donde se almacenarán los modelos para pasarlos a la BD
from typing import List
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Index, Date, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from .extensions import db

class IngestaStatus(db.Model):
    __tablename__ = 'ingesta_status'

    id = Column(Integer, primary_key = True, autoincrement = True)
    dataset = Column(String(30), nullable = False) # Historico / Actual / Futuro
    tipo = Column(String(20), nullable = False) # Hora / Dia / Mes
    year = Column(Integer, nullable = False)
    month = Column(Integer, nullable = False)
    day = Column(Integer, nullable = False)

    status = Column(String(20), nullable = False) # Pending / Loading / Ready

    started_at = Column(DateTime, nullable = False)
    finished_at = Column(DateTime, nullable = True)
    error_message = Column(Text, nullable = True)

    zona = Column(String(20), nullable = False)

    # Constraint para evitar valores duplicados
    __table_args__ = (
        UniqueConstraint(
            'dataset', 'tipo', 'year', 'month', 'day', 'zona',
            name = 'uq_ingesta_dataset_fecha'
        ),
    )

class Sector(db.Model):
    __tablename__ = 'sectores'
    
    id = Column(Integer, primary_key = True, autoincrement = True)
    nombre = Column(String(50), unique = True, nullable = False)
    finca_id = Column(Integer, ForeignKey("fincas.id"), nullable = False)
    #cultivo_id = Column(Integer, ForeignKey("cultivos.id"), nullable = True)

    finca = relationship("Finca", back_populates = "sectores")
    #cultivo = relationship("Cultivo", back_populates = "sectores")

class Plaga(db.Model):
    __tablename__ = 'plagas'

    id = Column(Integer, primary_key = True, autoincrement = True)
    public_id = Column(String(5), nullable = False)
    nombre = Column(String(100), unique = True, nullable = False)
    agente_causante = Column(String(100), nullable = False)
    momento_critico = Column(String(300), nullable = True)
    observaciones = Column(String(1000), nullable = True)
    mas_info = Column(String(300), nullable = True)
    tipo = Column(String(50), nullable = False)

    calendarios = relationship("CalendarioPlaga", back_populates = "plaga")

class CalendarioPlaga(db.Model):
    __tablename__ = 'calendario_plaga'

    id = Column(Integer, primary_key = True, autoincrement = True)
    cultivo_id = Column(String(50), nullable = False)
    plaga_id = Column(Integer, ForeignKey("plagas.id"), nullable = False)
    grupo = Column(String(50), nullable = False)
    semana = Column(Integer, nullable = False)
    nivel_alerta = Column(Integer, nullable = False)

    plaga = relationship("Plaga", back_populates = "calendarios")

class Finca(db.Model):
    __tablename__ = 'fincas'

    id = Column(Integer, primary_key = True, autoincrement = True)
    #provincia_id = Column(Integer, ForeignKey("provincias.id"), nullable = False)
    #estacion_id = Column(Integer, ForeignKey('estaciones.id'), nullable = False)
    nombre = Column(String(50), unique = True, nullable = False)

    #estaciones = relationship("Estacion", back_populates = "finca")
    sectores = relationship("Sector", back_populates = "finca")
    #provincia = relationship("Provincia", back_populates = "fincas")

class Estacion(db.Model):
    __tablename__ = 'estaciones'

    id = Column(Integer, primary_key=True, autoincrement = True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), unique=False, nullable=False)
    longitud = Column(String(100), nullable=False)
    latitud = Column(String(100), nullable=False)
    altitud = Column(Integer, nullable=False)
    provincia_id = Column(Integer, ForeignKey("provincias.id"), nullable = False)
    #finca_id = Column(Integer, ForeignKey("fincas.id"), nullable = False)

    mediciones = relationship("MedicionClimatica", back_populates="estacion")
    #finca = relationship("Finca", back_populates = "estaciones")
    provincia = relationship("Provincia", back_populates = "estaciones")

class Provincia(db.Model):
    __tablename__ = 'provincias'

    id = Column(Integer, primary_key=True, autoincrement = True)
    codigo = Column(String(20), unique = True, nullable = False)
    nombre = Column(String(50), unique = True, nullable = False)
    ccaa_id = Column(Integer, ForeignKey("ccaa.id"), nullable = False)

    ccaa = relationship("CCAA", back_populates="provincias")
    estaciones = relationship("Estacion", back_populates="provincia")
    #fincas = relationship("Finca", back_populates = "provincia")
    mediciones = relationship("MedicionClimatica", back_populates="provincia")
    predicciones = relationship("Predicciones", back_populates = "provincia")
    
class CCAA(db.Model):
    __tablename__ = 'ccaa'

    id = Column(Integer, primary_key = True, autoincrement = True)
    codigo = Column(String(20), unique = True, nullable = False)
    nombre = Column(String(50), unique = True, nullable = False)

    provincias = relationship("Provincia", back_populates = "ccaa")
    predicciones = relationship("Predicciones", back_populates = "ccaa")

class MedicionClimatica(db.Model):
    __tablename__ = 'mediciones_climaticas'

    id = Column(Integer, primary_key=True, autoincrement = True)
    estacion_id = Column(Integer, ForeignKey("estaciones.id"), nullable = True)
    provincia_id = Column(Integer, ForeignKey("provincias.id"), nullable = True)
    semana = Column(Integer, nullable = True)
    mes = Column(Integer, nullable = True)
    anio = Column(Integer, nullable = True)
    timestamp = Column(DateTime, nullable = False, index = True )

    humedad = Column(Float, nullable = False)
    temperatura = Column(Float, nullable = False)
    vel_viento = Column(Float)
    precipitacion = Column(Float, nullable = False)
    etp_mon = Column(Float, nullable = True)
    pep_mon = Column(Float, nullable = True)

    estacion = relationship("Estacion", back_populates = "mediciones")
    provincia = relationship("Provincia", back_populates = "mediciones")

    __table_args__ = (
        Index("idx_estacion_timestamp", "estacion_id", "timestamp"),
        Index("idx_provincia_timestamp", "provincia_id", "timestamp"),
        Index("idx_anio_semana", "anio", "semana")
    )

class Predicciones(db.Model):
    __tablename__ = "predicciones"

    id = Column(Integer, primary_key = True, autoincrement = True)
    
    # Foreign key con CCAA
    ccaa_id = Column(Integer, ForeignKey("ccaa.id"), nullable = True)

    # Foreign key con Provincia
    provincia_id = Column(Integer, ForeignKey("provincias.id"), nullable = True)

    # Tipo de prediccion : actual / tomorrow / aftertomorrow
    tipo_prediccion = Column(String(20), nullable = False)

    # Zona : ccaa / nacional / provincial
    tipo_zona = Column(String(20), nullable = False)
    codigo_zona = Column(String(10), nullable = True)

    # Fechas
    fecha_prediccion = Column(Date, nullable = False)
    fecha_elaboracion = Column(DateTime, nullable = False)


    # Texto original
    texto_original = Column(Text, nullable = False)

    # Datos específicos recogidos
    estado_cielo = Column(String(100), nullable = True)
    tendencia_temp_general = Column(String(100), nullable = True)
    tendencia_temp_max = Column(String(50), nullable = True)
    tendencia_temp_min = Column(String(50), nullable = True)
    rachas_viento = Column(String(100), nullable = True)
    precipitaciones = Column(String(300), nullable = True)
    cotas_nieve = Column(String(100), nullable = True)
    existencia_helada = Column(Boolean, nullable = True)
    zona_helada  = Column(String(100), nullable = True)
    aparicion_nieblas = Column(String(100), nullable = True)

    ccaa = relationship("CCAA", back_populates = "predicciones")
    provincia = relationship("Provincia", back_populates = "predicciones")

    __table_args__ = (
        Index("idx_pred_tipo_fecha", "tipo_zona", "fecha_prediccion"),
        Index("idx_zona_fecha", "codigo_zona", "fecha_prediccion")
    )
