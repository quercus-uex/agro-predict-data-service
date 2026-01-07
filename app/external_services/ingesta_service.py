from app import db
from typing import Optional
from datetime import date
from ..historicos.historico_dto import TipoHistorico
from .siar_service import SiARService
from ..models import MedicionClimatica, Estacion, Provincia, CCAA
class IngestionService:

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
            estacion : Estacion = Estacion.query.filter_by(codigo_estacion_id=Estacion.codigo).one()
            provincia : Provincia = Provincia.query.filter_by(codigo_provincia_id=Provincia.codigo).one()

            medicion = MedicionClimatica(
                estacion_id = estacion.id,
                provincia_id = provincia.id,
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
            print(medicion, flush=True)
            # Comprobamos si existe ya el dato a insertar, para evitar duplicados
            existe = db.session.query(MedicionClimatica.id).filter_by(
                estacion_id=estacion.id,
                timestamp=d_timestamp
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

            if estaciones:
                codigo_raw : str = d.get('codigo')
                codigo_formateado = codigo_raw[0:3] # Segmentación para quedarme con las dos primeras letras de la cadena que indican la provincia
                
                provincia : Provincia = Provincia.query.filter_by(codigo_formateado=Provincia.codigo).one()

                estacion = Estacion(
                    codigo = d.get('codigo'),
                    nombre = d.get('nombre'),
                    longitud = d.get('longitud'),
                    latitud = d.get('latitud'),
                    altitud = d.get('altitud'),
                    provincia_id = provincia.id
                )
                # Comprobamos si ya existe la estacion en la BD, para no tener duplicados
                existe = db.session.query(Estacion.id).filter_by(
                    codigo=estacion.codigo,
                    nombre=estacion.nombre,
                    provincia_id=provincia.id
                ).first()

                if existe:
                    continue

                db.session.add(estacion)
            else:
                codigo_ccaa = d.get('codigo_ccaa')
                
                ccaa : CCAA = CCAA.query.filter_by(codigo_ccaa=CCAA.codigo).one()
                
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