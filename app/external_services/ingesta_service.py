from app import db
from typing import Optional
from datetime import date, timedelta
from ..historicos.historico_dto import TipoHistorico
from .siar_service import SiARService
from ..models import MedicionClimatica, Estacion, Provincia, CCAA, Predicciones
from app.globals.actuales_futuros_dto import TipoPrediccion, TipoZona
from .aemet_service import AemetService
class IngestionService:

    @staticmethod
    def ingest_aemet_data(
        tipo_zona : TipoZona,
        tipo_prediccion : TipoPrediccion,
        codigo_zona : Optional[str],
        fecha : date
    ):
        data = AemetService.get_aemet_data(
            tipo_prediccion = tipo_prediccion,
            tipo_zona = tipo_zona,
            codigo_zona = codigo_zona,
            fecha = fecha
        )

        ccaa : CCAA = CCAA.query.filter_by(codigo=codigo_zona.upper()).first()
        provincia : Provincia = Provincia.query.filter_by(codigo=codigo_zona.upper()).first()
        # Solo vamos a obtener un datos porque solo se realiza la peticion sobre un factor
        predicciones = Predicciones(
            ccaa_id = ccaa.id if ccaa else None,
            provincia_id = provincia.id if provincia else None,
            **data
        )

        existe = db.session.query(Predicciones.id).filter_by(
            tipo_prediccion = predicciones.tipo_prediccion,
            tipo_zona = predicciones.tipo_zona,
            codigo_zona = predicciones.codigo_zona,
            fecha_prediccion = predicciones.fecha_prediccion
        ).first()

        if existe:
            print("Entro")
            return
        
        #[✔]Tiene que ser los datos que reciba del broker
        db.session.add(predicciones)
        db.session.commit()


    @staticmethod
    def ingest_data(
        codigo_estacion_id : Optional[str],
        codigo_provincia_id : Optional[str],
        tipo : TipoHistorico,
        fec_init : date,
        fec_fin: date
    ):
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
        # Cuando estén todos los datos formados correctamente, se confirma la inserción de los datos
        db.session.commit()
    
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
                
                provincia : Provincia = Provincia.query.filter_by(codigo=codigo_formateado).one()

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
        tipo : TipoHistorico,
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