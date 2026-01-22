from typing import Optional
from ..globals.actuales_futuros_dto import ActualesFuturosDTO, CccaaActualFuturoDTO, ProvinciaActualFuturoDTO, NacionActualFuturoDTO, TipoPrediccion, TipoZona
from .actuales_dao import ActualesDAO

class ActualService:

    @staticmethod
    def _build_actuales(
        data,
        cca_id : Optional[int],
        province_id : Optional[int]
    ) : 
        """
        Construye DTOs actuales en base a los datos proporcionados
        """
        # Como datos solo va a tener un objeto json, no es necesario implementar estructuras de datos complejas ni bucles for
        return ActualesFuturosDTO(
            tipo_prediccion = data.get("tipo_prediccion"),
            tipo_zona = data.get("tipo_zona"),
            codigo_zona = data.get("codigo_zona"),
            fecha_prediccion = data.get("fecha_prediccion"),
            fecha_elaboracion = data.get("fecha_elaboracion"),
            estado_cielo = data.get("estado_cielo"),
            tendencia_temp_general = data.get("tendencia_temp_general"),
            tendencia_temp_max = data.get("tendencia_temp_max"),
            tendencia_temp_min = data.get("tendencia_temp_min"),
            rachas_viento = data.get("rachas_viento"),
            precipitaciones = data.get("precipitaciones"),
            cotas_nieve = data.get("cotas_nieve"),
            existencia_heladas = data.get("existencias_heladas"),
            zona_heladas = data.get("zona_helada"),
            aparicion_nieblas = data.get("aparicion_nieblas"),
            provincia = data.get("provincia") if province_id else None,
            ccaa = data.get("ccaa") if cca_id else None
        )


    @staticmethod
    def get_actual(
        ccaa_id : Optional[int],
        province_id : Optional[int],
        tipo_zona : TipoZona,
        tipo_predicccion : TipoPrediccion
    ) : 
        # Caso base de comprobación de parámetros
        if (ccaa_id and province_id):
            raise ValueError("Debe indicarse solo la comunidad autonoma o la provincia, no las dos a la vez")
        
        if ccaa_id:
            data = ActualesDAO._get_predicciones(
                tipo_prediccion = "actual",
                tipo_zona = "ccaa",
                zona_id = ccaa_id 
            )
            items = ActualService._build_actuales(
                data = data,
                cca_id = ccaa_id,
                province_id = province_id
            )

            return CccaaActualFuturoDTO(
                type_prediction = tipo_predicccion,
                type_zone = tipo_zona,
                datos = items
            )

        elif province_id:
            data = ActualesDAO._get_predicciones(
                tipo_prediccion = "actual",
                tipo_zona = "provincial",
                zona_id = province_id
            )
            items = ActualService._build_actuales(
                data = data,
                ccaa_id = ccaa_id,
                province_id = province_id
            )

            return ProvinciaActualFuturoDTO(
                type_prediction = tipo_predicccion,
                type_zone = tipo_zona,
                datos = items
            )
        
        else:
            data = ActualesDAO._get_predicciones(
                tipo_prediccion = "actual",
                tipo_zona = "nacional"
            )
            items = ActualService._build_actuales(
                data = data,
                cca_id = ccaa_id,
                province_id = province_id
            )

            return NacionActualFuturoDTO(
                type_prediction = tipo_predicccion,
                type_zone = tipo_zona,
                datos = items
            )