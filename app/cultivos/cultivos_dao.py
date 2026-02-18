from ..models import EtapaFenologica, Cultivo, ModelosHoraFrio, Variedades, UmbralesTemperatura
from sqlalchemy import select, and_, update
from app.extensions import db
from typing import Optional
from ..globals.row2dict_converter import row2dict_converter
from sqlalchemy.inspection import inspect


class CultivosDAO:

    @staticmethod
    def crear_estados_fenologicos(
        nombre : str,
        codigo : str,
        orden : int
    ):
        """
        Registra un nuevo estado fenologico en la base de datos
        """
        try:

            etapa = EtapaFenologica(
                nombre = nombre,
                codigo = codigo,
                orden = orden
            )

            # Si ya existiera el nombre a insertar y el orden a insertar, salta excepción y no se inserta nuevamente
            db.session.add(etapa)
            db.session.commit()

            return etapa

        except Exception as e:
            db.session.rollback(e)
            print(f"Error insertando un nuevo estado fenologico : {e}")
            return []

    @staticmethod
    def crear_cultivo(
        nombre : str,
        nombre_cientifico : str,
        descripcion : str
    ):
        """
        Registra un nuevo cultivo en la base de datos
        """
        try:

            cultivo = Cultivo(
                nombre = nombre,
                nombre_cientifico = nombre_cientifico,
                descripcion = descripcion
            )

            # Si existiera ya un cultivo con este nombre y nombre_cientifico, salta la constraint y no se inserta
            db.session.add(cultivo)
            db.session.commit()

            return cultivo

        except Exception as e:
            db.session.rollback()
            print(f"Error insertando un nuevo cultivo : {e}")
            return []

    @staticmethod
    def crear_modelos_horas_frio(
        nombre : str,
        codigo : str,
        descripcion : str
    ):
        try:
            modelo = ModelosHoraFrio(
                nombre = nombre, 
                codigo = codigo,
                descripcion = descripcion
            )
            # Nombre del modelo debe de ser único, si no salta excepción y no se inserta
            db.session.add(modelo)
            db.session.commit()

            return modelo

        except Exception as e:
            db.session.rollback()
            print(f"Error insertando un nuevo modelo: {e}")
            return []

    @staticmethod
    def crear_variedad(
        nombre_variedad : str,
        nombre_cultivo_asociado : str,
        horas_frio_min : int,
        horas_frio_max : int,
        nombre_modelo_horas_frio : str
    ):
        try:
            # Cultivo asociado a la variedad
            query_cultivo = (
                select(
                    Cultivo.id
                )
                .where(
                    Cultivo.nombre == nombre_cultivo_asociado
                )
            )

            cultivo_id = db.session.execute(query_cultivo).scalar_one_or_none()

            if not cultivo_id:
                raise ValueError("El cultivo no existe")

            # Modelo asociado a la variedad
            query_modelo = (
                select(
                    ModelosHoraFrio.id
                )
                .where(
                    ModelosHoraFrio.codigo == nombre_modelo_horas_frio
                )
            )

            modelo_id = db.session.execute(query_modelo).scalar_one_or_none()

            if not modelo_id:
                raise ValueError("El modelo no existe")

            # Creación de la variedad
            variedad = Variedades(
                cultivo_id = cultivo_id,
                modelo_id = modelo_id,
                nombre = nombre_variedad, 
                horas_frio_min = horas_frio_min,
                horas_frio_max = horas_frio_max
            )

            db.session.add(variedad)
            db.session.commit()

            return variedad

        except Exception as e:
            db.session.rollback()
            print(f"Error insertando una variedad nueva : {e}")
            return []

    @staticmethod
    def crear_umbrales_temperatura(
        nombre_variedad : str,
        nombre_etapa_fenologica : str,
        umbrales_criticidad : dict
    ):
        try:
            # Variedad asociada al umbral
            query_variedad = (
                select(
                    Variedades.id
                )
                .where(
                    Variedades.nombre == nombre_variedad
                )
            )

            variedad_id = db.session.execute(query_variedad).scalar_one_or_none()

            if not variedad_id:
                raise ValueError("La variedad no existe")

            # Etapa fenologica asociada al umbral
            query_etapa = (
                select(
                    EtapaFenologica.id
                )
                .where(
                    EtapaFenologica.codigo == nombre_etapa_fenologica
                )
            )

            etapa_id = db.session.execute(query_etapa).scalar_one_or_none()

            if not etapa_id:
                raise ValueError("La etapa fenologica no existe")

            # Crear un nuevo umbral de temperaturas
            umbral = UmbralesTemperatura(
                variedad_id = variedad_id,
                etapa_id = etapa_id,
                critico = umbrales_criticidad['critico'],
                alto = umbrales_criticidad['alto'],
                moderado = umbrales_criticidad['moderado'],
                bajo = umbrales_criticidad['bajo']
            )

            db.session.add(umbral)
            db.session.commit()

            return umbral

        except Exception as e:
            db.session.rollback()
            print(f"Error inserando un nuevo umbral de temperaturas : {e}")
            return []

    @staticmethod
    def umbrales_por_variedad(
        nombre_variedad : str
    ):
        try:
            query = (
                select(
                    UmbralesTemperatura,
                    EtapaFenologica
                )
                .join(Variedades)
                .join(EtapaFenologica)
                .where(
                    and_(
                        UmbralesTemperatura.variedad_id == Variedades.id,
                        Variedades.nombre == nombre_variedad,
                        UmbralesTemperatura.etapa_id == EtapaFenologica.id
                    )
                )
            )

            # Obtengo todos los umbrales de sus etapas fenologicas
            resultado = db.session.execute(query).all()

            if not resultado:
                return None
            
            return [
                {
                    'nombre_variedad': nombre_variedad,
                    'etapa_fenologica': {
                        'nombre': etapa.nombre,
                        'codigo': etapa.codigo,
                        'orden': etapa.orden
                    },
                    'critico': umbral.critico,
                    'alto': umbral.alto,
                    'moderado': umbral.moderado,
                    'bajo': umbral.bajo
                }
                for umbral, etapa in resultado
            ]
        
        except Exception as e:
            print(f"Error consultado el umbral de temperatura sobre la variedad {nombre_variedad} : {e}")
            return None

    @staticmethod
    def actualizar_rango_horas_frio(
        nombre_variedad : str,
        horas_min_frio : int,
        horas_max_frio : int
    ):
        try: 
            query = (
                update(
                    Variedades
                )
                .where(
                    Variedades.nombre == nombre_variedad
                )
                .values(
                    horas_frio_max = horas_max_frio,
                    horas_frio_min = horas_min_frio
                )
            )

            resultado_actualizado = db.session.execute(query)

            if resultado_actualizado.rowcount == 0:
                print(f"No se ha actualizado las horas_frio en la variedad : {nombre_variedad}")
                return 
            
            db.session.commit()
        
        except Exception as e:
            db.session.rollback()
            print(f"Error actualizando las horas_frio de la variedad {nombre_variedad} : {e}")
            return []
    
    @staticmethod
    def obtener_variedades_por_modelo(
        nombre_modelo : str
    ):
        try:
            query = (
                select(
                    Variedades.nombre.label('variedad_nombre'),
                    Variedades.horas_frio_max,
                    Variedades.horas_frio_min,
                    ModelosHoraFrio.nombre.label('modelo_nombre'),
                    ModelosHoraFrio.descripcion
                )
                .join(ModelosHoraFrio)
                .where(
                    and_(
                        Variedades.modelo_id == ModelosHoraFrio.id,
                        ModelosHoraFrio.codigo == nombre_modelo
                    )
                )
            )

            variedades = db.session.execute(query).all()

            if not variedades:
                return None
            
            return row2dict_converter(variedades)
        
        except Exception as e:
            print(f"Error consultando variedades que utilizan el modelo {nombre_modelo} : {e}")
            return None
    
    @staticmethod
    def obtener_modelos_frio():
        try:
            query = (
                select(ModelosHoraFrio)
            )

            resultado = db.session.execute(query).scalars().all()

            if not resultado:
                raise ValueError("Error, no se han obtenido modelos de frio de la base de datos")
            
            modelos = [
                {
                    c.key: getattr(m, c.key)
                    for c in inspect(m).mapper.column_attrs
                }
                for m in resultado
            ]

            return modelos
        
        except Exception as e:
            print(f"Error consultado los modelos de frio disponibles : {e}")
            return None
        
    @staticmethod
    def obtener_horas_frio_variedad(
        nombre_variedad : str
    ):
        try:
            query = (
                select(
                    Variedades.horas_frio_min,
                    Variedades.horas_frio_max
                )
                .where(
                    Variedades.nombre == nombre_variedad
                )
            )

            resultado = db.session.execute(query).one_or_none()

            if not resultado: 
                return None
            
            return row2dict_converter(resultado)
        
        except Exception as e:
            print(f"Error consultando horas frio de la variedad {nombre_variedad} : {e}")
            return None
            
    @staticmethod
    def obtener_cultivos():
        try:
            query = (
                select(
                    Cultivo
                )
            )

            resultado = db.session.execute(query).scalars().all()

            if not resultado:
                return None
            
            cultivos = [
                {
                    c.key: getattr(cu, c.key)
                    for c in inspect(cu).mapper.column_attrs
                }
                for cu in resultado
            ]

            return cultivos
        
        except Exception as e:
            print(f"Error obteniendo todos los cultivos disponibles : {e}")
            return None
        
    @staticmethod
    def obtener_variedades(
        cultivo : Optional[str]
    ): 
        try:
            if cultivo:
                query = (
                    select(
                        Variedades.nombre.label('variedad_nombre'),
                        Variedades.horas_frio_max,
                        Variedades.horas_frio_min,
                        ModelosHoraFrio.nombre.label('modelo_nombre'),
                        ModelosHoraFrio.descripcion
                    )
                    .join(Cultivo)
                    .join(ModelosHoraFrio)
                    .where(
                        and_(
                            Variedades.cultivo_id == Cultivo.id,
                            Cultivo.nombre == cultivo,
                            Variedades.modelo_id == ModelosHoraFrio.id
                        )
                    )
                )
            else:
                query = (
                    select(
                        Variedades.nombre.label('variedad_nombre'),
                        Variedades.horas_frio_max,
                        Variedades.horas_frio_min,
                        ModelosHoraFrio.nombre.label('modelo_nombre'),
                        ModelosHoraFrio.descripcion
                    )
                    .join(
                        ModelosHoraFrio #SQLAlchemy ya se encarga de asociar las claves foraneas con las primarias
                    )
                )
            
            resultado = db.session.execute(query).all()
            print(resultado)
            if not resultado:
                return None
            return row2dict_converter(resultado)
        
        except Exception as e:
            print(f"Error obteniendo variedades disponibles: {e}")
            return None
        
    @staticmethod
    def obtener_etapas_fenologicas():
        try:
            query = (
                select(
                    EtapaFenologica
                )
            )

            resultado = db.session.execute(query).scalars().all()

            if not resultado:
                return None
            
            etapas = [
                {
                    c.key: getattr(e, c.key)
                    for c in inspect(e).mapper.column_attrs
                }
                for e in resultado
            ]

        except Exception as e:
            print(f"Error obteniendo las etapas fenologicas disponibles : {e}")
            return None