# Donde se almacenarán los modelos para pasarlos a la BD
from typing import List
from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    ForeignKey, 
    DateTime, 
    Float, 
    Index, 
    Date, 
    Text, 
    Boolean, 
    UniqueConstraint,
    JSON
)
from sqlalchemy.orm import relationship
from .extensions import db

class TipoDato(db.Model):
    __tablemane__ = 'tipo_dato'

    id = Column(Integer, primary_key = True, autoincrement = True)
    nombre = Column(String(50), nullable = False, unique = True)
    descripcion = Column(String(300), nullable = True)

    plagas_tipo_dato = relationship("PlagaTipoDato", back_populates = "tipo_dato")

class EtapaFenologica(db.Model):
    __tablename__ = 'etapa_fenologica'

    id = Column(Integer, primary_key = True, autoincrement = True)
    nombre = Column(String(20), nullable = False, unique = True)
    codigo = Column(String(10), nullable = False, unique = True)
    orden = Column(Integer, nullable = False, unique = True)

    umbral = relationship("UmbralesTemperatura", back_populates = "etapa")

class Cultivo(db.Model):
    __tablename__ = 'cultivos'

    id = Column(Integer, primary_key = True, autoincrement = True)
    nombre = Column(String(100), nullable = False)
    nombre_cientifico = Column(String(200), nullable = False)
    descripcion = Column(String(300), nullable = False, unique = False)
    grupo = Column(String(50), nullable = False)

    variedades = relationship("Variedades", back_populates = "cultivo")
    cultivos_plagas = relationship("CultivoPlaga", back_populates = "cultivo")
    parcelas = relationship("CultivoParcela", back_populates = "cultivo")

    __table_args__ = (
        UniqueConstraint(
            'nombre', 'nombre_cientifico',
            name = 'uq_cultivo_nombre_cientifico'
        ),
    )

class CultivoParcela(db.Model):
    __tablename__ = 'cultivo_parcela'

    id = Column(Integer, primary_key = True, autoincrement = True)
    cultivo_id = Column(Integer, ForeignKey("cultivos.id"), nullable = False)
    parcela_id = Column(Integer, ForeignKey("parcelas.id"), nullable = False)
    fecha_inicio = Column(DateTime, nullable = False)
    fecha_fin = Column(DateTime, nullable = True) # Puede que no se haya producido rotación de cultivo todavía en una parcela

    cultivo = relationship("Cultivo", back_populates = "parcelas")
    parcela = relationship("Parcelas", back_populates = "cultivos")

class CultivoPlaga(db.Model):
    __tablename__ = 'cultivo_plaga'

    id = Column(Integer, primary_key = True,nullable = False, autoincrement = True)
    cultivo_id = Column(Integer, ForeignKey("cultivos.id"), nullable = False)
    plaga_id = Column(Integer, ForeignKey("plagas.id"), nullable = False)

    cultivo = relationship("Cultivo", back_populates = "cultivos_plagas")
    plaga = relationship("Plaga", back_populates = "cultivos_plagas")

    __table__args__ = (
        UniqueConstraint(
            'cultivo_id', 'plaga_id',
            name = 'uq_cultivo_plaga'
        ),
    )

class PlagaTipoDato(db.Model):
    __tablename__ = 'plaga_tipo_dato'

    id = Column(Integer, primary_key = True, autoincrement = True)
    plaga_id = Column(Integer, ForeignKey("plagas.id"), nullable = False)
    tipo_dato_id = Column(Integer, ForeignKey('tipo_dato.id'), nullable = False)

    plaga = relationship("Plaga", back_populates = "plagas_tipo_dato")
    tipo_dato = relationship("TipoDato", back_populates = "plagas_tipo_dato")

    __table__args__ = (
        UniqueConstraint(
            'plaga_id', 'tipo_dato_id',
            name = 'uq_plaga_tipo_dato'
        )
    )


class Variedades(db.Model):
    __tablename__ = 'variedades'

    id = Column(Integer, primary_key = True, autoincrement = True)
    cultivo_id = Column(Integer, ForeignKey("cultivos.id"), nullable = False)
    nombre = Column(String(200), nullable = False)
    horas_frio_min = Column(Integer, nullable = False)
    horas_frio_max = Column(Integer, nullable = False)
    horas_frio_actuales = Column(Float)
    modelo_id = Column(Integer, ForeignKey("modelos_hora_frio.id"), nullable = False)

    cultivo = relationship("Cultivo", back_populates = "variedades")
    modelo = relationship("ModelosHoraFrio", back_populates = "variedades")
    umbral = relationship("UmbralesTemperatura", back_populates = "variedades")

    __table_args__ = (
        UniqueConstraint(
            'nombre', 'cultivo_id', 'modelo_id',
            name = 'uq_variedad'
        ),
    )

