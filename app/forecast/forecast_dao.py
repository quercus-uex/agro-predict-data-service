from ..models import Predicciones, Provincia, CCAA, LocalidadesClimaticas
from sqlalchemy import select, and_
from app.extensions import db
from ..globals.row2dict_converter import row2dict_converter

class ForecastDAO:
    
    EXCLUIR = {"texto_original", "provincia_id", "ccaa_id"}

    @staticmethod
    def _base_columns(extra_columns = None):
        cols = [
            c for c in Predicciones.__table__.columns
            if c.name not in ForecastDAO.EXCLUIR
        ]

        if extra_columns:
            cols.extend(extra_columns)

        return cols
    
    @staticmethod
    def _get_predicciones(
        *,
        tipo_prediccion : str,
        tipo_zona : str,
        zona_id : str | None
    ):
        try:
            # Contenido de la clausula where en la consulta, generico para reutilizar código
            print(f"Zona : {zona_id}")
            filtros = [
                Predicciones.tipo_prediccion == tipo_prediccion,
                Predicciones.tipo_zona == tipo_zona
            ]

            # Por si hay que obtener además el id de la provincia o ccaa en la select
            extra_columns = []

            # Almacena la referencia a la tabla que se va a hacer el join
            join_model = None

            if tipo_zona == "ccaa":
                filtros.append(CCAA.codigo == zona_id)
                join_model = CCAA
                extra_columns.append(CCAA.codigo.label("ccaa"))

            elif tipo_zona == "provincial":
                filtros.append(Provincia.codigo == zona_id)
                join_model = Provincia
                extra_columns.append(Provincia.codigo.label("provincia"))
            
            query = (
                select(
                    *ForecastDAO._base_columns(extra_columns = extra_columns) 
                )
                .where(
                    and_(*filtros)
                )
                .order_by(Predicciones.fecha_prediccion.desc())
                .limit(1)
            )

            if join_model:
                query = query.join(join_model)

            result = db.session.execute(query).fetchone()

            if result is None:
                return None
            
            valores_predictivos = row2dict_converter(result)

            return valores_predictivos
        
        except Exception as e:
            print(f"Error obteniendo predicción {tipo_zona} ({tipo_prediccion}) : {e}")
            return None

    @staticmethod
    def _get_localidades_climaticas(
        prediccion_id
    ):
        try:
            query = (
                select(
                    LocalidadesClimaticas.nombre,
                    LocalidadesClimaticas.temperatura_maxima,
                    LocalidadesClimaticas.temperatura_minima
                )
                .where(
                    LocalidadesClimaticas.prediccion_id == prediccion_id
                )
            )

            result = db.session.execute(query)
            
            if result is None:
                return

            result_final = []
            for r in result:
                r_to_dict = row2dict_converter(r)
                result_final.append(r_to_dict)

            return result_final
        
        except Exception as e:
            print(f"Algo ha ocurrido obteniendo las localidades de la prediccion {prediccion_id} - {e}")
            return None            