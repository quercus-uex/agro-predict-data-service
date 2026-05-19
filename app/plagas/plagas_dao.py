from ..models import Plaga, CalendarioPlaga, PlagaTipoDato, TipoDato
from sqlalchemy import select, and_
from app.extensions import db
from sqlalchemy.inspection import inspect
from typing import Optional

class PlagasDAO:

    @staticmethod
    def _get_recursos_disponibles():
        try:
            return db.session.query(TipoDato.nombre).all()
        except Exception as e:
            raise

    @staticmethod
    def _get_plagas(
        grupo : str,
        tipo : str,
        plaga_id : Optional[int]
    ):
        try:

            condiciones = [
                Plaga.grupo == grupo,
                Plaga.tipo == tipo
            ]

            if plaga_id:
                condiciones.append(Plaga.id == plaga_id)                        
            
            query = (
                select(Plaga, CalendarioPlaga)
                .outerjoin(CalendarioPlaga, Plaga.id == CalendarioPlaga.plaga_id)
                .where(and_(*condiciones))
                .order_by(Plaga.public_id.desc())
            )

            resultados = db.session.execute(query).all()
            resultados_dict = []

            for plaga, calendario in resultados:
                plaga_dict = {
                    c.key: getattr(plaga, c.key)
                    for c in inspect(plaga).mapper.column_attrs
                }
                
                if calendario is not None:
                    plaga_dict["calendario"] = {
                        c.key: getattr(calendario, c.key)
                        for c in inspect(calendario).mapper.column_attrs
                    }
                else:
                    plaga_dict["calendario"] = None
                
                resultados_dict.append(plaga_dict)

            return resultados_dict
        
        except Exception as e:
            raise
        
    @staticmethod
    def _get_grupos_calendario():
        try:
            query = (
                select(
                    CalendarioPlaga.grupo
                ).distinct()
            )

            resultado = db.session.execute(query).scalars().all()

            return set(resultado)
        
        except Exception as e:
            raise


    @staticmethod
    def crear_plagas(
        public_id: str,
        nombre: str,
        agente_causante: str,
        momento_critico: str,
        observaciones: Optional[str],
        mas_info: Optional[str],
        tipo: str,
        grupo: str,
        recursos: list,
        algoritmo : str,
        algoritmo_url : str,
        condiciones_evaluables: list,
        ventana_temporal: list
    ):
        try:
            # Compruebo si ya existe la plaga a insertae
            existe = db.session.query(Plaga).filter_by(public_id = public_id).first()
            if existe:
                return None

            plaga = Plaga(
                public_id=public_id,
                nombre=nombre,
                agente_causante=agente_causante,
                momento_critico=momento_critico,
                observaciones=observaciones,
                mas_info=mas_info,
                tipo=tipo,
                grupo=grupo,
                condiciones_evaluables=condiciones_evaluables,
                ventana_temporal = ventana_temporal,
                algoritmo = algoritmo,
                algoritmo_url = algoritmo_url
            )

            db.session.add(plaga)
            db.session.flush()

            tipos_validos = {
                t.nombre: t.id for t in db.session.query(TipoDato).all()
            }

            for recurso_nombre in recursos:
                if recurso_nombre not in tipos_validos:
                    raise ValueError(f"Tipo de dato no válido: {recurso_nombre}")

                recurso = PlagaTipoDato(
                    plaga_id=plaga.id,
                    tipo_dato_id=tipos_validos[recurso_nombre]
                )
                db.session.add(recurso)

            db.session.commit()
            return plaga

        except Exception:
            db.session.rollback()
            raise 
