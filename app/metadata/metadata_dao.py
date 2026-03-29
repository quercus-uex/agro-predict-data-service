from sqlalchemy import select, and_, inspect, delete, update
from ..models import Parcelas, Sensores, Dispositivos
from ..extensions import db
from typing import Optional
from ..models import Metadatos
from datetime import datetime

class MetadataDAO:

    JOIN_POR_MODELO = {
        Parcelas : [Sensores],
        Dispositivos : [Sensores],
        Sensores : [Parcelas, Dispositivos],
    }

    METADATOS_POR_MODELO = {
        Parcelas : 'area',
        Dispositivos : 'device_plt_id',
        Sensores : 'dev_eui'
    }

    # === GENERICOS === #
    @staticmethod
    def crear_registro(
        modelo,
        datos : dict,
        campos_unicos : list[str]
    ):
        try:

            if modelo == Sensores and datos.get('dispositivo_id'):
                existe = db.session.query(Dispositivos).filter_by(
                    dev_eui = datos['dispositivo_id']
                ).first()
                if not existe:
                    return None


            condiciones = [
                getattr(modelo, campo) == datos.get(campo)
                for campo in campos_unicos
            ]

            existe_registro = db.session.query(modelo).filter(*condiciones).first()

            if existe_registro:
                return existe_registro

            entidad = modelo(**datos)
            db.session.add(entidad)
            db.session.flush()
            
            entidad_id = next(
                (getattr(entidad, campo) for campo in campos_unicos if getattr(entidad, campo, None)),
                entidad.id
            )
            
            metadatos = Metadatos(
                tipo = modelo.__name__.lower(),
                entidad_id = entidad_id,
                clave = modelo.__name__,
                valor = MetadataDAO.METADATOS_POR_MODELO.get(modelo.__name__),
                fuente = 'csv',
                fecha_creacion = datetime.today()
            )

            db.session.add(metadatos)

            db.session.commit()
            return entidad
        
        except Exception as e:
            db.session.rollback()
            print(f"Error al intentar insertar una entidad {modelo.__name__} al sistema : {e}")
            return None
        
    @staticmethod
    def consultar_registro(
        modelo,
        filtros : Optional[dict]
    ):
        try:
            query = db.session.query(modelo)
            
            for join in MetadataDAO.JOIN_POR_MODELO.get(modelo, []):
                query = query.join(join)
            
            if filtros:
                condiciones = [
                    getattr(modelo, filtro) == valor
                    for filtro,valor in filtros.items()
                ]
                query = query.filter(*condiciones)
            
            registros = query.all()

            return [
                {
                    columna.key: getattr(row, columna.key) 
                    for columna in inspect(row).mapper.column_attrs
                }
                for row in registros
            ]

        except Exception as e:
            print(f"Error al consultar datos registrados sobre la entidad {modelo.__name__} en el sistem : {e}")
            return None
        
    @staticmethod
    def eliminar_registro(
        modelo,
        filtros : Optional[list] = None
    ):
        try:

            if not filtros:
                raise ValueError("Se requieren filtros para eliminar registros")

            query = db.session.query(modelo)
            registros = query.filter(*filtros).all()

            if not registros:
                return 0  # Nada que eliminar

            for registro in registros:
                db.session.delete(registro)

            db.session.commit()
            return len(registros)
        
        except Exception as e:
            db.session.rollback()
            print(f"Error al eliminar instancias de tipo {modelo.__name__} : {e}")
            return None
        
    @staticmethod
    def actualizar_registro(
        modelo,
        valores: dict,
        filtros: Optional[list] = None
    ):
        try:
            if not valores:
                raise ValueError("Se requieren valores para actualizar")
            
            if not filtros:
                raise ValueError("Se requieren filtros para actualizar registros")

            registros = db.session.query(modelo).filter(*filtros).all()

            if not registros:
                return 0

            for registro in registros:
                for campo, valor in valores.items():
                    if hasattr(registro, campo):
                        setattr(registro, campo, valor)
                    else:
                        raise ValueError(f"El campo '{campo}' no existe en {modelo.__name__}")

            db.session.commit()
            return len(registros)

        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar instancias de {modelo.__name__}: {e}")
            return None

    # === FIN GENERICOS === #