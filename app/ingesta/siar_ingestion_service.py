from app.extensions import db
from typing import Optional
from datetime import date, datetime
from ..external_services.siar_service import SiARService
from ..ingesta.ingesta_dao import IngestaDAO
from ..models import MedicionClimatica, Estacion, Provincia
from helpers.siar_exceptions import SiARFechaInvalidaError
import logging

logger = logging.getLogger(__name__)


class SiarIngestionService:

    @staticmethod
    def callback_db_siar(data, codigo_provincia_id, fec_init, tipo):
        """Persiste en BD cada bloque de datos devuelto por SiAR y actualiza el estado."""
        for d in data:
            d_timestamp = d["timestamp"]
            anio, semana, _ = d_timestamp.isocalendar()

            estacion = Estacion.query.filter_by(codigo=d["estacion"]).first()
            provincia = Provincia.query.filter_by(codigo=codigo_provincia_id).first()

            medicion = MedicionClimatica(
                estacion_id   = estacion.id if estacion else None,
                provincia_id  = provincia.id if provincia else None,
                semana        = semana,
                mes           = d_timestamp.month,
                anio          = anio,
                timestamp     = d_timestamp,
                humedad       = d.get('humedad'),
                temperatura   = d.get('temperatura'),
                vel_viento    = d.get('vel_viento'),
                precipitacion = d.get('precipitacion'),
                radiacion     = d.get('radiacion'),
                etp_mon       = d.get('etp_mon'),
                pep_mon       = d.get('pep_mon')
            )

            existe = db.session.query(MedicionClimatica.id).filter_by(
                temperatura   = medicion.temperatura,
                humedad       = medicion.humedad,
                vel_viento    = medicion.vel_viento,
                precipitacion = medicion.precipitacion,
                etp_mon       = medicion.etp_mon,
                pep_mon       = medicion.pep_mon,
                radiacion     = medicion.radiacion
            ).first()

            if not existe:
                db.session.add(medicion)

        IngestaDAO.actualizar_estado(
            status      = 'READY',
            dataset     = 'historico',
            tipo        = tipo.value,
            year        = fec_init.year,
            month       = fec_init.month,
            day         = fec_init.day,
            finish_time = datetime.now(),
            zona        = "provincia" if codigo_provincia_id else "estacion",
            error       = None,
            codigo      = codigo_provincia_id,
        )
        db.session.commit()

    @staticmethod
    def ingest_siar_data(
        codigo_estacion_id: Optional[str],
        codigo_provincia_id: Optional[str],
        tipo,
        fec_init: date,
        fec_fin: date
    ):
        try:
            IngestaDAO.actualizar_estado(
                status      = 'LOADING',
                dataset     = 'historico',
                tipo        = tipo.value,
                year        = fec_init.year,
                month       = fec_init.month,
                day         = fec_init.day,
                zona        = "provincia" if codigo_provincia_id else "estacion",
                finish_time = None,
                error       = None,
                codigo      = codigo_estacion_id if codigo_estacion_id else codigo_provincia_id,
            )

            lista_datos = SiARService.get_siar_data(
                estacion_id  = codigo_estacion_id,
                provincia_id = codigo_provincia_id,
                tipo         = tipo,
                fec_init     = fec_init,
                fec_fin      = fec_fin,
                on_datos_obtenidos=lambda datos_dia: SiarIngestionService.callback_db_siar(
                    datos_dia, codigo_provincia_id, fec_init, tipo
                )
            )

            IngestaDAO.actualizar_estado(
                status      = 'READY',
                dataset     = 'historico',
                tipo        = tipo.value,
                year        = fec_init.year,
                month       = fec_init.month,
                day         = fec_init.day,
                zona        = "provincia" if codigo_provincia_id else "estacion",
                finish_time = datetime.now(),
                error       = None,
                codigo      = codigo_estacion_id if codigo_estacion_id else codigo_provincia_id,
            )

            return lista_datos
        except SiARFechaInvalidaError as e:
            from ..historicos.tasks import programar_consulta_datos_task
            programar_consulta_datos_task.delay({
                'tipo'  : tipo.value,
                'codigo_estacion_id' : codigo_estacion_id,
                'codigo_provincia_id' : codigo_provincia_id,
                'fec_init' : fec_init.strftime("%Y-%m-%d"),
                'fec_fin' : fec_fin.strftime("%Y-%m-%d")
            })

            IngestaDAO.actualizar_estado(
                status      = 'PENDING_RETRY',
                dataset     = 'historico',
                tipo        = tipo,
                year        = fec_init.year,
                month       = fec_init.month,
                day         = fec_init.day,
                finish_time = datetime.now(),
                zona        = "provincia" if codigo_provincia_id else "estacion",
                error       = str(e),
                codigo      = codigo_estacion_id if codigo_estacion_id else codigo_provincia_id,
            )

        except Exception as e:
            IngestaDAO.actualizar_estado(
                status      = 'FAILED',
                dataset     = 'historico',
                tipo        = tipo.value,
                year        = fec_init.year,
                month       = fec_init.month,
                day         = fec_init.day,
                finish_time = datetime.now(),
                zona        = "provincia" if codigo_provincia_id else "estacion",
                error       = e.message if hasattr(e, 'message') else str(e),
                codigo      = codigo_estacion_id if codigo_estacion_id else codigo_provincia_id,
            )

    @staticmethod
    def ingest_info(estaciones: bool = True):
        from ..models import Estacion, CCAA, Provincia
        data = SiARService.get_siar_informacion(estaciones=estaciones)
        todas_comunidades = []

        for d in data:
            if estaciones:
                codigo_raw = d.get('codigo', '')
                if codigo_raw[:2] != "CC":
                    continue

                provincia = Provincia.query.filter_by(codigo=codigo_raw[:2]).one_or_none()
                estacion = Estacion(
                    codigo       = d.get('codigo'),
                    nombre       = d.get('nombre_estacion'),
                    longitud     = d.get('longitud'),
                    latitud      = d.get('latitud'),
                    altitud      = d.get('altitud'),
                    provincia_id = provincia.id
                )
                existe = db.session.query(Estacion.id).filter_by(codigo=estacion.codigo).first()
                if not existe:
                    db.session.add(estacion)
            else:
                if d.get('nombre-comunidades'):
                    todas_comunidades = d['nombre-comunidades']
                    continue

                codigo_ccaa_raw = d.get('codigo_ccaa')
                if not codigo_ccaa_raw:
                    continue

                nombre_ccaa = next(
                    (n.strip() for n in todas_comunidades if n.upper().startswith(codigo_ccaa_raw)),
                    None
                )
                if not nombre_ccaa:
                    continue

                if not CCAA.query.filter_by(codigo=codigo_ccaa_raw).first():
                    db.session.add(CCAA(codigo=codigo_ccaa_raw, nombre=nombre_ccaa))

                ccaa = CCAA.query.filter_by(codigo=codigo_ccaa_raw).first()
                provincia = Provincia(
                    codigo   = d.get('codigo'),
                    nombre   = d.get('nombre'),
                    ccaa_id  = ccaa.id
                )
                existe = db.session.query(Provincia.id).filter_by(
                    codigo=provincia.codigo, nombre=provincia.nombre, ccaa_id=ccaa.id
                ).first()
                if not existe:
                    db.session.add(provincia)

        db.session.commit()