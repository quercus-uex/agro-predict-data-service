from sqlalchemy import select, and_, inspect, delete, update
from ..models import Parcelas, Sensores, Dispositivos
from shapely.geometry import Point, Polygon
from shapely.validation import make_valid
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
    def vaidar_columnas(
        modelo
    ):
        try:
            columnas_validas = {c.key for c in inspect(modelo).mapper.column_attrs}
            return columnas_validas
        except Exception as e:
            print(f"Error al consultar las columnas válidas del modelo : {modelo.__name__}")
            return None

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
            print(f"Query resultante : {query}")
            
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

    # === ESPECÍFICOS === #
    @staticmethod
    def asignar_parcela_a_sensores():
        """
        Recorre los sensores cuya parcela_id están a NULL, comprobando si su 
        geocoordenada se integra dentro de las geocoordenadas que almacenan 
        las parcelas. Si encuentra la coincidencia se actualiza la parcela_id 
        del sensor.
        """
        try:
            # 1. Obtención de los sensores cuya parcela_id se encuentra a NULL
            sensores_sin_parcela = db.session.query(Sensores).filter(
                Sensores.parcela_id == None,
                Sensores.geometria != None
            ).all()

            if not sensores_sin_parcela:
                return {
                    'actualizados' : 0,
                    'mensaje' : 'No hay sensores pendientes de asignacion'
                }
            
            # 2. Obtención de las parcelas con coordenadas
            parcelas = db.session.query(Parcelas).filter(
                Parcelas.geometria != None
            )

            if not parcelas:
                return {
                    'actualizados' : 0,
                    'mensaje' : 'No hay parcelas registradas que incorporen geocoordenasas'
                }
            
            # 3. Preconfiguración de la geomentría de parcelas
            geometrias_parcelas = []
            for parcela in parcelas:
                try:
                    coordenadas = parcela.geometria
                    # Disposición de coordenadas: [[[logn, lat]]], extraer la capa exterior
                    capa_exterior = coordenadas[0]
                    poligono = make_valid(Polygon(capa_exterior))
                    geometrias_parcelas.append((parcela, poligono))
                except Exception as e:
                    print(f"Parcela {parcela.public_id} tiene coordenadas inválidad, se omite: {e}")
                    continue
            
            # 4. Para cada sensor, comprobar si dentro de un polígono de parcela
            actualizados = 0
            for sensor in sensores_sin_parcela:
                try:
                    coordenadas = sensor.geometria # [long, lat]
                    punto = Point(coordenadas[0], coordenadas[1])

                    for parcela, poligono in geometrias_parcelas:
                        if poligono.covers(punto): # covers, por si los sensores se encuentran en el borde del polígono procesado
                            sensor.parcela_id = parcela.public_id
                            actualizados += 1
                            break # Un sensor solo puede pertenecer a una partcela, no a más
                except Exception as e:
                    print(f"Error procesando el sensor {sensor.id}: {e}")
                    continue
            
            db.session.commit()
            return {"actualizados" : actualizados, "total_procesados" : len(sensores_sin_parcela)}
        
        except Exception as e:
            db.session.rollback()
            print(f"Error en asignación geoespacial de sensores : {e}")
            return None

