from . import forecast_bp
from ..decorator.log_decorator import log
from helpers.ApiExceptions import APIException
from .forecast_service import ForecastService
from flask import jsonify, request, current_app
from ..globals.dto2dict import dataclass_to_json
from ..globals.convertidor_tipo import convertir_tipo
from .forecast_dto import TipoPrediccion, TipoZona
import logging
from typing import Optional

logger = logging.getLogger(__name__)


@forecast_bp.route('/climate/pronostico/localidades', methods = ['GET'])
@log('../logs/fichero_salida.json')
def localidades():
    try:
        datos = ForecastService.get_localidades()

        if not datos:
            raise APIException(
                message = "No se han obtenido datos de localidades",
                status = 404,
                error = 'Data Not Found'
            )
        
        return dataclass_to_json(datos)
    
    except APIException as e:
        logger.info(f"API Exception: {e}")
        return jsonify(
            {
                'success' : 'false',
                'code' : '502',
                'message' : 'Provider Exception',
                'error' : str(e)
            }
        ), 502

@forecast_bp.route('/climate/pronostico/<string:zona>/<string:prediccion>', methods = ['GET'])
@log('../logs/fichero_salida.json')
def pronostico(
    zona : str,
    prediccion : str
) : 
    try:
        if not (zona and prediccion):
            raise APIException(
                message = "El valor de los parámetros de entrada no son los apropiados",
                status = 400,
                error = 'Invalid Parameters' 
            )
        
        ccaa : Optional[str] = request.args.get('ccaaId')
        provincia : Optional[str] = request.args.get('provinciaId')

        # Conversor de str a int -- zona_id
        """if ccaa:
            ccaa = convertir_tipo(ccaa, int)
        elif provincia:
            provincia = convertir_tipo(provincia, int)"""

        # Convertidores de enum
        type_zona = convertir_tipo(zona, TipoZona)
        type_prediccion = convertir_tipo(prediccion, TipoPrediccion)

        datos = ForecastService.get_forecast(
            current_app._get_current_object(),
            ccaa_id = ccaa,
            provincia_id = provincia,
            tipo_prediccion = type_prediccion,
            tipo_zona = type_zona
        )

        logger.info(f"Datos recibidos por el servicio Forecast: {datos}")

        if not datos:
            raise APIException(
                message = f"Los datos con pronostico {type_prediccion} - {type_zona} no se han recuperado",
                status = 404,
                error = 'Data Not Found'
            )
        
        return dataclass_to_json(datos)
    
    except APIException as e:
        logger.info(f"API Exception: {e}")
        return jsonify(
            {
                'success' : 'false',
                'code' : '502',
                'message' : 'Provider Exception',
                'error' : str(e)
            }
        ), 502