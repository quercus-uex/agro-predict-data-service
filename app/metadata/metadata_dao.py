from sqlalchemy import select, and_, inspect
from models import Parcelas, Sensores, Dispositivo
from extensions import db
from typing import Optional
from datetime import datetime

class MetadataDAO:

    JOIN_POR_MODELO = {
        Parcelas : [Sensores],
        Dispositivo : [Sensores],
        Sensores : [Parcelas, Dispositivo],
    }

    # === GENERICOS === #
    @staticmethod
    def crear_registro(
        modelo,
        datos : dict,
        campos_unicos : list[str]
    ):
        try:
            condiciones = [
                getattr(modelo, campo) == datos.get(campo)
                for campo in campos_unicos
            ]

            existe_registro = db.session.query(modelo).filter(*condiciones).first()

            if existe_registro:
                return existe_registro

            entidad = modelo(**datos)
            db.session.add(entidad)
            db.session.commit()
            return entidad
        
        except Exception as e:
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
    # === FIN GENERICOS === #

    """
    @staticmethod
    def crear_parcelas(
        id_publico : str,
        nombre : str,
        geometria : dict
    ):
        try:
            datos = {
                'public_id' : id_publico,
                'nombre' : nombre,
                'geometria' : geometria
            }

            campos_unicos = ['public_id']

            parcela = MetadataDAO.crear_registro(
                modelo = Parcelas,
                datos = datos,
                campos_unicos = campos_unicos
            )

            if not parcela:
                print(f"Error al registrar la parcela {nombre}")
                return None
            
            return parcela
            
        except Exception as e:
            print(f"Error al registrar una nueva parcela en el sistema : {e}")
            return None

    @staticmethod
    def crear_dispositivo(
        id_publico : str,
        dev_eui : str,
        descripcion : Optional[str],
        nombre : Optional[str],
        creado : datetime,
        actualizado : Optional[datetime]
    ):
        try:
            datos = {
                'public_id' : id_publico,
                'dev_eui' : dev_eui,
                'descripcion' : descripcion if descripcion else None,
                'nombre' : nombre if nombre else None,
                'creado' : creado,
                'actualizado' : actualizado if actualizado else None
            }

            campos_unicos = ['public_id', 'dev_eui']

            dispositivo = MetadataDAO.crear_registro(
                modelo = Dispositivo,
                datos = datos,
                campos_unicos = campos_unicos
            )

            if not dispositivo:
                print(f"Error al registrar el dispisitivo {dev_eui}")
                return None
            
            return dispositivo
        
        except Exception as e:
            print(f"Error al registrar un nuevo dispositivos en el sistema : {e}")
            return None
        
    @staticmethod
    def crear_sensores(
        eui : str,
        dispositivo_id : Optional[str],
        parcela_id : str,
        geometria : Optional[dict]
    ):
        try:
            datos = {
                'eui' : eui,
                'dispositivo_id' : dispositivo_id if dispositivo_id else None,
                'parcela_id' : parcela_id,
                'geometria' : geometria if geometria else None
            }

            campos_unicos = ['eui']

            sensor = MetadataDAO.crear_registro(
                modelo = Sensores,
                datos = datos,
                campos_unicos = campos_unicos
            )

            if not sensor:
                print(f"Error al registrar el sensor {eui}")
                return None
            
            return sensor

        except Exception as e:
            print(f"Error al registrar un nuevo sensor en el sistema : {e}")
            return None
    """