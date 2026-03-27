from app.extensions import db
from typing import Optional
from datetime import date, timedelta, datetime
from ..external_services.siar_service import SiARService
from ..ingesta.ingesta_dao import IngestaDAO
from ..models import (
    MedicionClimatica, 
    Estacion, 
    Provincia, 
    CCAA, 
    Plaga,
    CalendarioPlaga,
    Sensores
)

from ..external_services.aemet_service import AemetService
from ..external_services.itacyl_service import ItacylService
from ..external_services.dtagro_service import DTAgroService
from metadata.metadata_dao import MetadataDAO
from config.config import Config
import pandas as pd
import json
import os

class IngestionService:

    @staticmethod
    def ingesta_metadata(
        modelo,
        campos_unicos : list[str],
        nombre_fichero : str,
        mapeo_columnas : dict,
        transformaciones : Optional[dict] = None # Funcion especial a aplicar por campo especial
    ):
        try: 
            ruta_fichero = Config.obtener_ruta_contenido_metadatos(modelo.__name__.lower())
            fichero = ruta_fichero / nombre_fichero
            
            # Leo los ficheros csv almacenandolos en un dataframe
            df = pd.read_csv(fichero)

            # Renombrar columnas segun el mapeo
            df = df.rename(mapeo_columnas)

            # Me quedo solo con las columnas pertenecientes al modelo seleccionado
            columnas_modelo = list(mapeo_columnas.values())
            df = df[columnas_modelo]

            # Aplico transformaciones de datos opcionales por campo
            if transformaciones:
                for campo, funcion in transformaciones.items():
                    if campo in df.columns:
                        df[campo] = df[campo].apply(function)

            # Pasamos el contenido del dataframe a dict para manejarlo mejor
            contenido = df.to_dict(orient = "records")

            insertado = 0
            for registro in contenido:
                resultado = MetadataDAO.crear_registro(
                    modelo = modelo,
                    datos = registro,
                    campos_unicos = campos_unicos
                )

                if resultado:
                    insertado +=1

            print(f"Ingesta de {modelo.__name__}: {insertado} insertados")

        except Exception as e:
            print(f"Error al ingestar datos sobre el modelo {modelo.__name__} : {e}")






    @staticmethod
    def ingesta_sensores_data(
        eui : str,
        fecha_inicio : date,
        fecha_fin : date
    ):
        try:
            print(f"Parametros : {eui} - {fecha_inicio} - {fecha_fin}")
            # Obtengo los datos que recibe DTAgroService
            datos = DTAgroService.get_dtagro_datos(
                eui = eui,
                fecha_inicio = fecha_inicio,
                fecha_fin = fecha_fin
            )

            # Recorro los datos obtenidos y los inserto en la base de datos
            for d in datos:
                if d is not None:
                    IngestaDAO.crear_datos_sensores(
                        eui = eui,
                        humedad_foliar = d['humedad_foliar'],
                        temperatura_sensor = d['temp_DS18B20'],
                        temperatura_hojas = d['temperatura_hoja'],
                        timestamp = d['timestamp']
                    )

            # Si no ha habido ningún error, se da paso a creat todos los datos obtenidos
            db.session.commit()
        
        except Exception as e:
            print(f"Error intentando cargar nuevos datos de sensores en la base de datos : {e}")
            return None


    @staticmethod
    def ingest_localidad_data():
        try:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(BASE_DIR, "..", "data", "location_altitudes.json")
            with open(file_path, 'r', encoding = 'utf-8') as f:
                datos = json.load(f)

            # Recorro todas las localidades que hay almacenadas en el json
            for d in datos:
                print(f"Dato : {d}")
                IngestaDAO.crear_localidades(
                    nombre = d['nombre'],
                    nombre_normalizado = d['nombre_normalizado'],
                    altitud = d['altitud'],
                    longitud = d['longitud'],
                    latitud = d['latitud'],
                    provincia = d['provincia']
                )

            db.session.commit()

        except Exception as e:
            print (f"Algo ha ido mal insertando datos de localidades : {e}")
            return None

    @staticmethod
    def ingest_aemet_data(
        tipo_zona,
        tipo_prediccion,
        codigo_zona : Optional[str],
        fecha
    ):
        print("Entro en la ingesta de datos AEMET")
        try:

            # Actualizamos el estado almacenado a LOADING porque se van a cargar los datos
            IngestaDAO.actualizar_estado(
                status = 'LOADING',
                dataset = 'actual_futuro',
                tipo = tipo_prediccion.value,
                year = fecha.year,
                month = fecha.month,
                day = fecha.day,
                zona = tipo_zona.value,
                finish_time = None,
                error = None
            )
            print("Antes de llamar al servicio de datos")
            data_predicciones, data_localidades = AemetService.get_aemet_data(
                tipo_prediccion = tipo_prediccion,
                tipo_zona = tipo_zona,
                codigo_zona = codigo_zona,
                fecha = fecha
            )

            print(f"Aemet data : {data_predicciones} + {data_localidades}")
            
            # Creo la prediccion sobre los datos obtenidos de la IA
            prediccion_insertada = IngestaDAO.crear_predicciones(
                codigo_zona = codigo_zona,
                data = data_predicciones
            )

            print(f"Prediccion id : {prediccion_insertada.id}")

            # Obtengo la informacion de las localidades obtenidas
            localidades = data_localidades.get('temperaturas_localidades')
            # Obtengo los datos internos de las localidades
            for localidad, datos in localidades.items():
                temp_max = datos.get('temp_max')
                temp_min = datos.get('temp_min')
                IngestaDAO.crear_localidades_climaticas(
                    prediccion_id = prediccion_insertada.id,
                    loc = localidad,
                    temp_max = temp_max,
                    temp_min = temp_min
                )

            db.session.commit()

            # Todo ha salido bien por lo que cambiamos el estado de los datos solicitados READY
            IngestaDAO.actualizar_estado(
                status = 'READY',
                dataset = 'actual_futuro',
                tipo = tipo_prediccion.value,
                year = fecha.year,
                month = fecha.month,
                day = fecha.day,
                finish_time = datetime.now(),
                zona = tipo_zona.value,
                error = None
            )

            db.session.commit()
        
        except Exception as e:
            # Algo fallo, por lo que cambiamos el estado a FAILED
            IngestaDAO.actualizar_estado(
                status = 'FAILED',
                dataset = 'actual_futuro',
                tipo = tipo_prediccion.value,
                year = fecha.year,
                month = fecha.month,
                day = fecha.day,
                finish_time = datetime.now(),
                zona = tipo_zona.value,
                error = str(e)
            )

    @staticmethod
    def ingest_itacyl_data(
        cultivo : Optional[int],
        grupo : Optional[str]
    ):
        try:
            # ITACyL no tiene un controlador del estado de ingesta de datos
            # La información es global y estática, no cambia con el tiempo
            # No influyen las fechas para la recopilación de datos.
            data = ItacylService.get_itacyl_datos(
                cultivo = cultivo,
                grupo = grupo
            )

            # Extraigo todas los calendarios almacenados en la db
            # Para comprobar futuros repetidos
            existing_calendars = set(
                (c.cultivo_id, c.grupo, c.semana)
                for c in db.session.query(
                    CalendarioPlaga.cultivo_id,
                    CalendarioPlaga.grupo,
                    CalendarioPlaga.semana
                ).all()
            )

            # Extraigo todas las plagas almacenadas en la db
            # Para comprobar futuros repetidos
            existing_plagas = set(
                (p.public_id, p.nombre, p.agente_causante, p.momento_critico, p.tipo)
                for p in db.session.query(
                    Plaga.public_id,
                    Plaga.nombre,
                    Plaga.agente_causante,
                    Plaga.momento_critico,
                    Plaga.tipo
                ).all()
            )

            # Itero sobre los datos recibidos
            for d in data:
                plaga_key = (
                    d.get('id'),
                    d.get('nombre'),
                    d.get('agente_causante'),
                    d.get('momento_critico'),
                    d.get('tipo')
                )

                if plaga_key not in existing_plagas:
                    plaga = Plaga(
                        public_id = d.get('id'),
                        nombre = d.get('nombre'),
                        agente_causante = d.get('agente_causante'),
                        momento_critico = d.get('momento_critico'),
                        observaciones = d.get('observaciones'),
                        mas_info = d.get('enlace'),
                        tipo = d.get('tipo')
                    )

                    db.session.add(plaga)
                    db.session.flush() # Debo de enviar los cambios a la bd antes del commit para que lo use el calendario
                    existing_plagas.add(plaga_key) # Evito duplicados en el procesamiento de datos

                # Calendarios
                for calendario_item in d.get('calendario_de_productos', []):
                    for c in calendario_item.get('calendar', []):
                        calendario_key = (
                            cultivo if cultivo else "General",
                            grupo,
                            c.get('week')
                        )
                        if calendario_key not in existing_calendars:
                            calendario = CalendarioPlaga(
                                cultivo_id = cultivo,
                                plaga_id = plaga.id,
                                grupo = grupo,
                                semana = c.get('week'),
                                nivel_alerta = c.get('alertLevel')
                            )

                            db.session.add(calendario)
                            existing_calendars.add(calendario)

            db.session.commit()
        except Exception as e:
            print(f"Ha ocurrido un error insertando datos de plagas con sus calendarios : {e}")
            # Para echar para atrás el flush que se hace
            db.session.rollback()
            return []
            

    @staticmethod
    def ingest_siar_data(
        codigo_estacion_id : Optional[str],
        codigo_provincia_id : Optional[str],
        tipo,
        fec_init : date,
        fec_fin: date
    ):
        try:
            # Actualizamos el estado almacenado a LOADING porque se van a cargar los datos
            IngestaDAO.actualizar_estado(
                status = 'LOADING',
                dataset = 'historico',
                tipo = tipo.value,
                year = fec_init.year,
                month = fec_init.month,
                day = fec_init.day,
                zona = "provincia" if codigo_provincia_id else "estacion",
                finish_time = None,
                error = None
            )


            # Obtengo los datos del siar
            data = SiARService.get_siar_data(
                estacion_id = codigo_estacion_id,
                provincia_id = codigo_provincia_id,
                tipo = tipo,
                fec_init = fec_init,
                fec_fin = fec_fin  
            )     

            for d in data:
                
                d_timestamp = d["timestamp"]
                anio, semana, _ = d_timestamp.isocalendar()
                
                # Mapeo de estacion y provincia 
                estacion : Estacion = Estacion.query.filter_by(codigo=d["estacion"]).first()
                provincia : Provincia = Provincia.query.filter_by(codigo=codigo_provincia_id).first()

                medicion = MedicionClimatica(
                    estacion_id = estacion.id if estacion else None,
                    provincia_id = provincia.id if provincia else None,
                    semana = semana,
                    mes = d_timestamp.month,
                    anio = anio,
                    timestamp = d_timestamp,
                    humedad = d.get('humedad'),
                    temperatura = d.get('temperatura'),
                    vel_viento = d.get('vel_viento'),
                    precipitacion = d.get('precipitacion'),
                    etp_mon = d.get('etp_mon'),
                    pep_mon = d.get('pep_mon')
                )
                # Comprobamos si existe ya el dato a insertar, para evitar duplicados
                existe = db.session.query(MedicionClimatica.id).filter_by(
                    temperatura=medicion.temperatura,
                    humedad=medicion.humedad,
                    vel_viento=medicion.vel_viento,
                    precipitacion=medicion.precipitacion,
                    etp_mon=medicion.etp_mon,
                    pep_mon=medicion.pep_mon
                ).first()

                if existe:
                    continue

                # Almacenamos los datos en la base de datos
                db.session.add(medicion)

            IngestaDAO.actualizar_estado(
                status = 'READY',
                dataset = 'historico',
                tipo = tipo.value,
                year = fec_init.year,
                month = fec_init.month,
                day = fec_init.day,
                finish_time = datetime.now(),
                zona = "provincia" if codigo_provincia_id else "estacion",
                error = None
            )
            # Cuando estén todos los datos formados correctamente, se confirma la inserción de los datos
            db.session.commit()
        
        except Exception as e:
            IngestaDAO.actualizar_estado(
                status = 'FAILED',
                dataset = 'historico',
                tipo = tipo.value,
                year = fec_init.year,
                month = fec_init.month,
                day = fec_init.day,
                finish_time = datetime.now(),
                zona = "provincia" if codigo_provincia_id else "estacion",
                error = str(e)
            )
    
    @staticmethod
    def ingest_info(
        estaciones : bool = True
    ):
        data = SiARService.get_siar_informacion(
            estaciones = estaciones
        )

        for d in data:
            # Si se ha especificado en la peticion, inserto las estaciones
            if estaciones:
                codigo_raw : str = d.get('codigo')
                codigo_formateado = codigo_raw[0:2] # Segmentación para quedarme con las dos primeras letras de la cadena que indican la provincia

                # Solo nos interesa las de caceres, si no, comentar este condicional
                if codigo_formateado != "CC":
                    continue
                
                provincia : Provincia = Provincia.query.filter_by(codigo=codigo_formateado).one_or_none()

                estacion = Estacion(
                    codigo = d.get('codigo'),
                    nombre = d.get('nombre_estacion'),
                    longitud = d.get('longitud'),
                    latitud = d.get('latitud'),
                    altitud = d.get('altitud'),
                    provincia_id = provincia.id
                )
                # Comprobamos si ya existe la estacion en la BD, para no tener duplicados
                existe = db.session.query(Estacion.id).filter_by(
                    codigo=estacion.codigo
                ).first()

                if existe:
                    continue

                db.session.add(estacion)  
            else:
                print(f"Datos de ingestaService: {data}")
                # Inserto primero las comunidades autonomas
                if d.get('nombre-comunidades'):
                    todas_comunidades = d['nombre-comunidades']
                    print(f"Todas las comunidades: {todas_comunidades}")
                    continue

                codigo_ccaa_raw : str = d['codigo_ccaa']
                print(f"Codigo de comunidad autonoma: {codigo_ccaa_raw}")
                if not codigo_ccaa_raw:
                    print(f"Elemento sin codigo_ccaa: {d}")
                    continue

                nombre_ccaa = next((n.strip() for n in todas_comunidades if n.upper().startswith(codigo_ccaa_raw)), None)
                
                if not nombre_ccaa:
                    print(f"No se ha podido encontrar el nombre para {codigo_ccaa_raw}")
                    continue

                ccaa_existe = CCAA.query.filter_by(codigo=codigo_ccaa_raw).first()
            
                if not ccaa_existe:
                    comunidad_autonoma = CCAA(
                        codigo = codigo_ccaa_raw,
                        nombre = nombre_ccaa
                    )
                    db.session.add(comunidad_autonoma)

                # Una vez insertadas las comunidades autonomas, inserto las provincias
                ccaa : CCAA = CCAA.query.filter_by(codigo=codigo_ccaa_raw).first()
                
                provincia = Provincia(
                    codigo = d.get('codigo'),
                    nombre = d.get('nombre'),
                    ccaa_id = ccaa.id
                )
                # Comprobamos si ya existe la estacion en la BD, para no tener duplicados
                existe = db.session.query(Provincia.id).filter_by(
                    codigo=provincia.codigo,
                    nombre=provincia.nombre,
                    ccaa_id=ccaa.id
                ).first()

                if existe:
                    continue
                    
                db.session.add(provincia)
        db.session.commit()

    DIAS_BLOQUES = 7 # Dias por bloques de carga
    def ingest_range(
        codigo_estacion_id : Optional[str],
        codigo_provincia_id : Optional[str],
        tipo,
        fec_init : date,
        fec_fin : date
    ):
        actual = fec_init

        total_days = (fec_fin - fec_init).days + 1
        print(f"Inicio de carga masiva de datos: {fec_init} -> {fec_fin}")

        while actual <= fec_fin:
            bloque_fin = min(actual + timedelta(days=IngestionService.DIAS_BLOQUES - 1), fec_fin)

            print(f"\nCargando bloque {actual} → {bloque_fin}")

            try:
                IngestionService.ingest_data(
                    codigo_estacion_id=codigo_estacion_id,
                    codigo_provincia_id=codigo_provincia_id,
                    tipo=tipo,
                    fec_init=actual,
                    fec_fin=bloque_fin
                )
                print(f"✔️ Bloque cargado correctamente")
            except Exception as e:
                print(f"❌ Error cargando {actual} → {bloque_fin}: {e}")

            actual = bloque_fin + timedelta(days=1)
        print("\nCarga masiva finalizada.")