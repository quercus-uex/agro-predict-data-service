from app.extensions import db
from typing import Optional
from ..models import Plaga, CalendarioPlaga
from ..external_services.itacyl_service import ItacylService
import logging

logger = logging.getLogger(__name__)


class ItacylIngestionService:

    @staticmethod
    def ingest_itacyl_data(cultivo: Optional[int], grupo: Optional[str]) -> None:
        try:
            data = ItacylService.get_itacyl_datos(cultivo=cultivo, grupo=grupo)

            existing_plagas_ids = {p.public_id for p in db.session.query(Plaga.public_id).all()}
            existing_calendar_keys = {
                (c.plaga_id, c.grupo, c.semana)
                for c in db.session.query(
                    CalendarioPlaga.plaga_id,
                    CalendarioPlaga.grupo,
                    CalendarioPlaga.semana
                ).all()
            }

            for d in data:
                public_id = d.get('id')

                if public_id not in existing_plagas_ids:
                    plaga = Plaga(
                        public_id            = public_id,
                        nombre               = d.get('nombre'),
                        agente_causante      = d.get('agente_causante'),
                        momento_critico      = d.get('momento_critico'),
                        observaciones        = d.get('observaciones'),
                        mas_info             = d.get('enlace'),
                        tipo                 = d.get('tipo'),
                        grupo                = grupo or None,
                        condiciones_evaluables = [],
                        algoritmo            = "por_defecto"
                    )
                    db.session.add(plaga)
                    db.session.flush()
                    existing_plagas_ids.add(public_id)
                else:
                    plaga = db.session.query(Plaga).filter_by(public_id=public_id).first()

                for calendario_item in d.get('calendario_de_productos', []):
                    for c in calendario_item.get('calendar', []):
                        key = (plaga.id, grupo, c.get('week'))
                        if key not in existing_calendar_keys:
                            db.session.add(CalendarioPlaga(
                                plaga_id    = plaga.id,
                                grupo       = grupo,
                                semana      = c.get('week'),
                                nivel_alerta = c.get('alertLevel')
                            ))
                            existing_calendar_keys.add(key)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error insertando datos de plagas: {e}")