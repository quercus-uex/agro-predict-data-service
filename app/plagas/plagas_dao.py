from ..models import Plaga, CalendarioPlaga
from sqlalchemy import select, and_
from app.extensions import db
from ..globals.row2dict_converter import row2dict_converter
from sqlalchemy.inspection import inspect
from typing import Optional

class PlagasDAO:

    @staticmethod
    def _get_plagas(
        tipo : str,
        plaga_id : Optional[int]
    ):
        try:

            condiciones = [
                Plaga.id == CalendarioPlaga.plaga_id,
                Plaga.tipo == tipo
            ]

            if plaga_id:
                condiciones.append(Plaga.id == plaga_id)

            # Query que obtiene todas las plagas de la bd
            query_plagas = (
                select(
                    Plaga # Obtengo filas de objetos ORM
                )
                .join(CalendarioPlaga)
                .where(
                    and_(*condiciones)
                )
                .order_by(
                    Plaga.public_id.desc()
                )
            )

            resultados = (
                db.session.execute(query_plagas)
                .scalars()
                .unique()
                .all()
            )
            # Como tengo filas de objetos ORM, no puedo usar row2dict_converter
            plagas = [
                {
                    c.key: getattr(p, c.key)  # Creamos el diccionario obteniendo los valores de las columnas del objeto ORM
                    for c in inspect(p).mapper.column_attrs # Recorre las columnas del objeto ORM
                }
                for p in resultados
            ]
            
            return plagas
        
        except Exception as e:
            print(f"Error leyendo datos de la bd sobre plagas: {e}")
            return None
        
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
            print(f"Error obteniendo los grupos de los calendarios de plaga : {e}")
            return None


    @staticmethod
    def _get_calendario_plagas(
        plaga_id : Optional[int]
    ):
        try:
            
            condicion = [
                CalendarioPlaga.plaga_id == Plaga.id
            ]

            if plaga_id:
                condicion.append(CalendarioPlaga.plaga_id == plaga_id)
            
            # Query que obtiene el calendario de la plaga asociada
            query_calendario_plagas = (
                select(
                    CalendarioPlaga
                )
                .join(Plaga)
                .where(
                    *condicion
                )
                .order_by(
                    CalendarioPlaga.plaga_id.desc()
                )
            )

            resultados = (
                db.session.execute(query_calendario_plagas)
                .scalars()
                .unique()
                .all()
            )

            calendarios = [
                {
                    c.key: getattr(p, c.key)  # Creamos el diccionario obteniendo los valores de las columnas del objeto ORM
                    for c in inspect(p).mapper.column_attrs # Recorre las columnas del objeto ORM
                }
                for p in resultados
            ]
            
            return calendarios
            
        except Exception as e:
            print(f"Error leyendo datos del calendario de plagas: {e}")
            return None

    @staticmethod
    def crear_plagas(
        public_id : str,
        nombre : str,
        agente_causante : str,
        momento_critico : str,
        observaciones : Optional[str],
        mas_info : Optional[str],
        tipo : str,
        grupo : str
    ):
        try:
            plaga_existente = (
                select(
                    Plaga
                )
                .where(
                    and_(
                        Plaga.public_id == public_id,
                        Plaga.nombre == nombre,
                        Plaga.agente_causante == agente_causante,
                        Plaga.momento_critico == momento_critico,
                        Plaga.observaciones == observaciones,
                        Plaga.mas_info == mas_info,
                        Plaga.tipo == tipo,
                        Plaga.grupo == grupo,
                    )
                )
            )

            resultado = db.session.execute(plaga_existente).one_or_none

            if resultado:
                return

            # Creación de la plaga a insertar
            plaga = Plaga(
                public_id = public_id,
                nombre = nombre,
                agente_causante = agente_causante,
                momento_critico = momento_critico,
                observaciones = observaciones if observaciones else None,
                mas_info = mas_info if mas_info else None,
                tipo = tipo,
                grupo = grupo,
            )
            if not plaga:
                return
            
            db.session.add(plaga)
            db.session.commit()

            return plaga
        
        except Exception as e:
            db.session.rollback()
            print(f"Se ha producido un error insertando una nueva plaga : {e}")
            return 