class UmbralesTemperatura(db.Model):
    __tablename__ = 'umbrales_temperatura'

    id = Column(Integer, primary_key = True, autoincrement = True)
    variedad_id = Column(Integer, ForeignKey("variedades.id"), nullable = False)
    etapa_id = Column(Integer, ForeignKey("etapa_fenologica.id"), nullable = False)
    critico = Column(Float, nullable = False)
    alto = Column(Float, nullable = False)
    moderado = Column(Float, nullable = False)
    bajo = Column(Float, nullable = False)

    etapa = relationship("EtapaFenologica", back_populates = "umbral")
    variedades = relationship("Variedades", back_populates = "umbral")

class ModelosHoraFrio(db.Model):
    __tablename__ = 'modelos_hora_frio'

    id = Column(Integer, primary_key = True, autoincrement = True)
    nombre = Column(String(50), nullable = False, unique = True)
    codigo = Column(String(10), nullable = False, unique = True)
    descripcion = Column(String(300), nullable = False)

    variedades = relationship("Variedades", back_populates = "modelo")


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


class Plaga(db.Model):
    __tablename__ = 'plagas'

    id = Column(Integer, primary_key = True, autoincrement = True)
    public_id = Column(String(30), nullable = False)
    nombre = Column(String(100), unique = True, nullable = False)
    agente_causante = Column(String(100), nullable = False)
    momento_critico = Column(String(300), nullable = True)
    observaciones = Column(String(1000), nullable = True)
    mas_info = Column(String(300), nullable = True)
    tipo = Column(String(50), nullable = False)
    grupo = Column(String(100), nullable = True)
    condiciones_evaluables = Column(JSON, nullable = False)
    ventana_temporal = Column(JSON, nullable = True)
    algoritmo = Column(String(50), nullable = False)
    algoritmo_url = Column(String(200), nullable = True)

    calendarios = relationship("CalendarioPlaga", back_populates = "plaga")
    cultivos_plagas = relationship("CultivoPlaga", back_populates = "plaga")
    plagas_tipo_dato = relationship("PlagaTipoDato", back_populates = "plaga")

class CalendarioPlaga(db.Model):
    __tablename__ = 'calendario_plaga'

    id = Column(Integer, primary_key = True, autoincrement = True)
    plaga_id = Column(Integer, ForeignKey("plagas.id"), nullable = False)
    grupo = Column(String(50), nullable = False)
    semana = Column(Integer, nullable = False)
    nivel_alerta = Column(Integer, nullable = False)

    plaga = relationship("Plaga", back_populates = "calendarios")


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
    localidades = relationship("Localidades", back_populates = "provincia")
    
class CCAA(db.Model):
    __tablename__ = 'ccaa'

    id = Column(Integer, primary_key = True, autoincrement = True)
    codigo = Column(String(20), unique = True, nullable = False)
    nombre = Column(String(50), unique = True, nullable = False)

    provincias = relationship("Provincia", back_populates = "ccaa")
    predicciones = relationship("Predicciones", back_populates = "ccaa")

class Localidades(db.Model):
    __tablename__ = 'localidades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable = False)
    nombre_normalizado = Column(String(50), nullable = False)
    altitud = Column(Integer, nullable = False)
    latitud = Column(Float, nullable = True)
    longitud = Column(Float, nullable = True)
    provincia_id = Column(Integer, ForeignKey('provincias.id'), nullable = False)

    provincia = relationship("Provincia", back_populates = "localidades")
    localidades_climaticas = relationship("LocalidadesClimaticas", back_populates = "localidad")

class LocalidadesClimaticas(db.Model):
    __tablename__ = 'localidades_climaticas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prediccion_id = Column(Integer, ForeignKey('predicciones.id'), nullable = True)
    localidad_id = Column(Integer, ForeignKey('localidades.id'), nullable = False)
    nombre = Column(String(50), nullable = False)
    temperatura_maxima = Column(Integer, nullable = True)
    temperatura_minima = Column(Integer, nullable = True)

    prediccion = relationship("Predicciones", back_populates = "localidades_climaticas")
    localidad = relationship("Localidades", back_populates = "localidades_climaticas")

    __table_args__ = (
        UniqueConstraint(
            'prediccion_id', 'nombre',
            name = 'uq_prediccion_localidad'
        ),
    )

