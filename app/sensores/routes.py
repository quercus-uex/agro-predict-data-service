from .sensores_service import SensoresService
from ..ingesta.ingesta_service import IngestionService
from . import sensores_bp
from flask import request, jsonify
from ..decorator.log_decorator import log
from ..globals.convertidor_tipo import convertir_tipo
from app.globals.dto2dict import dataclass_to_json
from helpers.ApiExceptions import APIException
from datetime import date
import logging

logger = logging.getLogger(__name__)

@sensores_bp.route('/sensores', methods = ['GET'])
@log('../logs/fichero_salida.json')
def sensores():

    try:
        eui = request.args.get('eui', '')
        fecha_inicio = request.args.get('fecha_inicio', '')
        fecha_fin = request.args.get('fecha_fin', '')

        if not all([eui, fecha_inicio, fecha_fin]):
            raise APIException(
                message = "Debe indicarse todos los parámetros de la query (eui, fecha_inicio, fecha_fin)",
                status = 400,
                error = 'Invalid parameters'
            )

        # Conversor de string a date
        fecha_inicio = convertir_tipo(fecha_inicio, date)
        fecha_fin = convertir_tipo(fecha_fin, date)

        
        IngestionService.ingesta_sensores_data(
            eui = eui,
            fecha_inicio = fecha_inicio,
            fecha_fin = fecha_fin
        )
        
        
        datos = SensoresService.get_sensor_data(
            eui = eui,
            fecha_inicio = fecha_inicio,
            fecha_fin = fecha_fin
        )

        if not datos:
            raise APIException(
                message = "No se han encontrado datos de sensores para los parámetros indicados",
                status = 404,
                error = 'Data Not Found'
            )
        
        return dataclass_to_json(datos), 200
    
    except APIException as e:
        logger.error(f"API Exception: {e}")
        return jsonify(
            {
                'success': 'false',
                'code': '502',
                'message': 'Provider Exception',
                'error' : str(e)
            }
        ), 502