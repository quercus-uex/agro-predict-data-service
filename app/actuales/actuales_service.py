from typing import Optional
from actuales_dao import ActualesDAO
from globals.actuales_futuros_dto import ActualesFuturosDTO, CccaaActualFuturoDTO, ProvinciaActualFuturoDTO, NacionActualFuturoDTO, TipoPrediccion, TipoZona

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
        valores = data.get("valores_actuales")

        return ActualesFuturosDTO(
            tipoPrediccion = valores.get("tipo_prediccion"),
            tipoZona = valores.get("tipo_zona"),
            codigoZona = valores.get("codigo_zona"),
            fechaPrediccion = valores.get("fecha_prediccion"),
            fechaElaboracion = valores.get("fecha_elaboracion"),
            estadoCielo = valores.get("estado_cielo"),
            tendenciaTempGeneral = valores.get("tendencia_temp_general"),
            tendenciaTempMax = valores.get("tendencia_temp_max"),
            tendenciaTempMin = valores.get("tendencia_temp_min"),
            rachasViento = valores.get("rachas_viento"),
            precipitaciones = valores.get("precipitaciones"),
            cotasNieve = valores.get("cotas_nieve"),
            existenciaHeladas = valores.get("existencias_heladas"),
            zonaHeladas = valores.get("zona_helada"),
            aparicionNieblas = valores.get("aparicion_nieblas"),
            provincia = valores.get("provincia") if province_id else None,
            ccaa = valores.get("ccaa") if cca_id else None
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
            data = ActualesDAO.define_computing_current_ccaa(ccaa_id = ccaa_id)
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
            data = ActualesDAO.define_computing_current_provincia(provincia_id = province_id)
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
            data = ActualesDAO.define_computing_current_nacional()
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