class MedicionClimatica(db.Model):
    __tablename__ = 'mediciones_climaticas'

    id = Column(Integer, primary_key=True, autoincrement = True)
    estacion_id = Column(Integer, ForeignKey("estaciones.id"), nullable = True)
    provincia_id = Column(Integer, ForeignKey("provincias.id"), nullable = True)
    semana = Column(Integer, nullable = True)
    mes = Column(Integer, nullable = True)
    anio = Column(Integer, nullable = True)
    timestamp = Column(DateTime, nullable = False, index = True )

    humedad = Column(Float)
    temperatura = Column(Float, nullable = False)
    vel_viento = Column(Float)
    precipitacion = Column(Float, nullable = False)
    etp_mon = Column(Float, nullable = True)
    pep_mon = Column(Float, nullable = True)
    radiacion = Column(Float, nullable = True)

    estacion = relationship("Estacion", back_populates = "mediciones")
    provincia = relationship("Provincia", back_populates = "mediciones")

    __table_args__ = (
        Index("idx_estacion_timestamp", "estacion_id", "timestamp"),
        Index("idx_provincia_timestamp", "provincia_id", "timestamp"),
        Index("idx_anio_semana", "anio", "semana")
    )

class Parcelas(db.Model):
    __tablename__ = "parcelas"
    
    id = Column(Integer, primary_key = True, autoincrement = True)

    public_id = Column(String(50), nullable = False, unique = True)
    nombre = Column(String(100), nullable = False)
    geometria = Column(JSON, nullable = False)

    sensor = relationship("Sensores", back_populates = "parcela")
    cultivos = relationship("CultivoParcela", back_populates = "parcela")

class Dispositivos(db.Model):
    __tablename__ = "dispositivos"
    
    id = Column(Integer, primary_key = True, autoincrement = True)

    public_id = Column(String(50), nullable = False)
    dev_eui = Column(String(50), nullable = False, unique = True)
    descripcion = Column(String(300), nullable = True)
    nombre = Column(String(100), nullable = True)
    creado = Column(DateTime, nullable = False)
    actualizado = Column(DateTime, nullable = True)

    sensor = relationship("Sensores", back_populates = 'dispositivo')


class Sensores(db.Model):
    __tablename__ = "sensores"

    id = Column(Integer, primary_key = True, autoincrement = True)

    eui = Column(String(50), nullable = False, unique = True)

    dispositivo_id = Column(String(50), ForeignKey(Dispositivos.dev_eui), nullable = True)
    parcela_id = Column(String(50), ForeignKey(Parcelas.public_id), nullable = True)
    geometria = Column(JSON, nullable = True)

    mediciones = relationship("MedicionesSensor", back_populates = 'sensor')
    dispositivo = relationship("Dispositivos", back_populates = 'sensor')
    parcela = relationship("Parcelas", back_populates = 'sensor')

class Metadatos(db.Model):
    __tablename__ = "metadatos"

    id = Column(Integer, primary_key = True, autoincrement = True)

    tipo = Column(String(50), nullable = False) # Controla la tabla a la que pertenece
    entidad_id = Column(String(50), nullable = False) # Almacena el identificador unico sobre la tabla definida en tipo
    clave = Column(String(50), nullable = False) 
    valor = Column(Text, nullable = False)
    fuente = Column(String(50), nullable = True)
    fecha_creacion = Column(DateTime, nullable = True)

class MedicionesSensor(db.Model):

    id = Column(Integer, primary_key = True, autoincrement = True)

    humedad_foliar = Column(Float, nullable = True)
    temperatura_DS18B20 = Column(Integer, nullable = True)
    temperatura_hojas = Column(Float, nullable = True)
    timestamp = Column(String(50), nullable = False)
    temperatura_suelo = Column(Float, nullable = True)
    humedad_suelo = Column(Float, nullable = True)
    temperatura_minima = Column(Float, nullable = True)
    temperatura_maxima = Column(Float, nullable = True)
    sensor_id = Column(Integer, ForeignKey("sensores.id"), nullable = False)

    sensor = relationship("Sensores", back_populates = 'mediciones')

    __table_args__ = (
        UniqueConstraint(
            'sensor_id', 'timestamp',
            name = 'uq_sensor_data'
        ),
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
    estado_cielo = Column(String(300), nullable = True)
    tendencia_temp_general = Column(String(100), nullable = True)
    tendencia_temp_max = Column(String(50), nullable = True)
    tendencia_temp_min = Column(String(50), nullable = True)
    rachas_viento = Column(String(100), nullable = True)
    precipitaciones = Column(String(300), nullable = True)
    cotas_nieve = Column(String(100), nullable = True)
    existencia_helada = Column(String(100), nullable = True)
    zona_helada  = Column(String(100), nullable = True)
    aparicion_nieblas = Column(String(100), nullable = True)

    ccaa = relationship("CCAA", back_populates = "predicciones")
    provincia = relationship("Provincia", back_populates = "predicciones")
    localidades_climaticas = relationship("LocalidadesClimaticas", back_populates = "prediccion")

    __table_args__ = (
        Index("idx_pred_tipo_fecha", "tipo_zona", "fecha_prediccion"),
        Index("idx_zona_fecha", "codigo_zona", "fecha_prediccion")
    )
