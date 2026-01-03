# Donde se almacenarán los modelos para pasarlos a la BD
from typing import List
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from app import db

class Sectores(db.Model):
    __tablename__ = 'sectores'
    
    id = Column(Integer, primary_key = True, autoincrement = True)
    nombre = Column(String(50), unique = True, nullable = False)
    finca_id = Column(Integer, ForeignKey("fincas.id"), nullable = False)
    cultivo_id = Column(String(50), nullable = True)

    finca = relationship("Finca", back_populates = "sectores")

class Cultivo(db.Model):
    __tablename__ = 'cultivos'

    id = Column(Integer, primary_key = True, autoincrement = True)
    nombre = Column(String(100), unique = True, nullable = False)
    grupo = Column(String(50), nullable = False)
    calendario_id = Column(Integer, ForeignKey("calendario_cultivo.id"), nullable = False)

    calendario = relationship("CalendarioCultivo", back_populates = "cultivo")

class CalendarioCultivo(db.Model):
    __tablename__ = 'calendario_cultivo'

    id = Column(Integer, primary_key = True, autoincrement = True)
    cultivo_id = Column(Integer, ForeignKey("cultivos.id"), nullable = False)
    semana = Column(Integer, nullable = False)
    nivel_alerta = Column(Integer, nullable = False)

    cultivo = relationship("Cultivo", back_populates = "calendario_cultivo")

class Finca(db.Model):
    __tablename__ = 'fincas'

    id = Column(Integer, primary_key = True, autoincrement = True)
    provincia_id = Column(Integer, ForeignKey("provincias.id"), nullable = False)
    nombre = Column(String(50), unique = True, nullable = False)

    estaciones = relationship("Estacion", back_populates = "finca")
    sectores = relationship("Sector", back_populates = "finca")
    provincia = relationship("Provincia", back_populates = "fincas")

class Estacion(db.Model):
    __tablename__ = 'estaciones'

    id = Column(Integer, primary_key=True, autoincrement = True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), unique=True, nullable=False)
    provincia_id = Column(Integer, ForeignKey("provincias.id"), nullable = False)
    finca_id = Column(Integer, ForeignKey("fincas.id"), nullable = False)

    mediciones = relationship("MedicionClimatica", back_populates="estacion")
    finca = relationship("Finca", back_populates = "estaciones")
    provincia = relationship("Provincia", back_populates = "estaciones")

class Provincia(db.Model):
    __tablename__ = 'provincias'

    id = Column(Integer, primary_key=True, autoincrement = True)
    codigo = Column(String(20), unique = True, nullable = False)
    nombre = Column(String(50), unique = True, nullable = False)
    ccaa_id = Column(Integer, ForeignKey("ccaa.id"), nullable = False)

    ccaa = relationship("CCAA", back_populates="provincias")
    estaciones = relationship("Estacion", back_populates="provincia")
    fincas = relationship("Finca", back_populates = "provincia")

class CCAA(db.Model):
    __tablename__ = 'ccaa'

    id = Column(Integer, primary_key = True, autoincrement = True)
    codigo = Column(String(20), unique = True, nullable = False)
    nombre = Column(String(50), unique = True, nullable = False)

    provincias = relationship("Provincia", back_populates="ccaa")

class MedicionesClimaticas(db.Model):
    __tablename__ = 'mediciones_climaticas'

    id = Column(Integer, primary_key=True, autoincrement = True)
    estacion_id = Column(Integer, ForeignKey("estaciones.id"), nullable = False)
    timestamp = Column(DateTime, nullable = False, index = True )

    humedad = Column(Float)
    temperatura = Column(Float)
    vel_viento = Column(Float)
    precipitacion = Column(Float)
    etp_mon = Column(Float)
    pep_mon = Column(Float)

    estacion = relationship("Estacion", back_populates = "mediciones")