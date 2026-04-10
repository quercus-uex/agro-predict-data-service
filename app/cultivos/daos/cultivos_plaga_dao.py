from sqlalchemy import select, and_, update
from app.extensions import db
from typing import Optional
from ...globals.row2dict_converter import row2dict_converter
from sqlalchemy.inspection import inspect
from ...models import Cultivo, CalendarioPlaga, CultivoPlaga, Plaga
import logging

logger = logging.getLogger(__name__)

class CultivoPlagaDAO:
    @staticmethod
    def obtener_info_cultivo_plaga(
        nombres_cultivo : list[str]
    ):
        try:
            resultados = []

            for nombre_cultivo in nombres_cultivo:
                cultivo = db.session.query(Cultivo).filter(
                    Cultivo.nombre == nombre_cultivo
                ).first()

                if not cultivo:
                    print(f"Cultivo {nombre_cultivo} no encontrado")
                    return None
                
                tiene_calendario = db.session.execute(
                    select(CalendarioPlaga.id)
                    .where(CalendarioPlaga.grupo == cultivo.grupo)
                    .limit(1)
                ).scalar()

                if tiene_calendario:
                    query = (
                        select(
                            Cultivo,
                            Plaga,
                            CalendarioPlaga
                        )
                        .select_from(Cultivo)
                        .join(CultivoPlaga, CultivoPlaga.cultivo_id == cultivo.id)
                        .join(Plaga, CultivoPlaga.plaga_id == Plaga.id)
                        .join(CalendarioPlaga, CalendarioPlaga.plaga_id == Plaga.id)
                    )
                else:
                    logger.info(f"El cultivo {nombre_cultivo} no tiene asociado un calendario")
                    query = (
                        select(
                            Cultivo, 
                            Plaga
                        )
                        .select_from(Cultivo)
                        .join(CultivoPlaga, CultivoPlaga.cultivo_id == cultivo.id)
                        .join(Plaga, CultivoPlaga.plaga_id == Plaga.id)
                    )

                resultado = db.session.execute(query).mappings().all()

                if not resultado:
                    return None
                
                cultivo_info = None
                plagas = {}

                for r in resultado:
                    if cultivo_info is None:
                        cultivo_info = cultivo
                    
                    plaga = r['Plaga']

                    # Si la plaga no se encuentra en el diccionario, se inicializa
                    if plaga.id not in plagas:
                        plagas[plaga.id] = {
                            'plaga' : plaga,
                            'calendario' : []
                        }
                    if tiene_calendario:
                        plagas[plaga.id]['calendario'].append(r['CalendarioPlaga'])


                resultados.append(
                    {
                        'cultivo' : cultivo_info,
                        'plagas' : list(plagas.values()) # Convertir el diccionario a lista
                    }
                )
            
            return resultados
        
        except Exception as e:
            raise

    @staticmethod
    def crear_relacion_cultivo_plaga(
        nombre_cultivo: str,
        recursos: dict
    ):
        try:

            cultivo = db.session.query(Cultivo).filter_by(
                nombre = nombre_cultivo
            ).first()

            if not cultivo:
                print(f"Cultivo {nombre_cultivo} no encontrado")
                return None
            
            tiene_calendario = db.session.execute(
                select(CalendarioPlaga.id)
                .where(CalendarioPlaga.grupo == cultivo.grupo)
                .limit(1)
            ).scalar()

            if tiene_calendario:
                # Obtiene plagas desde el calendario de cultivo
                query = (
                    select(Plaga.id.label('plaga_id'))
                    .join(CalendarioPlaga, CalendarioPlaga.plaga_id == Plaga.id)
                    .where(CalendarioPlaga.grupo == cultivo.grupo)
                    .distinct()
                )
            else:
                query = (
                    select(Plaga.id.label('plaga_id'))
                    .where(Plaga.grupo == cultivo.grupo)
                )

            plagas = db.session.execute(query).mappings().all()

            if not plagas:
                print(f"No existen plagas relacionadas con el grupo de cultivo : {cultivo.grupo}")
                return
            
            for r in plagas:
                existe = db.session.execute(
                    select(CultivoPlaga)
                    .where(
                        and_(
                            CultivoPlaga.cultivo_id == cultivo.id,
                            CultivoPlaga.plaga_id == r['plaga_id']
                        )
                    )
                ).scalar()

                if not existe:
                    cultivo_plaga = CultivoPlaga(
                        cultivo_id = cultivo.id,
                        plaga_id = r['plaga_id']
                    )
                    db.session.add(cultivo_plaga)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise