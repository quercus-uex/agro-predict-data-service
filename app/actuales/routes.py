# Controlador ACTUALES
from . import actuales_bp
from ..globals.log_decorator import log
from flask import request
from helpers.ApiExceptions import APIException
from .actuales_service import ActualService
from flask import jsonify
from ..globals.dto2dict import dataclass_to_json
from app.globals.convertidor_tipo import convertir_tipo
from app.globals.actuales_futuros_dto import TipoPrediccion, TipoZona
import logging

logger = logging.getLogger(__name__)

@actuales_bp.route('/climate/current/ccaa/<string:ccaa>', methods = ['GET'])
@log('../logs/fichero_salida.json')
def pronostico_actual_ccaa(
    ccaa : str
):
    try:
        if not ccaa:
            raise APIException(
                message = "El valor de los parámetros de entrada no son los apropiados",
                status = 400,
                error = 'Invalid Parameters'
            )
        
        # Conversor de str a int -- ccaa
        ccaa_id = convertir_tipo(ccaa, int)
        
        # Convertidores de Enum
        type_zona = convertir_tipo("ccaa", TipoZona)
        type_prediccion = convertir_tipo("actual", TipoPrediccion)
        
        datos = ActualService.get_actual(
            ccaa_id = ccaa_id,
            province_id = None,
            tipo_zona = type_zona,
            tipo_predicccion = type_prediccion  
        )

        logger.info(f"Datos recibidos por el servicio actuales: {datos}")

        if not datos:
            raise APIException(
                message = f'Los datos actuales de la comunidad autónoma {ccaa}, no están disponibles',
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
    
@actuales_bp.route('/climate/current/nacional', methods = ['GET'])
@log('../logs/fichero_salida.json')
def pronostico_actual_nacional():

    try:

        # No hay que comprobar parámetros

        #Convertidores de Enums
        type_zona = convertir_tipo("nacional", TipoZona)
        type_prediccion = convertir_tipo("actual", TipoPrediccion)

        datos = ActualService.get_actual(
            ccaa_id = None,
            province_id = None,
            tipo_zona = type_zona,
            tipo_predicccion = type_prediccion
        )

        logger.info(f"Datos recibidos por el servicio actuales: {datos}")

        if not datos:
            raise APIException(
                message = f'Los datos actuales nacionales, no están disponibles',
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
    
@actuales_bp.route('/climate/current/provincia/<string:provinciaCode>', methods = ['GET'])
@log('../logs/fichero_salida.json')
def pronostico_actual_provincia(
    provinciaCode : str
):
    try:
        if not provinciaCode:
            raise APIException(
                message = "El valor de los parámetros de entrada no son los apropiados",
                status = 400,
                error = 'Invalid Parameters'
            )
        
        # Conversor de str a int -- ccaa
        provincia_id = convertir_tipo(provinciaCode, int)
        
        # Convertidores de Enum
        type_zona = convertir_tipo("provincial", TipoZona)
        type_prediccion = convertir_tipo("actual", TipoPrediccion)
        
        datos = ActualService.get_actual(
            ccaa_id = provincia_id,
            province_id = None,
            tipo_zona = type_zona,
            tipo_predicccion = type_prediccion  
        )

        logger.info(f"Datos recibidos por el servicio actuales: {datos}")

        if not datos:
            raise APIException(
                message = f'Los datos actuales de la provincia {provinciaCode}, no están disponibles',
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